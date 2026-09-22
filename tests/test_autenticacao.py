from unittest.mock import MagicMock

import pytest
from django.contrib.auth import get_user_model
from django.urls import reverse

from apps.auditoria.models import AcaoAuditoria, LogAuditoria
from apps.advogados.models import Advogado, InscricaoOab, TipoInscricaoOab, UnidadeFederativa
from apps.organizacoes.models import Organizacao, OrganizacaoUsuario, PerfilOrganizacao

Usuario = get_user_model()


@pytest.fixture
def usuario(db):
    return Usuario.objects.create_user(
        login="loginuser",
        email="login@jurisly.com",
        password="SenhaForte123!",
        nome="Login",
        is_staff=True,  # evita sync/onboarding em testes de auth
    )


@pytest.fixture
def mock_sync(monkeypatch):
    resultado = MagicMock(ok=True, total_novos=0, mensagem="ok")
    monkeypatch.setattr(
        "apps.integracoes.djen.sincronizacao.sincronizar_advogado_do_usuario",
        lambda *a, **k: resultado,
    )
    return resultado


@pytest.mark.django_db
class TestAutenticacao:
    def test_login_correto(self, client, usuario, mock_sync):
        resposta = client.post(
            reverse("contas:login"),
            {"username": "loginuser", "password": "SenhaForte123!"},
        )
        assert resposta.status_code == 302
        assert resposta.url == reverse("core:dashboard")
        assert LogAuditoria.objects.filter(acao=AcaoAuditoria.LOGIN_SUCESSO).exists()

    def test_login_por_email_legado(self, client, usuario, mock_sync):
        resposta = client.post(
            reverse("contas:login"),
            {"username": "login@jurisly.com", "password": "SenhaForte123!"},
        )
        assert resposta.status_code == 302

    def test_senha_incorreta(self, client, usuario):
        resposta = client.post(
            reverse("contas:login"),
            {"username": "loginuser", "password": "errada"},
        )
        assert resposta.status_code == 400
        assert LogAuditoria.objects.filter(acao=AcaoAuditoria.LOGIN_FALHA).exists()

    def test_usuario_inexistente(self, client):
        resposta = client.post(
            reverse("contas:login"),
            {"username": "naoexiste", "password": "SenhaForte123!"},
        )
        assert resposta.status_code == 400
        assert b"N" in resposta.content

    def test_usuario_inativo(self, client, usuario):
        usuario.ativo = False
        usuario.save(update_fields=["ativo"])
        resposta = client.post(
            reverse("contas:login"),
            {"username": "loginuser", "password": "SenhaForte123!"},
        )
        assert resposta.status_code == 400

    def test_logout(self, client, usuario):
        client.force_login(usuario)
        resposta = client.post(reverse("contas:logout"))
        assert resposta.status_code == 302
        assert resposta.url == reverse("contas:login")
        assert LogAuditoria.objects.filter(acao=AcaoAuditoria.LOGOUT).exists()

    def test_lembrar_de_mim_define_expiracao(self, client, usuario, settings, mock_sync):
        client.post(
            reverse("contas:login"),
            {
                "username": "loginuser",
                "password": "SenhaForte123!",
                "lembrar": "on",
            },
        )
        assert client.session.get_expiry_age() == settings.SESSION_COOKIE_AGE

    def test_onboarding_obrigatorio(self, client, db, mock_sync):
        usuario = Usuario.objects.create_user(
            login="novoadv",
            password="SenhaForte123!",
        )
        org = Organizacao.objects.create(nome="Org", slug="org-onboard")
        OrganizacaoUsuario.objects.create(
            organizacao=org,
            usuario=usuario,
            perfil=PerfilOrganizacao.ADVOGADO,
        )
        resposta = client.post(
            reverse("contas:login"),
            {"username": "novoadv", "password": "SenhaForte123!"},
        )
        assert resposta.status_code == 302
        assert resposta.url == reverse("contas:completar_cadastro")

        client.force_login(usuario)
        completa = client.post(
            reverse("contas:completar_cadastro"),
            {
                "nome_completo": "Novo Advogado",
                "email": "novo@jurisly.com",
                "numero_oab": "123456",
                "uf_oab": UnidadeFederativa.SP,
            },
        )
        assert completa.status_code == 302, completa.content.decode()[:500]
        assert completa.url == reverse("core:dashboard")
        usuario.refresh_from_db()
        assert usuario.email == "novo@jurisly.com"
        assert InscricaoOab.objects.filter(
            advogado__usuario=usuario, numero="123456", uf="SP"
        ).exists()
        assert usuario.precisa_completar_cadastro is False
