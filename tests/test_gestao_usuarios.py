import pytest
from django.urls import reverse

from apps.contas.models import Usuario
from apps.contas.servicos_usuarios import senha_padrao_usuario
from apps.organizacoes.models import Organizacao, OrganizacaoUsuario, PerfilOrganizacao


@pytest.mark.django_db
class TestGestaoUsuarios:
    @pytest.fixture
    def setup_users(self, db):
        admin = Usuario.objects.create_superuser(
            login="admin",
            email="admin@jurisly.com",
            password="SenhaForte123!",
        )
        org = Organizacao.objects.create(nome="Escritório", slug="esc-gestao")
        alvo = Usuario.objects.create_user(
            login="adv@escritorio.com",
            email="adv@escritorio.com",
            password="SenhaAntiga123!",
            nome="Gabriel",
            sobrenome="Souza",
        )
        OrganizacaoUsuario.objects.create(
            organizacao=org,
            usuario=alvo,
            perfil=PerfilOrganizacao.ADVOGADO,
        )
        return admin, org, alvo

    def test_senha_padrao(self, setup_users):
        _, _, alvo = setup_users
        senha = senha_padrao_usuario(alvo)
        assert senha.startswith("Gab")
        assert senha.endswith("#")
        assert len(senha) >= 5

    def test_bloquear_desbloquear(self, client, setup_users):
        admin, _, alvo = setup_users
        client.force_login(admin)
        resp = client.post(
            reverse("contas:acao_usuario", args=[alvo.id]),
            {"acao": "bloquear"},
        )
        assert resp.status_code == 302
        alvo.refresh_from_db()
        assert alvo.ativo is False

        resp = client.post(
            reverse("contas:acao_usuario", args=[alvo.id]),
            {"acao": "desbloquear"},
        )
        assert resp.status_code == 302
        alvo.refresh_from_db()
        assert alvo.ativo is True

    def test_resetar_senha(self, client, setup_users):
        admin, _, alvo = setup_users
        client.force_login(admin)
        senha = senha_padrao_usuario(alvo)
        resp = client.post(
            reverse("contas:acao_usuario", args=[alvo.id]),
            {"acao": "resetar_senha"},
        )
        assert resp.status_code == 302
        alvo.refresh_from_db()
        assert alvo.check_password(senha)
        assert alvo.deve_alterar_senha is True

    def test_excluir(self, client, setup_users):
        admin, _, alvo = setup_users
        client.force_login(admin)
        pk = alvo.id
        resp = client.post(
            reverse("contas:acao_usuario", args=[pk]),
            {"acao": "excluir"},
        )
        assert resp.status_code == 302
        assert not Usuario.objects.filter(pk=pk).exists()
