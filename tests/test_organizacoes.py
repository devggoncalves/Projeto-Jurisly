import pytest
from django.contrib.auth import get_user_model
from django.db import IntegrityError

from apps.auditoria.models import LogAuditoria
from apps.organizacoes.models import Organizacao, OrganizacaoUsuario, PerfilOrganizacao
from apps.organizacoes.services import (
    filtrar_por_organizacoes_do_usuario,
    usuario_pertence_a_organizacao,
)

Usuario = get_user_model()


@pytest.mark.django_db
class TestOrganizacoes:
    def test_cria_organizacao_com_slug(self):
        org = Organizacao.objects.create(nome="Escritório Alfa")
        assert org.slug == "escritorio-alfa"
        assert org.ativo is True

    def test_slug_unico(self):
        Organizacao.objects.create(nome="Beta", slug="beta")
        with pytest.raises(IntegrityError):
            Organizacao.objects.create(nome="Beta 2", slug="beta")

    def test_membership(self):
        usuario = Usuario.objects.create_user(
            email="membro@jurisly.com",
            password="SenhaForte123!",
            nome="Membro",
        )
        org = Organizacao.objects.create(nome="Gama")
        vinculo = OrganizacaoUsuario.objects.create(
            organizacao=org,
            usuario=usuario,
            perfil=PerfilOrganizacao.PROPRIETARIO,
        )
        assert vinculo.perfil == PerfilOrganizacao.PROPRIETARIO
        assert usuario_pertence_a_organizacao(usuario, org.id)

    def test_impede_membership_duplicado(self):
        usuario = Usuario.objects.create_user(
            email="dup@jurisly.com",
            password="SenhaForte123!",
            nome="Dup",
        )
        org = Organizacao.objects.create(nome="Delta")
        OrganizacaoUsuario.objects.create(organizacao=org, usuario=usuario)
        with pytest.raises(IntegrityError):
            OrganizacaoUsuario.objects.create(organizacao=org, usuario=usuario)

    def test_isolamento_multi_tenant(self):
        u1 = Usuario.objects.create_user(
            email="u1@jurisly.com", password="SenhaForte123!", nome="U1"
        )
        u2 = Usuario.objects.create_user(
            email="u2@jurisly.com", password="SenhaForte123!", nome="U2"
        )
        org1 = Organizacao.objects.create(nome="Org 1")
        org2 = Organizacao.objects.create(nome="Org 2")
        OrganizacaoUsuario.objects.create(organizacao=org1, usuario=u1)
        OrganizacaoUsuario.objects.create(organizacao=org2, usuario=u2)

        LogAuditoria.objects.create(organizacao=org1, acao="LOGIN_SUCESSO")
        LogAuditoria.objects.create(organizacao=org2, acao="LOGIN_SUCESSO")

        qs = filtrar_por_organizacoes_do_usuario(LogAuditoria.objects.all(), u1)
        assert qs.count() == 1
        assert qs.first().organizacao_id == org1.id
        assert not usuario_pertence_a_organizacao(u1, org2.id)
