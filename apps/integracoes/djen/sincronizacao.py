from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import date, timedelta

from django.conf import settings
from django.utils import timezone

from apps.advogados.services import obter_perfil_advogado
from apps.integracoes.djen.cliente import ClienteDjen, ErroDjen
from apps.integracoes.djen.mapeamento import extrair_advogados_item, mapear_item_comunicacao
from apps.integracoes.djen.servico import ServicoConsultaDjen
from apps.integracoes.models import (
    FonteIntegracao,
    StatusSincronizacao,
    SincronizacaoIntegracao,
)

logger = logging.getLogger(__name__)


@dataclass
class ResultadoSincronizacao:
    ok: bool
    mensagem: str
    total_encontrado: int = 0
    total_novos: int = 0
    total_atualizados: int = 0
    erro: str = ""


def sincronizar_advogado_do_usuario(usuario, *, dias: int | None = None) -> ResultadoSincronizacao:
    advogado = obter_perfil_advogado(usuario)
    if advogado is None:
        return ResultadoSincronizacao(ok=False, mensagem="Perfil de advogado não encontrado.")
    return sincronizar_advogado(advogado, dias=dias)


def sincronizar_advogado(advogado, *, dias: int | None = None) -> ResultadoSincronizacao:
    """
    Busca comunicações DJEN das OAB ativas do advogado na janela de dias
    e persiste vínculos como PENDENTE / não visualizado.
    """
    inscricoes = list(advogado.inscricoes.filter(ativo=True))
    if not inscricoes:
        return ResultadoSincronizacao(ok=False, mensagem="Nenhuma OAB ativa cadastrada.")

    dias = dias if dias is not None else settings.DJEN_DIAS_SINCRONIZACAO
    hoje = date.today()
    data_inicio = (hoje - timedelta(days=dias)).isoformat()
    data_fim = hoje.isoformat()
    organizacao = advogado.organizacao

    sync = SincronizacaoIntegracao.objects.create(
        organizacao=organizacao,
        fonte=FonteIntegracao.DJEN,
        status=StatusSincronizacao.EM_ANDAMENTO,
        parametros={
            "advogado_id": str(advogado.id),
            "data_inicio": data_inicio,
            "data_fim": data_fim,
            "oabs": [f"{i.uf}/{i.numero}" for i in inscricoes],
        },
        iniciado_em=timezone.now(),
    )

    servico = ServicoConsultaDjen()
    total_encontrado = 0
    total_novos = 0
    total_atualizados = 0
    erros: list[str] = []

    try:
        for inscricao in inscricoes:
            pagina = 1
            while True:
                try:
                    resposta = servico.cliente.consultar_comunicacoes(
                        numero_oab=inscricao.numero,
                        uf_oab=inscricao.uf,
                        data_inicio=data_inicio,
                        data_fim=data_fim,
                        pagina=pagina,
                        itens_por_pagina=settings.DJEN_ITENS_POR_PAGINA,
                    )
                except ErroDjen as exc:
                    erros.append(str(exc))
                    break

                total_encontrado += resposta.count if pagina == 1 else 0
                for item in resposta.items:
                    mapeado = mapear_item_comunicacao(item)
                    comunicacao, criado_com = servico._upsert_comunicacao(
                        organizacao=organizacao,
                        mapeado=mapeado,
                    )
                    _, criado_vinc = servico._vincular_advogado(
                        organizacao=organizacao,
                        comunicacao=comunicacao,
                        advogado=advogado,
                        inscricao=inscricao,
                        advogados_origem=extrair_advogados_item(item),
                        numero_oab=inscricao.numero,
                        uf_oab=inscricao.uf,
                    )
                    if criado_vinc:
                        total_novos += 1
                    else:
                        total_atualizados += 1
                    if criado_com:
                        pass

                if not resposta.items or len(resposta.items) < resposta.itens_por_pagina:
                    break
                if pagina * resposta.itens_por_pagina >= resposta.count:
                    break
                pagina += 1
                if pagina > 100:
                    break
    finally:
        servico.cliente.close()

    if erros and total_novos == 0 and total_atualizados == 0:
        sync.status = StatusSincronizacao.ERRO
        sync.mensagem = "; ".join(erros)
        sync.finalizado_em = timezone.now()
        sync.save()
        return ResultadoSincronizacao(
            ok=False,
            mensagem="Falha ao sincronizar com o DJEN.",
            erro=sync.mensagem,
        )

    sync.status = StatusSincronizacao.PARCIAL if erros else StatusSincronizacao.SUCESSO
    sync.total_encontrado = total_encontrado
    sync.total_novos = total_novos
    sync.total_atualizados = total_atualizados
    sync.total_erros = len(erros)
    sync.mensagem = "Sincronização concluída."
    sync.detalhes = {"erros": erros}
    sync.finalizado_em = timezone.now()
    sync.save()

    return ResultadoSincronizacao(
        ok=True,
        mensagem=sync.mensagem,
        total_encontrado=total_encontrado,
        total_novos=total_novos,
        total_atualizados=total_atualizados,
    )
