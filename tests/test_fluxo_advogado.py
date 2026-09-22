import pytest
from django.urls import reverse

from apps.advogados.models import Advogado, InscricaoOab, TipoInscricaoOab, UnidadeFederativa
from apps.clientes.models import Cliente, Processo
from apps.contas.models import Usuario
from apps.integracoes.models import (
    ComunicacaoAdvogado,
    ComunicacaoJudicial,
    FonteIntegracao,
    StatusComunicacaoAdvogado,
)
from apps.organizacoes.models import Organizacao, OrganizacaoUsuario, PerfilOrganizacao


@pytest.fixture
def advogado_completo(db):
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
        numero="496901",
        uf=UnidadeFederativa.SP,
        tipo=TipoInscricaoOab.PRINCIPAL,
        principal=True,
    )
    return usuario, org, advogado


@pytest.mark.django_db
class TestDashboardEComunicacoes:
    def test_dashboard_conta_pendentes(self, client, advogado_completo):
        usuario, org, advogado = advogado_completo
        com = ComunicacaoJudicial.objects.create(
            organizacao=org,
            fonte=FonteIntegracao.DJEN,
            identificador_externo="hash1",
            hash="hash1",
            tipo_comunicacao="Intimação",
            numero_processo="123",
        )
        ComunicacaoAdvogado.objects.create(
            organizacao=org,
            comunicacao=com,
            advogado=advogado,
            status=StatusComunicacaoAdvogado.PENDENTE,
            visualizado=False,
        )
        client.force_login(usuario)
        resposta = client.get(reverse("core:dashboard"))
        assert resposta.status_code == 200
        assert resposta.context["stats"]["intimacoes"] == 1
        assert resposta.context["stats"]["nao_visualizados"] == 1

    def test_detalhe_marca_visualizado(self, client, advogado_completo):
        usuario, org, advogado = advogado_completo
        com = ComunicacaoJudicial.objects.create(
            organizacao=org,
            fonte=FonteIntegracao.DJEN,
            identificador_externo="hash2",
            hash="hash2",
            tipo_comunicacao="Intimação",
            texto="Texto da intimação",
            tribunal="TJSP",
        )
        vinculo = ComunicacaoAdvogado.objects.create(
            organizacao=org,
            comunicacao=com,
            advogado=advogado,
            visualizado=False,
        )
        client.force_login(usuario)
        resposta = client.get(reverse("integracoes:detalhe_comunicacao", args=[vinculo.id]))
        assert resposta.status_code == 200
        assert "Texto da intimação" in resposta.content.decode("utf-8")
        vinculo.refresh_from_db()
        assert vinculo.visualizado is True

    def test_cliente_e_processo(self, client, advogado_completo):
        usuario, org, advogado = advogado_completo
        client.force_login(usuario)
        resp = client.post(
            reverse("clientes:novo"),
            {
                "nome": "Maria Cliente",
                "documento": "52998224725",
                "email": "maria@teste.com",
                "telefone": "",
                "observacoes": "",
                "ativo": "on",
            },
        )
        assert resp.status_code == 302
        cliente = Cliente.objects.get(nome="Maria Cliente")
        resp2 = client.post(
            reverse("clientes:novo_processo"),
            {
                "cliente": str(cliente.id),
                "numero": "00000000000000000000",
                "numero_mascarado": "0000000-00.0000.0.00.0000",
                "tribunal": "TJSP",
                "classe": "",
                "assunto": "",
                "ativo": "on",
            },
        )
        assert resp2.status_code == 302
        assert Processo.objects.filter(cliente=cliente, numero="00000000000000000000").exists()
