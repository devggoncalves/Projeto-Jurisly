from __future__ import annotations

from datetime import date, datetime
from typing import Any


def _primeiro(*valores: Any) -> Any:
    for valor in valores:
        if valor is None:
            continue
        if isinstance(valor, str) and not valor.strip():
            continue
        return valor
    return None


def parse_data_djen(valor: Any) -> date | None:
    if valor is None or valor == "":
        return None
    if isinstance(valor, date) and not isinstance(valor, datetime):
        return valor
    if isinstance(valor, datetime):
        return valor.date()
    texto = str(valor).strip()
    for fmt in ("%Y-%m-%d", "%d/%m/%Y", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%dT%H:%M:%S.%f"):
        try:
            return datetime.strptime(texto[:26], fmt).date()
        except ValueError:
            continue
    if "T" in texto:
        try:
            return datetime.fromisoformat(texto.replace("Z", "+00:00")).date()
        except ValueError:
            return None
    return None


def identificador_externo_item(item: dict[str, Any]) -> str:
    hash_valor = _primeiro(item.get("hash"))
    if hash_valor:
        return str(hash_valor)
    id_valor = _primeiro(item.get("id"), item.get("numeroComunicacao"))
    if id_valor is not None:
        return str(id_valor)
    # Fallback determinístico mínimo
    processo = _primeiro(item.get("numero_processo"), item.get("numeroprocessocommascara"), "")
    data = _primeiro(item.get("data_disponibilizacao"), item.get("datadisponibilizacao"), "")
    return f"fallback:{processo}:{data}:{item.get('tipoComunicacao', '')}"


def mapear_item_comunicacao(item: dict[str, Any]) -> dict[str, Any]:
    """Converte item bruto DJEN → campos do model ComunicacaoJudicial."""
    data_disp = parse_data_djen(
        _primeiro(item.get("data_disponibilizacao"), item.get("datadisponibilizacao"))
    )
    data_canc = parse_data_djen(item.get("data_cancelamento"))
    link = _primeiro(item.get("link"), "") or ""
    return {
        "identificador_externo": identificador_externo_item(item),
        "hash": str(_primeiro(item.get("hash"), "") or ""),
        "tipo_comunicacao": str(_primeiro(item.get("tipoComunicacao"), "") or ""),
        "tipo_documento": str(_primeiro(item.get("tipoDocumento"), "") or ""),
        "tribunal": str(_primeiro(item.get("siglaTribunal"), "") or ""),
        "orgao": str(_primeiro(item.get("nomeOrgao"), "") or ""),
        "id_orgao": str(_primeiro(item.get("idOrgao"), "") or ""),
        "numero_processo": str(
            _primeiro(item.get("numero_processo"), item.get("numeroProcesso"), "") or ""
        ),
        "numero_processo_mascarado": str(
            _primeiro(item.get("numeroprocessocommascara"), "") or ""
        ),
        "numero_comunicacao": str(_primeiro(item.get("numeroComunicacao"), "") or ""),
        "meio": str(_primeiro(item.get("meiocompleto"), item.get("meio"), "") or ""),
        "link": link[:500] if link else "",
        "nome_classe": str(_primeiro(item.get("nomeClasse"), "") or ""),
        "codigo_classe": str(_primeiro(item.get("codigoClasse"), "") or ""),
        "texto": str(_primeiro(item.get("texto"), "") or ""),
        "data_disponibilizacao": data_disp,
        "data_cancelamento": data_canc,
        "motivo_cancelamento": str(_primeiro(item.get("motivo_cancelamento"), "") or ""),
        "ativo_origem": item.get("ativo") if isinstance(item.get("ativo"), bool) else None,
        "status_origem": str(_primeiro(item.get("status"), "") or ""),
        "dados_originais": item,
    }


def extrair_advogados_item(item: dict[str, Any]) -> list[dict[str, str]]:
    resultado: list[dict[str, str]] = []
    lista = item.get("destinatarioadvogados") or []
    if not isinstance(lista, list):
        return resultado
    for entrada in lista:
        if not isinstance(entrada, dict):
            continue
        adv = entrada.get("advogado") if isinstance(entrada.get("advogado"), dict) else entrada
        if not isinstance(adv, dict):
            continue
        resultado.append(
            {
                "id": str(_primeiro(adv.get("id"), "") or ""),
                "nome": str(_primeiro(adv.get("nome"), "") or ""),
                "numero_oab": str(
                    _primeiro(adv.get("numero_oab"), adv.get("numeroOab"), "") or ""
                ),
                "uf_oab": str(_primeiro(adv.get("uf_oab"), adv.get("ufOab"), "") or "").upper(),
            }
        )
    return resultado


def chaves_item_achatadas(item: dict[str, Any], prefixo: str = "") -> list[tuple[str, Any]]:
    """Lista (caminho, valor) para exibição completa na UI de testes."""
    pares: list[tuple[str, Any]] = []
    for chave, valor in item.items():
        caminho = f"{prefixo}.{chave}" if prefixo else str(chave)
        if isinstance(valor, dict):
            pares.extend(chaves_item_achatadas(valor, caminho))
        elif isinstance(valor, list):
            if not valor:
                pares.append((caminho, []))
            else:
                for idx, elemento in enumerate(valor):
                    sub = f"{caminho}[{idx}]"
                    if isinstance(elemento, dict):
                        pares.extend(chaves_item_achatadas(elemento, sub))
                    else:
                        pares.append((sub, elemento))
        else:
            pares.append((caminho, valor))
    return pares
