from __future__ import annotations

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.shortcuts import redirect, render
from django.views.decorators.http import require_http_methods

from apps.advogados.forms import FormularioMeusDadosAdvogado, InscricaoOabFormSet
from apps.advogados.services import obter_ou_preparar_perfil
from apps.core.shell import contexto_shell, organizacao_padrao


def _contexto(request, **extra):
    ctx = contexto_shell(request.user)
    ctx.update(extra)
    return ctx


@login_required
@require_http_methods(["GET", "POST"])
def meus_dados(request):
    """Tela única: o usuário visualiza e altera apenas o próprio perfil de advogado."""
    if organizacao_padrao(request.user) is None:
        messages.error(
            request,
            "Sua conta ainda não está vinculada a uma organização. Contate o suporte.",
        )
        return redirect("core:dashboard")

    perfil = obter_ou_preparar_perfil(request.user)

    if request.method == "POST":
        form = FormularioMeusDadosAdvogado(request.POST, instance=perfil)
        # Valida o pai antes de amarrar o formset (pai pode ainda não ter PK).
        if form.is_valid():
            advogado = form.save(commit=False)
            advogado.usuario = request.user
            advogado.organizacao = organizacao_padrao(request.user)
            advogado.ativo = True
            formset = InscricaoOabFormSet(
                request.POST, instance=advogado, prefix="inscricoes"
            )
            if formset.is_valid():
                with transaction.atomic():
                    advogado.save()
                    formset.instance = advogado
                    formset.save()
                    ativas = list(advogado.inscricoes.filter(ativo=True))
                    if ativas and not any(i.principal for i in ativas):
                        primeira = ativas[0]
                        primeira.principal = True
                        primeira.save(update_fields=["principal", "data_atualizacao"])
                messages.success(request, "Seus dados profissionais foram atualizados.")
                return redirect("advogados:meus_dados")
        else:
            formset = InscricaoOabFormSet(
                request.POST,
                instance=perfil if perfil and perfil.pk else None,
                prefix="inscricoes",
            )
    else:
        form = FormularioMeusDadosAdvogado(instance=perfil)
        formset = InscricaoOabFormSet(
            instance=perfil if perfil and perfil.pk else None,
            prefix="inscricoes",
        )

    principal = None
    if perfil and perfil.pk:
        principal = perfil.inscricao_principal()

    return render(
        request,
        "advogados/meus_dados.html",
        _contexto(
            request,
            pagina_ativa="meus_dados",
            form=form,
            formset=formset,
            advogado=perfil if perfil and perfil.pk else None,
            oab_exibida=principal.oab_formatada if principal else None,
        ),
    )
