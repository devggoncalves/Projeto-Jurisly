from __future__ import annotations

from urllib.parse import urlparse

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import (
    PasswordResetCompleteView,
    PasswordResetConfirmView,
    PasswordResetDoneView,
    PasswordResetView,
)
from django.db import transaction
from django.shortcuts import redirect, render
from django.urls import reverse, reverse_lazy
from django.utils.decorators import method_decorator
from django.utils.http import url_has_allowed_host_and_scheme
from django.views import View
from django.views.decorators.http import require_http_methods, require_POST

from apps.advogados.models import Advogado, InscricaoOab, TipoInscricaoOab
from apps.contas.forms import (
    FormularioCompletarCadastro,
    FormularioLogin,
    FormularioNovaSenha,
    FormularioRecuperacaoSenha,
)
from apps.contas.services import ServicoAutenticacao
from apps.core.shell import contexto_shell, organizacao_padrao


def _destino_seguro(request, candidato: str | None) -> str:
    padrao = reverse("core:dashboard")
    if not candidato:
        return padrao
    if url_has_allowed_host_and_scheme(
        url=candidato,
        allowed_hosts={request.get_host()},
        require_https=request.is_secure(),
    ):
        caminho = urlparse(candidato).path or candidato
        if caminho.startswith("/"):
            return candidato
    return padrao


class ViewLogin(View):
    template_name = "contas/login.html"

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            if request.user.precisa_completar_cadastro:
                return redirect("contas:completar_cadastro")
            return redirect("core:dashboard")
        return super().dispatch(request, *args, **kwargs)

    def get(self, request):
        form = FormularioLogin(request)
        return render(request, self.template_name, {"form": form})

    def post(self, request):
        form = FormularioLogin(request, data=request.POST)
        login_id = request.POST.get("username", "")
        senha = request.POST.get("password", "")
        lembrar = request.POST.get("lembrar") == "on"

        usuario, erro = ServicoAutenticacao.autenticar(
            request,
            login_id=login_id,
            senha=senha,
            lembrar=lembrar,
        )
        if usuario is None:
            messages.error(request, erro)
            form = FormularioLogin(request, data=request.POST)
            return render(request, self.template_name, {"form": form}, status=400)

        if usuario.precisa_completar_cadastro:
            return redirect("contas:completar_cadastro")

        sync_info = request.session.pop("ultima_sync_djen", None)
        if sync_info and sync_info.get("ok") and sync_info.get("novos"):
            messages.info(
                request,
                f"Sincronização DJEN: {sync_info['novos']} nova(s) comunicação(ões).",
            )

        destino = _destino_seguro(request, request.POST.get("next") or request.GET.get("next"))
        return redirect(destino)


@method_decorator(require_POST, name="dispatch")
class ViewLogout(View):
    def post(self, request):
        ServicoAutenticacao.encerrar_sessao(request)
        return redirect("contas:login")


@login_required
@require_http_methods(["GET", "POST"])
def completar_cadastro(request):
    """Primeiro acesso: e-mail + OAB obrigatórios."""
    if not request.user.precisa_completar_cadastro:
        return redirect("core:dashboard")

    form = FormularioCompletarCadastro(
        request.POST or None, usuario=request.user
    )

    if request.method == "POST" and form.is_valid():
        dados = form.cleaned_data
        organizacao = organizacao_padrao(request.user)
        if organizacao is None:
            messages.error(
                request,
                "Sua conta ainda não está vinculada a uma organização. Contate o administrador.",
            )
            return redirect("contas:completar_cadastro")

        with transaction.atomic():
            usuario = request.user
            usuario.email = dados["email"]
            partes = dados["nome_completo"].split(" ", 1)
            usuario.nome = partes[0]
            usuario.sobrenome = partes[1] if len(partes) > 1 else ""
            usuario.save(update_fields=["email", "nome", "sobrenome", "data_atualizacao"])

            advogado, _ = Advogado.objects.update_or_create(
                usuario=usuario,
                defaults={
                    "organizacao": organizacao,
                    "nome_completo": dados["nome_completo"],
                    "email": dados["email"],
                    "ativo": True,
                },
            )
            InscricaoOab.objects.update_or_create(
                advogado=advogado,
                numero=dados["numero_oab"],
                uf=dados["uf_oab"],
                defaults={
                    "tipo": TipoInscricaoOab.PRINCIPAL,
                    "principal": True,
                    "ativo": True,
                },
            )

        messages.success(request, "Cadastro concluído. Bem-vindo ao Jurisly.")

        try:
            from apps.integracoes.djen.sincronizacao import sincronizar_advogado_do_usuario

            resultado = sincronizar_advogado_do_usuario(usuario)
            if resultado.ok and resultado.total_novos:
                messages.info(
                    request,
                    f"Encontramos {resultado.total_novos} comunicação(ões) no DJEN.",
                )
        except Exception:  # noqa: BLE001
            pass

        return redirect("core:dashboard")

    ctx = contexto_shell(request.user)
    ctx.update({"pagina_ativa": "completar_cadastro", "form": form, "onboarding": True})
    return render(request, "contas/completar_cadastro.html", ctx)


class ViewEsqueciSenha(PasswordResetView):
    template_name = "contas/esqueci_senha.html"
    email_template_name = "contas/email/recuperacao_senha.txt"
    subject_template_name = "contas/email/recuperacao_senha_assunto.txt"
    form_class = FormularioRecuperacaoSenha
    success_url = reverse_lazy("contas:recuperacao_enviada")

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.info(
            self.request,
            (
                "Se existir uma conta associada a este e-mail, "
                "enviaremos as instruções de recuperação."
            ),
        )
        return response


class ViewRecuperacaoEnviada(PasswordResetDoneView):
    template_name = "contas/recuperacao_enviada.html"


class ViewRedefinirSenha(PasswordResetConfirmView):
    template_name = "contas/redefinir_senha.html"
    form_class = FormularioNovaSenha
    success_url = reverse_lazy("contas:senha_redefinida")


class ViewSenhaRedefinida(PasswordResetCompleteView):
    template_name = "contas/senha_redefinida.html"
