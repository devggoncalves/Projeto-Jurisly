from unittest.mock import MagicMock

import pytest
from django.contrib.auth import get_user_model
from django.urls import reverse

from apps.advogados.models import InscricaoOab, UnidadeFederativa
from apps.auditoria.models import AcaoAuditoria, LogAuditoria
from apps.organizacoes.models import Organizacao, OrganizacaoUsuario, PerfilOrganizacao

Usuario = get_user_model()


@pytest.fixture
def mock_sync(monkeypatch):
    resultado = MagicMock(ok=True, total_novos=0, mensagem="ok")
    monkeypatch.setattr(
        "apps.integracoes.djen.sincronizacao.sincronizar_advogado_do_usuario",
        lambda *a, **k: resultado,
    )
    return resultado


@pytest.fixture
def admin_sistema(db):
    return Usuario.objects.create_superuser(
        login="admin",
        email="admin@jurisly.com",
        password="SenhaForte123!",
    )


@pytest.mark.django_db
class TestCriacaoEPrimeiroAcesso:
    def test_admin_cria_usuario_email_senha(self, client, admin_sistema, mock_sync):
        org = Organizacao.objects.create(nome="Escritório", slug="esc")
        client.force_login(admin_sistema)
        resp = client.post(
            reverse("contas:novo_usuario"),
            {
                "email": "advogado@escritorio.com",
                "senha": "Provisoria123!",
                "senha_confirmacao": "Provisoria123!",
                "organizacao": str(org.id),
            },
        )
        assert resp.status_code == 302
        usuario = Usuario.objects.get(email="advogado@escritorio.com")
        assert usuario.login == "advogado@escritorio.com"
        assert usuario.deve_alterar_senha is True
        assert usuario.precisa_completar_cadastro is True
        assert usuario.check_password("Provisoria123!")

    def test_primeiro_login_exige_senha_e_oab(self, client, mock_sync):
        org = Organizacao.objects.create(nome="Escritório", slug="esc2")
        usuario = Usuario.objects.create_user(
            login="adv@jurisly.com",
            email="adv@jurisly.com",
            password="Provisoria123!",
            deve_alterar_senha=True,
        )
        OrganizacaoUsuario.objects.create(
            organizacao=org,
            usuario=usuario,
            perfil=PerfilOrganizacao.ADVOGADO,
        )

        login = client.post(
            reverse("contas:login"),
            {"username": "adv@jurisly.com", "password": "Provisoria123!"},
        )
        assert login.status_code == 302
        assert login.url == reverse("contas:completar_cadastro")

        completa = client.post(
            reverse("contas:completar_cadastro"),
            {
                "nome_completo": "Advogado Teste",
                "nova_senha": "NovaSenha123!",
                "confirmar_senha": "NovaSenha123!",
                "numero_oab": "496901",
                "uf_oab": UnidadeFederativa.SP,
            },
        )
        assert completa.status_code == 302
        assert completa.url == reverse("core:dashboard")

        usuario.refresh_from_db()
        assert usuario.deve_alterar_senha is False
        assert usuario.check_password("NovaSenha123!")
        assert usuario.precisa_completar_cadastro is False
        assert InscricaoOab.objects.filter(
            advogado__usuario=usuario, numero="496901", uf="SP"
        ).exists()


@pytest.mark.django_db
class TestAutenticacaoBasica:
    @pytest.fixture
    def usuario(self, db):
        return Usuario.objects.create_user(
            login="login@jurisly.com",
            email="login@jurisly.com",
            password="SenhaForte123!",
            nome="Login",
            is_staff=True,
        )

    def test_login_correto(self, client, usuario, mock_sync):
        resposta = client.post(
            reverse("contas:login"),
            {"username": "login@jurisly.com", "password": "SenhaForte123!"},
        )
        assert resposta.status_code == 302
        assert LogAuditoria.objects.filter(acao=AcaoAuditoria.LOGIN_SUCESSO).exists()

    def test_senha_incorreta(self, client, usuario):
        resposta = client.post(
            reverse("contas:login"),
            {"username": "login@jurisly.com", "password": "errada"},
        )
        assert resposta.status_code == 400
