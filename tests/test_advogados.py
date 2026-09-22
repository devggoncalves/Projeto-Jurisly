import pytest
from django.urls import reverse

from apps.advogados.models import Advogado, InscricaoOab, TipoInscricaoOab, UnidadeFederativa
from apps.contas.models import Usuario
from apps.organizacoes.models import Organizacao, OrganizacaoUsuario, PerfilOrganizacao


@pytest.fixture
def usuario_advogado(db):
    usuario = Usuario.objects.create_user(
        login="gabriel",
        email="gabriel@teste.com",
        password="SenhaForte123!",
        nome="Gabriel",
        sobrenome="Souza",
    )
    org = Organizacao.objects.create(nome="Escritório Gabriel", slug="esc-gabriel")
    OrganizacaoUsuario.objects.create(
        organizacao=org,
        usuario=usuario,
        perfil=PerfilOrganizacao.ADVOGADO,
    )
    advogado = Advogado.objects.create(
        usuario=usuario,
        organizacao=org,
        nome_completo="Gabriel Souza",
        email="gabriel@teste.com",
    )
    InscricaoOab.objects.create(
        advogado=advogado,
        numero="111000",
        uf=UnidadeFederativa.SP,
        tipo=TipoInscricaoOab.PRINCIPAL,
        principal=True,
        ativo=True,
    )
    return usuario, org


@pytest.mark.django_db
class TestMeusDadosAdvogado:
    def test_exige_login(self, client):
        resposta = client.get(reverse("advogados:meus_dados"))
        assert resposta.status_code == 302
        assert reverse("contas:login") in resposta.url

    def test_usuario_edita_apenas_proprios_dados(self, client, usuario_advogado):
        usuario, org = usuario_advogado
        client.force_login(usuario)
        inscricao = usuario.advogado.inscricoes.get()

        resposta = client.post(
            reverse("advogados:meus_dados"),
            {
                "nome_completo": "Gabriel Souza",
                "nome_consulta": "",
                "email": "gabriel@teste.com",
                "telefone": "11999990000",
                "cpf": "52998224725",
                "inscricoes-TOTAL_FORMS": "1",
                "inscricoes-INITIAL_FORMS": "1",
                "inscricoes-MIN_NUM_FORMS": "1",
                "inscricoes-MAX_NUM_FORMS": "1000",
                "inscricoes-0-id": str(inscricao.id),
                "inscricoes-0-numero": "496901",
                "inscricoes-0-uf": UnidadeFederativa.SP,
                "inscricoes-0-tipo": TipoInscricaoOab.PRINCIPAL,
                "inscricoes-0-principal": "on",
                "inscricoes-0-ativo": "on",
            },
        )
        assert resposta.status_code == 302
        perfil = Advogado.objects.get(usuario=usuario)
        assert perfil.organizacao_id == org.id
        assert perfil.nome_completo == "Gabriel Souza"
        assert perfil.inscricoes.filter(numero="496901", uf="SP").exists()
        assert Advogado.objects.filter(usuario=usuario).count() == 1

    def test_nao_acessa_perfil_de_outro(self, client, usuario_advogado):
        usuario, org = usuario_advogado
        outro = Usuario.objects.create_user(
            login="outro",
            email="outro@teste.com",
            password="SenhaForte123!",
            nome="Outro",
        )
        org2 = Organizacao.objects.create(nome="Outra", slug="outra")
        OrganizacaoUsuario.objects.create(
            organizacao=org2,
            usuario=outro,
            perfil=PerfilOrganizacao.ADVOGADO,
        )
        outro_adv = Advogado.objects.create(
            usuario=outro,
            organizacao=org2,
            nome_completo="Outro Advogado",
            email="outro@teste.com",
        )
        InscricaoOab.objects.create(
            advogado=outro_adv,
            numero="111111",
            uf=UnidadeFederativa.RJ,
            principal=True,
        )

        client.force_login(usuario)
        resposta = client.get(reverse("advogados:meus_dados"))
        assert resposta.status_code == 200
        assert b"111111" not in resposta.content
