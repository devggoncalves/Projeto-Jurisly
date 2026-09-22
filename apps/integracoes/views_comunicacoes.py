from __future__ import annotations

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_http_methods, require_POST

from apps.advogados.services import obter_perfil_advogado
from apps.core.shell import contexto_shell, organizacao_padrao
from apps.integracoes.djen.sincronizacao import sincronizar_advogado_do_usuario
from apps.integracoes.models import (
    ComunicacaoAdvogado,
    StatusComunicacaoAdvogado,
)


def _contexto(request, **extra):
    ctx = contexto_shell(request.user)
    ctx.update(extra)
    return ctx


def _vinculos_do_usuario(usuario):
    advogado = obter_perfil_advogado(usuario)
    if advogado is None:
        return ComunicacaoAdvogado.objects.none(), None
    qs = (
        ComunicacaoAdvogado.objects.filter(advogado=advogado)
        .select_related("comunicacao", "inscricao_oab", "advogado")
        .order_by("-comunicacao__data_disponibilizacao", "-data_criacao")
    )
    return qs, advogado


@login_required
@require_http_methods(["GET"])
def lista_comunicacoes(request):
    qs, advogado = _vinculos_do_usuario(request.user)
    filtro = request.GET.get("filtro", "pendentes")
    if filtro == "nao_visualizados":
        qs = qs.filter(visualizado=False)
    elif filtro == "pendentes":
        qs = qs.filter(status=StatusComunicacaoAdvogado.PENDENTE)
    elif filtro == "todos":
        pass
    else:
        filtro = "pendentes"
        qs = qs.filter(status=StatusComunicacaoAdvogado.PENDENTE)

    return render(
        request,
        "integracoes/comunicacoes_lista.html",
        _contexto(
            request,
            pagina_ativa="comunicacoes",
            vinculos=qs,
            filtro=filtro,
            advogado=advogado,
            total_nao_visualizados=qs.model.objects.filter(
                advogado=advogado, visualizado=False
            ).count()
            if advogado
            else 0,
        ),
    )


@login_required
@require_http_methods(["GET", "POST"])
def detalhe_comunicacao(request, vinculo_id):
    qs, advogado = _vinculos_do_usuario(request.user)
    vinculo = get_object_or_404(qs, pk=vinculo_id)
    comunicacao = vinculo.comunicacao

    if request.method == "GET" and not vinculo.visualizado:
        vinculo.visualizado = True
        vinculo.visualizado_em = timezone.now()
        vinculo.save(update_fields=["visualizado", "visualizado_em", "data_atualizacao"])

    if request.method == "POST":
        acao = request.POST.get("acao")
        if acao == "marcar_nao_visualizado":
            vinculo.visualizado = False
            vinculo.visualizado_em = None
            vinculo.save(update_fields=["visualizado", "visualizado_em", "data_atualizacao"])
            messages.success(request, "Marcado como não visualizado.")
        elif acao == "marcar_visualizado":
            vinculo.visualizado = True
            vinculo.visualizado_em = timezone.now()
            vinculo.save(update_fields=["visualizado", "visualizado_em", "data_atualizacao"])
            messages.success(request, "Marcado como visualizado.")
        elif acao == "confirmar":
            vinculo.status = StatusComunicacaoAdvogado.CONFIRMADA
            vinculo.save(update_fields=["status", "data_atualizacao"])
            messages.success(request, "Comunicação confirmada como sua.")
        elif acao == "rejeitar":
            vinculo.status = StatusComunicacaoAdvogado.REJEITADA
            vinculo.save(update_fields=["status", "data_atualizacao"])
            messages.success(request, "Comunicação rejeitada.")
        return redirect("integracoes:detalhe_comunicacao", vinculo_id=vinculo.id)

    destinatarios = []
    bruto = comunicacao.dados_originais or {}
    if isinstance(bruto.get("destinatarios"), list):
        destinatarios = bruto["destinatarios"]
    advogados_origem = []
    if isinstance(bruto.get("destinatarioadvogados"), list):
        for item in bruto["destinatarioadvogados"]:
            adv = item.get("advogado") if isinstance(item, dict) else None
            if isinstance(adv, dict):
                advogados_origem.append(adv)

    return render(
        request,
        "integracoes/comunicacao_detalhe.html",
        _contexto(
            request,
            pagina_ativa="comunicacoes",
            vinculo=vinculo,
            comunicacao=comunicacao,
            destinatarios=destinatarios,
            advogados_origem=advogados_origem,
            advogado=advogado,
        ),
    )


@login_required
@require_POST
def sincronizar_djen(request):
    if organizacao_padrao(request.user) is None:
        messages.error(request, "Organização não encontrada.")
        return redirect("core:dashboard")

    if request.user.precisa_completar_cadastro:
        return redirect("contas:completar_cadastro")

    resultado = sincronizar_advogado_do_usuario(request.user)
    if resultado.ok:
        messages.success(
            request,
            (
                f"Busca concluída: {resultado.total_encontrado} encontradas, "
                f"{resultado.total_novos} nova(s)."
            ),
        )
    else:
        messages.error(request, resultado.erro or resultado.mensagem)

    next_url = request.POST.get("next") or "core:dashboard"
    if next_url == "integracoes:lista_comunicacoes":
        return redirect("integracoes:lista_comunicacoes")
    return redirect("core:dashboard")
