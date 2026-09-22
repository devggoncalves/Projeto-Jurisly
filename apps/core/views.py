from django.contrib.auth.decorators import login_required
from django.db import connection
from django.http import JsonResponse
from django.shortcuts import redirect, render
from django.views.decorators.http import require_GET

from apps.advogados.services import obter_perfil_advogado
from apps.clientes.models import Cliente, Processo
from apps.core.shell import contexto_shell
from apps.integracoes.models import ComunicacaoAdvogado, StatusComunicacaoAdvogado


@require_GET
def health(request):
    status = "ok"
    http_status = 200
    try:
        connection.ensure_connection()
    except Exception:  # noqa: BLE001
        status = "error"
        http_status = 503
    return JsonResponse({"status": status}, status=http_status)


def raiz(request):
    if request.user.is_authenticated:
        if request.user.precisa_completar_cadastro:
            return redirect("contas:completar_cadastro")
        return redirect("core:dashboard")
    return redirect("contas:login")


@login_required
@require_GET
def dashboard(request):
    if request.user.precisa_completar_cadastro:
        return redirect("contas:completar_cadastro")

    ctx = contexto_shell(request.user)
    perfil = obter_perfil_advogado(request.user)

    pendentes = 0
    nao_visualizados = 0
    processos = 0
    clientes = 0
    recentes = []

    if perfil is not None:
        vinculos = ComunicacaoAdvogado.objects.filter(advogado=perfil)
        pendentes = vinculos.filter(status=StatusComunicacaoAdvogado.PENDENTE).count()
        nao_visualizados = vinculos.filter(visualizado=False).count()
        processos = Processo.objects.filter(advogado=perfil, ativo=True).count()
        clientes = Cliente.objects.filter(advogado=perfil, ativo=True).count()
        recentes = list(
            vinculos.filter(visualizado=False)
            .select_related("comunicacao")
            .order_by("-comunicacao__data_disponibilizacao", "-data_criacao")[:5]
        )

    ctx.update(
        {
            "pagina_ativa": "dashboard",
            "stats": {
                "processos": processos,
                "intimacoes": pendentes,
                "nao_visualizados": nao_visualizados,
                "prazos": 0,
                "clientes": clientes,
            },
            "alerta_novos": nao_visualizados > 0,
            "recentes_nao_visualizados": recentes,
            "tem_oab": perfil is not None
            and perfil.inscricoes.filter(ativo=True).exists(),
        }
    )
    return render(request, "core/dashboard.html", ctx)
