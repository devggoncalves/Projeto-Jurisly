from __future__ import annotations

import logging
import time
from dataclasses import dataclass, field
from typing import Any
from urllib.parse import urljoin

import httpx
from django.conf import settings

logger = logging.getLogger(__name__)


class ErroDjen(Exception):
    """Erro base da integração DJEN."""


class ErroDjenHttp(ErroDjen):
    def __init__(self, mensagem: str, *, status_code: int | None = None, corpo: Any = None):
        super().__init__(mensagem)
        self.status_code = status_code
        self.corpo = corpo


class ErroDjenRateLimit(ErroDjenHttp):
    def __init__(
        self,
        mensagem: str,
        *,
        status_code: int = 429,
        retry_after: float | None = None,
        corpo: Any = None,
    ):
        super().__init__(mensagem, status_code=status_code, corpo=corpo)
        self.retry_after = retry_after


@dataclass
class RespostaComunicacoesDjen:
    status: str
    message: str
    count: int
    items: list[dict[str, Any]]
    pagina: int
    itens_por_pagina: int
    headers_rate_limit: dict[str, str] = field(default_factory=dict)
    url: str = ""
    parametros: dict[str, Any] = field(default_factory=dict)
    bruto: dict[str, Any] = field(default_factory=dict)


class ClienteDjen:
    """
    Cliente HTTP para a API pública do DJEN/CNJ.
    Sem regras de negócio — apenas transporte, timeouts, retries e rate-limit.
    """

    def __init__(
        self,
        *,
        base_url: str | None = None,
        timeout: float | None = None,
        max_retries: int | None = None,
        itens_por_pagina: int | None = None,
        client: httpx.Client | None = None,
    ):
        self.base_url = (base_url or settings.DJEN_BASE_URL).rstrip("/") + "/"
        self.timeout = timeout if timeout is not None else settings.DJEN_TIMEOUT
        self.max_retries = (
            max_retries if max_retries is not None else settings.DJEN_MAX_RETRIES
        )
        self.itens_por_pagina_padrao = (
            itens_por_pagina
            if itens_por_pagina is not None
            else settings.DJEN_ITENS_POR_PAGINA
        )
        self._client_externo = client
        self._client_proprio: httpx.Client | None = None

    def _obter_client(self) -> httpx.Client:
        if self._client_externo is not None:
            return self._client_externo
        if self._client_proprio is None:
            self._client_proprio = httpx.Client(
                base_url=self.base_url,
                timeout=httpx.Timeout(self.timeout, connect=min(10.0, self.timeout)),
                headers={
                    "Accept": "application/json",
                    "User-Agent": "Jurisly/0.1 (+integracao-djen)",
                },
                follow_redirects=True,
            )
        return self._client_proprio

    def close(self) -> None:
        if self._client_proprio is not None:
            self._client_proprio.close()
            self._client_proprio = None

    def __enter__(self) -> ClienteDjen:
        return self

    def __exit__(self, *args) -> None:
        self.close()

    def consultar_comunicacoes(
        self,
        *,
        numero_oab: str | None = None,
        uf_oab: str | None = None,
        data_inicio: str | None = None,
        data_fim: str | None = None,
        nome_advogado: str | None = None,
        nome_parte: str | None = None,
        numero_processo: str | None = None,
        sigla_tribunal: str | None = None,
        texto: str | None = None,
        pagina: int = 1,
        itens_por_pagina: int | None = None,
        extras: dict[str, Any] | None = None,
    ) -> RespostaComunicacoesDjen:
        params: dict[str, Any] = {
            "pagina": max(1, int(pagina)),
            "itensPorPagina": itens_por_pagina or self.itens_por_pagina_padrao,
        }
        if numero_oab:
            params["numeroOab"] = str(numero_oab).strip()
        if uf_oab:
            params["ufOab"] = str(uf_oab).strip().upper()
        if data_inicio:
            params["dataDisponibilizacaoInicio"] = data_inicio
        if data_fim:
            params["dataDisponibilizacaoFim"] = data_fim
        if nome_advogado:
            params["nomeAdvogado"] = nome_advogado.strip()
        if nome_parte:
            params["nomeParte"] = nome_parte.strip()
        if numero_processo:
            params["numeroProcesso"] = numero_processo.strip()
        if sigla_tribunal:
            params["siglaTribunal"] = sigla_tribunal.strip().upper()
        if texto:
            params["texto"] = texto.strip()
        if extras:
            for chave, valor in extras.items():
                if valor is not None and valor != "":
                    params[chave] = valor

        payload, headers, url = self._get_json("/api/v1/comunicacao", params=params)
        rate = {
            k: v
            for k, v in headers.items()
            if k.lower().startswith("x-ratelimit") or k.lower() == "retry-after"
        }
        items = payload.get("items") or []
        if not isinstance(items, list):
            items = []
        return RespostaComunicacoesDjen(
            status=str(payload.get("status") or ""),
            message=str(payload.get("message") or ""),
            count=int(payload.get("count") or 0),
            items=items,
            pagina=params["pagina"],
            itens_por_pagina=params["itensPorPagina"],
            headers_rate_limit=rate,
            url=url,
            parametros=params,
            bruto=payload if isinstance(payload, dict) else {"raw": payload},
        )

    def iterar_comunicacoes(self, **kwargs) -> list[dict[str, Any]]:
        """Percorre páginas até esgotar `count` ou não haver mais items."""
        pagina = int(kwargs.pop("pagina", 1) or 1)
        acumulado: list[dict[str, Any]] = []
        total = None
        while True:
            resposta = self.consultar_comunicacoes(pagina=pagina, **kwargs)
            if total is None:
                total = resposta.count
            acumulado.extend(resposta.items)
            if not resposta.items:
                break
            if total is not None and len(acumulado) >= total:
                break
            if len(resposta.items) < resposta.itens_por_pagina:
                break
            pagina += 1
            if pagina > 500:
                logger.warning("DJEN: interrompido após 500 páginas de proteção.")
                break
        return acumulado

    def _get_json(
        self, path: str, *, params: dict[str, Any]
    ) -> tuple[Any, dict[str, str], str]:
        client = self._obter_client()
        url = urljoin(self.base_url, path.lstrip("/"))
        ultimo_erro: Exception | None = None

        for tentativa in range(self.max_retries + 1):
            try:
                resposta = client.get(path if self._usa_base(client) else url, params=params)
            except httpx.TimeoutException as exc:
                ultimo_erro = ErroDjen(f"Timeout ao consultar DJEN: {exc}")
                self._backoff(tentativa)
                continue
            except httpx.HTTPError as exc:
                ultimo_erro = ErroDjen(f"Erro de rede DJEN: {exc}")
                self._backoff(tentativa)
                continue

            headers = {k: v for k, v in resposta.headers.items()}
            if resposta.status_code == 429:
                retry_after = self._parse_retry_after(headers.get("Retry-After"))
                if tentativa < self.max_retries:
                    time.sleep(retry_after or (2 ** tentativa))
                    continue
                raise ErroDjenRateLimit(
                    "Rate limit DJEN (429).",
                    retry_after=retry_after,
                    corpo=self._safe_json(resposta),
                )

            if resposta.status_code >= 500:
                ultimo_erro = ErroDjenHttp(
                    f"DJEN respondeu {resposta.status_code}.",
                    status_code=resposta.status_code,
                    corpo=self._safe_json(resposta),
                )
                self._backoff(tentativa)
                continue

            if resposta.status_code >= 400:
                raise ErroDjenHttp(
                    f"DJEN respondeu {resposta.status_code}.",
                    status_code=resposta.status_code,
                    corpo=self._safe_json(resposta),
                )

            try:
                payload = resposta.json()
            except ValueError as exc:
                raise ErroDjen(f"Resposta DJEN não é JSON válido: {exc}") from exc

            return payload, headers, str(resposta.url)

        assert ultimo_erro is not None
        raise ultimo_erro

    @staticmethod
    def _usa_base(client: httpx.Client) -> bool:
        return bool(client.base_url)

    @staticmethod
    def _safe_json(resposta: httpx.Response) -> Any:
        try:
            return resposta.json()
        except Exception:
            return resposta.text[:2000]

    @staticmethod
    def _parse_retry_after(valor: str | None) -> float | None:
        if not valor:
            return None
        try:
            return float(valor)
        except ValueError:
            return None

    def _backoff(self, tentativa: int) -> None:
        if tentativa >= self.max_retries:
            return
        time.sleep(min(8.0, 0.5 * (2**tentativa)))
