from __future__ import annotations

import json

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render
from django.views.decorators.http import require_http_methods

from apps.advogados.services import obter_perfil_advogado
from apps.core.shell import contexto_shell, organizacao_padrao
from apps.integracoes.djen.servico import ServicoConsultaDjen
from apps.integracoes.forms import FormularioConsultaDjen


def _contexto(request, **extra):
    ctx = contexto_shell(request.user)
    ctx.update(extra)
    return ctx


@login_required
@require_http_methods(["GET", "POST"])
def consultas_djen(request):
    """
    Menu temporário: consulta a API pública DJEN e exibe o payload completo.
    Depois será removido / incorporado ao dashboard principal.
    """
    organizacao = organizacao_padrao(request.user)
    if organizacao is None:
        messages.error(
            request,
            "Sua conta ainda não está vinculada a uma organização. Contate o suporte.",
        )
        return redirect("core:dashboard")

    perfil = obter_perfil_advogado(request.user)
    form = FormularioConsultaDjen(request.POST or None)
    resultado = None
    json_bruto = None

    if request.method == "POST" and form.is_valid():
        dados = form.cleaned_data
        numero_oab = dados.get("numero_oab") or ""
        uf_oab = dados.get("uf_oab") or ""
        nome_advogado = dados.get("nome_advogado") or ""
        inscricao = None

        if dados.get("usar_perfil") and perfil is not None:
            inscricao = perfil.inscricao_principal()
            if inscricao and not numero_oab:
                numero_oab = inscricao.numero
                uf_oab = inscricao.uf
            if not nome_advogado:
                nome_advogado = perfil.nome_para_api

        servico = ServicoConsultaDjen()
        try:
            resultado = servico.consultar_para_teste(
                organizacao=organizacao,
                advogado=perfil if dados.get("persistir") else None,
                inscricao=inscricao if dados.get("persistir") else None,
                numero_oab=numero_oab,
                uf_oab=uf_oab,
                data_inicio=dados["data_inicio"].isoformat(),
                data_fim=dados["data_fim"].isoformat(),
                nome_advogado=nome_advogado,
                nome_parte=dados.get("nome_parte") or "",
                numero_processo=dados.get("numero_processo") or "",
                sigla_tribunal=dados.get("sigla_tribunal") or "",
                texto=dados.get("texto") or "",
                pagina=dados.get("pagina") or 1,
                itens_por_pagina=dados.get("itens_por_pagina") or 20,
                persistir=bool(dados.get("persistir")) and perfil is not None,
            )
        finally:
            servico.cliente.close()

        if resultado.ok and resultado.resposta:
            messages.success(
                request,
                f"DJEN: {resultado.mensagem} — {resultado.resposta.count} registro(s).",
            )
            json_bruto = json.dumps(
                resultado.resposta.bruto,
                ensure_ascii=False,
                indent=2,
                default=str,
            )
        else:
            messages.error(request, resultado.erro or resultado.mensagem)

    return render(
        request,
        "integracoes/consultas_djen.html",
        _contexto(
            request,
            pagina_ativa="consultas_djen",
            form=form,
            perfil=perfil,
            resultado=resultado,
            json_bruto=json_bruto,
            oab_perfil=(
                perfil.inscricao_principal().oab_formatada
                if perfil and perfil.inscricao_principal()
                else None
            ),
        ),
    )
