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
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse, reverse_lazy
from django.utils.decorators import method_decorator
from django.utils.http import url_has_allowed_host_and_scheme
from django.views import View
from django.views.decorators.http import require_http_methods, require_POST

from apps.advogados.models import Advogado, InscricaoOab, TipoInscricaoOab
from apps.contas.admin_forms import FormularioNovoAdvogadoApp
from apps.contas.forms import (
    FormularioLogin,
    FormularioNovaSenha,
    FormularioPrimeiroAcesso,
    FormularioRecuperacaoSenha,
)
from apps.contas.managers import normalizar_login
from apps.contas.models import Usuario
from apps.contas.services import ServicoAutenticacao
from apps.contas.permissions import pode_gerenciar_usuarios
from apps.contas.servicos_usuarios import (
    pode_atuar_sobre,
    senha_padrao_usuario,
    usuarios_gerenciaveis_por,
)
from apps.core.shell import contexto_shell, organizacao_padrao
from apps.organizacoes.models import OrganizacaoUsuario, PerfilOrganizacao
from apps.organizacoes.services import organizacoes_do_usuario


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
    """Primeiro acesso: alterar senha provisória + cadastrar OAB."""
    if not request.user.precisa_completar_cadastro:
        return redirect("core:dashboard")

    form = FormularioPrimeiroAcesso(request.POST or None, usuario=request.user)

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
            usuario.set_password(dados["nova_senha"])
            usuario.deve_alterar_senha = False
            partes = dados["nome_completo"].split(" ", 1)
            usuario.nome = partes[0]
            usuario.sobrenome = partes[1] if len(partes) > 1 else ""
            if not usuario.email:
                usuario.email = usuario.login if "@" in usuario.login else usuario.email
            usuario.save()

            advogado, _ = Advogado.objects.update_or_create(
                usuario=usuario,
                defaults={
                    "organizacao": organizacao,
                    "nome_completo": dados["nome_completo"],
                    "email": usuario.email or "",
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

        # Mantém a sessão após set_password
        from django.contrib.auth import update_session_auth_hash

        update_session_auth_hash(request, usuario)

        messages.success(request, "Senha atualizada e OAB cadastrada. Bem-vindo ao Jurisly.")

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
    ctx.update(
        {
            "pagina_ativa": "completar_cadastro",
            "form": form,
            "onboarding": True,
            "email_usuario": request.user.email or request.user.login,
        }
    )
    return render(request, "contas/completar_cadastro.html", ctx)


@login_required
@require_http_methods(["GET"])
def lista_usuarios(request):
    if not pode_gerenciar_usuarios(request.user):
        messages.error(request, "Você não tem permissão para gerenciar usuários.")
        return redirect("core:dashboard")

    usuarios = usuarios_gerenciaveis_por(request.user)
    return render(
        request,
        "contas/usuarios_lista.html",
        contexto_shell(request.user)
        | {"pagina_ativa": "usuarios", "usuarios": usuarios},
    )


@login_required
@require_POST
def acao_usuario(request, usuario_id):
    """Bloquear, desbloquear, resetar senha padrão ou excluir usuário."""
    if not pode_gerenciar_usuarios(request.user):
        messages.error(request, "Você não tem permissão para gerenciar usuários.")
        return redirect("core:dashboard")

    alvo = get_object_or_404(Usuario, pk=usuario_id)
    if not pode_atuar_sobre(request.user, alvo):
        messages.error(request, "Você não pode gerenciar este usuário.")
        return redirect("contas:lista_usuarios")

    acao = request.POST.get("acao")
    if acao == "bloquear":
        alvo.ativo = False
        alvo.save(update_fields=["ativo", "data_atualizacao"])
        messages.success(request, f"Usuário {alvo.email or alvo.login} bloqueado.")
    elif acao == "desbloquear":
        alvo.ativo = True
        alvo.save(update_fields=["ativo", "data_atualizacao"])
        messages.success(request, f"Usuário {alvo.email or alvo.login} desbloqueado.")
    elif acao == "resetar_senha":
        senha = senha_padrao_usuario(alvo)
        alvo.set_password(senha)
        alvo.deve_alterar_senha = True
        alvo.save(update_fields=["password", "deve_alterar_senha", "data_atualizacao"])
        messages.warning(
            request,
            (
                f"Senha de {alvo.email or alvo.login} redefinida para: {senha}. "
                "No próximo login ele deverá alterá-la."
            ),
        )
    elif acao == "excluir":
        identificador = alvo.email or alvo.login
        alvo.delete()
        messages.success(request, f"Usuário {identificador} excluído.")
    else:
        messages.error(request, "Ação inválida.")

    return redirect("contas:lista_usuarios")


@login_required
@require_http_methods(["GET", "POST"])
def novo_usuario(request):
    """Admin do sistema cria advogado com e-mail + senha provisória."""
    if not pode_gerenciar_usuarios(request.user):
        messages.error(request, "Você não tem permissão para criar usuários.")
        return redirect("core:dashboard")

    orgs = organizacoes_do_usuario(request.user)
    if request.user.is_staff or request.user.is_superuser:
        from apps.organizacoes.models import Organizacao

        qs_org = Organizacao.objects.filter(ativo=True)
    else:
        qs_org = orgs

    form = FormularioNovoAdvogadoApp(
        request.POST or None, organizacoes_queryset=qs_org
    )
    if not form.is_bound and qs_org.count() == 1:
        form.fields["organizacao"].initial = qs_org.first()

    if request.method == "POST" and form.is_valid():
        dados = form.cleaned_data
        email = dados["email"]
        with transaction.atomic():
            usuario = Usuario.objects.create_user(
                login=normalizar_login(email),
                email=email,
                password=dados["senha"],
                deve_alterar_senha=True,
            )
            OrganizacaoUsuario.objects.get_or_create(
                organizacao=dados["organizacao"],
                usuario=usuario,
                defaults={"perfil": PerfilOrganizacao.ADVOGADO, "ativo": True},
            )
        messages.success(
            request,
            (
                f"Usuário {email} criado. Informe a senha provisória ao advogado. "
                "No primeiro login ele deverá alterar a senha e cadastrar a OAB."
            ),
        )
        return redirect("contas:lista_usuarios")

    return render(
        request,
        "contas/usuario_novo.html",
        contexto_shell(request.user)
        | {"pagina_ativa": "usuarios", "form": form},
    )


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
