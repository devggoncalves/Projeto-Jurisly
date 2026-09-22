from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any

from django.db import transaction
from django.utils import timezone

from apps.advogados.models import Advogado, InscricaoOab
from apps.integracoes.djen.cliente import ClienteDjen, ErroDjen, RespostaComunicacoesDjen
from apps.integracoes.djen.mapeamento import (
    chaves_item_achatadas,
    extrair_advogados_item,
    mapear_item_comunicacao,
)
from apps.integracoes.models import (
    ComunicacaoAdvogado,
    ComunicacaoJudicial,
    FonteIntegracao,
    StatusComunicacaoAdvogado,
    StatusSincronizacao,
    SincronizacaoIntegracao,
)

logger = logging.getLogger(__name__)


@dataclass
class ResultadoConsultaTeste:
    ok: bool
    mensagem: str
    resposta: RespostaComunicacoesDjen | None = None
    itens_enriquecidos: list[dict[str, Any]] = field(default_factory=list)
    sincronizacao: SincronizacaoIntegracao | None = None
    erro: str = ""


class ServicoConsultaDjen:
    """
    Orquestra consulta DJEN para a tela temporária de testes e
    (opcionalmente) persiste comunicações com status PENDENTE.
    """

    def __init__(self, cliente: ClienteDjen | None = None):
        self.cliente = cliente or ClienteDjen()

    def consultar_para_teste(
        self,
        *,
        organizacao,
        advogado: Advogado | None = None,
        inscricao: InscricaoOab | None = None,
        numero_oab: str = "",
        uf_oab: str = "",
        data_inicio: str = "",
        data_fim: str = "",
        nome_advogado: str = "",
        nome_parte: str = "",
        numero_processo: str = "",
        sigla_tribunal: str = "",
        texto: str = "",
        pagina: int = 1,
        itens_por_pagina: int = 20,
        persistir: bool = False,
    ) -> ResultadoConsultaTeste:
        if inscricao is not None:
            numero_oab = inscricao.numero
            uf_oab = inscricao.uf
        elif advogado is not None and not numero_oab:
            principal = advogado.inscricao_principal()
            if principal:
                numero_oab = principal.numero
                uf_oab = principal.uf
            if not nome_advogado:
                nome_advogado = advogado.nome_para_api

        parametros = {
            "numero_oab": numero_oab,
            "uf_oab": uf_oab,
            "data_inicio": data_inicio,
            "data_fim": data_fim,
            "nome_advogado": nome_advogado,
            "nome_parte": nome_parte,
            "numero_processo": numero_processo,
            "sigla_tribunal": sigla_tribunal,
            "texto": texto,
            "pagina": pagina,
            "itens_por_pagina": itens_por_pagina,
        }

        sync = None
        if persistir:
            sync = SincronizacaoIntegracao.objects.create(
                organizacao=organizacao,
                fonte=FonteIntegracao.DJEN,
                status=StatusSincronizacao.EM_ANDAMENTO,
                parametros=parametros,
            )

        try:
            resposta = self.cliente.consultar_comunicacoes(
                numero_oab=numero_oab or None,
                uf_oab=uf_oab or None,
                data_inicio=data_inicio or None,
                data_fim=data_fim or None,
                nome_advogado=nome_advogado or None,
                nome_parte=nome_parte or None,
                numero_processo=numero_processo or None,
                sigla_tribunal=sigla_tribunal or None,
                texto=texto or None,
                pagina=pagina,
                itens_por_pagina=itens_por_pagina,
            )
        except ErroDjen as exc:
            logger.warning("Falha consulta DJEN: %s", exc)
            if sync:
                sync.status = StatusSincronizacao.ERRO
                sync.mensagem = str(exc)
                sync.finalizado_em = timezone.now()
                sync.save(
                    update_fields=["status", "mensagem", "finalizado_em"]
                )
            return ResultadoConsultaTeste(
                ok=False,
                mensagem="Falha ao consultar a API pública do DJEN.",
                erro=str(exc),
                sincronizacao=sync,
            )

        itens_enriquecidos = []
        novos = 0
        atualizados = 0

        for item in resposta.items:
            mapeado = mapear_item_comunicacao(item)
            advogados_origem = extrair_advogados_item(item)
            enriquecido = {
                "mapeado": mapeado,
                "advogados_origem": advogados_origem,
                "campos_achatados": chaves_item_achatadas(item),
                "bruto": item,
            }
            if persistir and advogado is not None:
                comunicacao, criado = self._upsert_comunicacao(
                    organizacao=organizacao,
                    mapeado=mapeado,
                )
                vinculo, vinculo_novo = self._vincular_advogado(
                    organizacao=organizacao,
                    comunicacao=comunicacao,
                    advogado=advogado,
                    inscricao=inscricao,
                    advogados_origem=advogados_origem,
                    numero_oab=numero_oab,
                    uf_oab=uf_oab,
                )
                if vinculo_novo:
                    novos += 1
                else:
                    atualizados += 1
                enriquecido["persistido_id"] = str(comunicacao.id)
                enriquecido["vinculo_id"] = str(vinculo.id)
            itens_enriquecidos.append(enriquecido)

        if sync:
            sync.status = StatusSincronizacao.SUCESSO
            sync.total_encontrado = resposta.count
            sync.total_novos = novos
            sync.total_atualizados = atualizados
            sync.mensagem = resposta.message or "Consulta concluída."
            sync.detalhes = {
                "rate_limit": resposta.headers_rate_limit,
                "url": resposta.url,
                "pagina": resposta.pagina,
            }
            sync.finalizado_em = timezone.now()
            sync.save()

        return ResultadoConsultaTeste(
            ok=True,
            mensagem=resposta.message or "Consulta concluída.",
            resposta=resposta,
            itens_enriquecidos=itens_enriquecidos,
            sincronizacao=sync,
        )

    @transaction.atomic
    def _upsert_comunicacao(self, *, organizacao, mapeado: dict[str, Any]):
        identificador = mapeado["identificador_externo"]
        defaults = {k: v for k, v in mapeado.items() if k != "identificador_externo"}
        defaults["fonte"] = FonteIntegracao.DJEN
        obj, criado = ComunicacaoJudicial.objects.update_or_create(
            organizacao=organizacao,
            fonte=FonteIntegracao.DJEN,
            identificador_externo=identificador,
            defaults=defaults,
        )
        return obj, criado

    def _vincular_advogado(
        self,
        *,
        organizacao,
        comunicacao: ComunicacaoJudicial,
        advogado: Advogado,
        inscricao: InscricaoOab | None,
        advogados_origem: list[dict[str, str]],
        numero_oab: str,
        uf_oab: str,
    ) -> ComunicacaoAdvogado:
        match = None
        numero_norm = (numero_oab or "").replace("-", "").upper()
        for cand in advogados_origem:
            cand_num = (cand.get("numero_oab") or "").replace("-", "").upper()
            cand_uf = (cand.get("uf_oab") or "").upper()
            if numero_norm and cand_num.startswith(numero_norm[: len(numero_norm)]) and (
                not uf_oab or cand_uf == uf_oab.upper()
            ):
                match = cand
                break
        if match is None and advogados_origem:
            match = advogados_origem[0]

        vinculo, criado = ComunicacaoAdvogado.objects.get_or_create(
            comunicacao=comunicacao,
            advogado=advogado,
            defaults={
                "organizacao": organizacao,
                "inscricao_oab": inscricao,
                "status": StatusComunicacaoAdvogado.PENDENTE,
                "visualizado": False,
                "nome_advogado_origem": (match or {}).get("nome", ""),
                "numero_oab_origem": (match or {}).get("numero_oab", ""),
                "uf_oab_origem": (match or {}).get("uf_oab", ""),
            },
        )
        return vinculo, criado
