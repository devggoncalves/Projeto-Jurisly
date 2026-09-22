from __future__ import annotations

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_http_methods

from apps.advogados.services import obter_perfil_advogado
from apps.clientes.forms import FormularioCliente, FormularioProcesso
from apps.clientes.models import Cliente, Processo
from apps.core.shell import contexto_shell, organizacao_padrao


def _contexto(request, **extra):
    ctx = contexto_shell(request.user)
    ctx.update(extra)
    return ctx


def _perfil_obrigatorio(request):
    perfil = obter_perfil_advogado(request.user)
    org = organizacao_padrao(request.user)
    if perfil is None or org is None:
        messages.error(
            request,
            "Complete seu cadastro de advogado antes de gerenciar clientes.",
        )
        return None, None
    return perfil, org


@login_required
@require_http_methods(["GET"])
def lista_clientes(request):
    perfil, org = _perfil_obrigatorio(request)
    if perfil is None:
        return redirect("contas:completar_cadastro")
    clientes = Cliente.objects.filter(advogado=perfil).prefetch_related("processos")
    return render(
        request,
        "clientes/lista.html",
        _contexto(request, pagina_ativa="clientes", clientes=clientes),
    )


@login_required
@require_http_methods(["GET", "POST"])
def novo_cliente(request):
    perfil, org = _perfil_obrigatorio(request)
    if perfil is None:
        return redirect("contas:completar_cadastro")

    form = FormularioCliente(request.POST or None)
    if request.method == "POST" and form.is_valid():
        cliente = form.save(commit=False)
        cliente.advogado = perfil
        cliente.organizacao = org
        cliente.save()
        messages.success(request, "Cliente cadastrado.")
        return redirect("clientes:lista")

    return render(
        request,
        "clientes/form.html",
        _contexto(
            request,
            pagina_ativa="clientes",
            form=form,
            titulo="Novo cliente",
        ),
    )


@login_required
@require_http_methods(["GET", "POST"])
def editar_cliente(request, cliente_id):
    perfil, org = _perfil_obrigatorio(request)
    if perfil is None:
        return redirect("contas:completar_cadastro")

    cliente = get_object_or_404(Cliente, pk=cliente_id, advogado=perfil)
    form = FormularioCliente(request.POST or None, instance=cliente)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Cliente atualizado.")
        return redirect("clientes:lista")

    return render(
        request,
        "clientes/form.html",
        _contexto(
            request,
            pagina_ativa="clientes",
            form=form,
            titulo="Editar cliente",
            cliente=cliente,
        ),
    )


@login_required
@require_http_methods(["GET", "POST"])
def novo_processo(request):
    perfil, org = _perfil_obrigatorio(request)
    if perfil is None:
        return redirect("contas:completar_cadastro")

    form = FormularioProcesso(request.POST or None, advogado=perfil)
    if request.method == "POST" and form.is_valid():
        processo = form.save(commit=False)
        processo.advogado = perfil
        processo.organizacao = org
        # Garante que o cliente pertence ao advogado
        if processo.cliente.advogado_id != perfil.id:
            messages.error(request, "Cliente inválido.")
            return redirect("clientes:novo_processo")
        processo.save()
        messages.success(request, "Processo atribuído ao cliente.")
        return redirect("clientes:lista")

    return render(
        request,
        "clientes/form_processo.html",
        _contexto(
            request,
            pagina_ativa="clientes",
            form=form,
            titulo="Atribuir processo",
        ),
    )


@login_required
@require_http_methods(["GET"])
def lista_processos(request):
    perfil, org = _perfil_obrigatorio(request)
    if perfil is None:
        return redirect("contas:completar_cadastro")
    processos = Processo.objects.filter(advogado=perfil).select_related("cliente")
    return render(
        request,
        "clientes/processos.html",
        _contexto(request, pagina_ativa="clientes", processos=processos),
    )
