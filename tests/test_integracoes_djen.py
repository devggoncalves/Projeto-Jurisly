import json
from datetime import date, timedelta
from unittest.mock import MagicMock

import httpx
import pytest
from django.urls import reverse

from apps.advogados.models import Advogado, InscricaoOab, TipoInscricaoOab, UnidadeFederativa
from apps.contas.models import Usuario
from apps.integracoes.djen.cliente import ClienteDjen
from apps.integracoes.djen.mapeamento import mapear_item_comunicacao
from apps.integracoes.djen.servico import ServicoConsultaDjen
from apps.integracoes.models import ComunicacaoAdvogado, StatusComunicacaoAdvogado
from apps.organizacoes.models import Organizacao, OrganizacaoUsuario, PerfilOrganizacao


@pytest.fixture
def usuario_advogado(db):
    usuario = Usuario.objects.create_user(
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
        cpf="52998224725",
    )
    InscricaoOab.objects.create(
        advogado=advogado,
        numero="496901",
        uf=UnidadeFederativa.SP,
        tipo=TipoInscricaoOab.PRINCIPAL,
        principal=True,
    )
    return usuario, org, advogado


SAMPLE_ITEM = {
    "id": 123,
    "hash": "abcHASH123",
    "data_disponibilizacao": "2026-09-02",
    "siglaTribunal": "TJSP",
    "tipoComunicacao": "Intimação",
    "tipoDocumento": "Intimação",
    "nomeOrgao": "1ª Vara Cível",
    "idOrgao": "12345",
    "texto": "Intimação de despacho.",
    "numero_processo": "00000000000000000000",
    "numeroprocessocommascara": "0000000-00.0000.0.00.0000",
    "meio": "D",
    "meiocompleto": "Diário de Justiça Eletrônico Nacional",
    "link": "https://example.com/doc",
    "nomeClasse": "Procedimento Comum",
    "codigoClasse": "7",
    "numeroComunicacao": "999",
    "ativo": True,
    "status": "P",
    "destinatarioadvogados": [
        {
            "advogado": {
                "id": 1,
                "nome": "Outro Nome",
                "numero_oab": "496901",
                "uf_oab": "SP",
            }
        }
    ],
}


class TestMapeamentoDjen:
    def test_mapear_item(self):
        mapeado = mapear_item_comunicacao(SAMPLE_ITEM)
        assert mapeado["identificador_externo"] == "abcHASH123"
        assert mapeado["tribunal"] == "TJSP"
        assert mapeado["data_disponibilizacao"] == date(2026, 9, 2)
        assert mapeado["numero_processo"] == "00000000000000000000"


class TestClienteDjen:
    def test_consulta_com_mock_transport(self):
        envelope = {
            "status": "success",
            "message": "Sucesso",
            "count": 1,
            "items": [SAMPLE_ITEM],
        }

        def handler(request: httpx.Request) -> httpx.Response:
            assert "/api/v1/comunicacao" in str(request.url)
            assert request.url.params.get("numeroOab") == "496901"
            assert request.url.params.get("ufOab") == "SP"
            return httpx.Response(
                200,
                json=envelope,
                headers={"x-ratelimit-limit": "20", "x-ratelimit-remaining": "19"},
            )

        transport = httpx.MockTransport(handler)
        with httpx.Client(
            transport=transport, base_url="https://comunicaapi.pje.jus.br"
        ) as http:
            cliente = ClienteDjen(client=http)
            resp = cliente.consultar_comunicacoes(
                numero_oab="496901",
                uf_oab="SP",
                data_inicio="2026-09-01",
                data_fim="2026-09-03",
            )
        assert resp.count == 1
        assert resp.items[0]["hash"] == "abcHASH123"
        assert resp.headers_rate_limit["x-ratelimit-limit"] == "20"


@pytest.mark.django_db
class TestServicoConsultaDjen:
    def test_persiste_como_pendente(self, usuario_advogado):
        usuario, org, advogado = usuario_advogado
        envelope = {
            "status": "success",
            "message": "Sucesso",
            "count": 1,
            "items": [SAMPLE_ITEM],
        }

        def handler(request: httpx.Request) -> httpx.Response:
            return httpx.Response(200, json=envelope)

        transport = httpx.MockTransport(handler)
        with httpx.Client(
            transport=transport, base_url="https://comunicaapi.pje.jus.br"
        ) as http:
            servico = ServicoConsultaDjen(cliente=ClienteDjen(client=http))
            resultado = servico.consultar_para_teste(
                organizacao=org,
                advogado=advogado,
                numero_oab="496901",
                uf_oab="SP",
                data_inicio="2026-09-01",
                data_fim="2026-09-03",
                persistir=True,
            )

        assert resultado.ok
        vinculo = ComunicacaoAdvogado.objects.get(advogado=advogado)
        assert vinculo.status == StatusComunicacaoAdvogado.PENDENTE
        assert vinculo.nome_advogado_origem == "Outro Nome"


@pytest.mark.django_db
class TestMeusDadosEnriquecido:
    def test_salva_nome_completo_e_oab(self, client, usuario_advogado):
        usuario, org, advogado = usuario_advogado
        client.force_login(usuario)
        inscricao = advogado.inscricoes.get()

        resposta = client.post(
            reverse("advogados:meus_dados"),
            {
                "nome_completo": "Gabriel Mitkawa Souza",
                "nome_consulta": "Gabriel Souza",
                "email": "gabriel@teste.com",
                "telefone": "11999990000",
                "cpf": "52998224725",
                "inscricoes-TOTAL_FORMS": "2",
                "inscricoes-INITIAL_FORMS": "1",
                "inscricoes-MIN_NUM_FORMS": "1",
                "inscricoes-MAX_NUM_FORMS": "1000",
                "inscricoes-0-id": str(inscricao.id),
                "inscricoes-0-numero": "496901",
                "inscricoes-0-uf": UnidadeFederativa.SP,
                "inscricoes-0-tipo": TipoInscricaoOab.PRINCIPAL,
                "inscricoes-0-principal": "on",
                "inscricoes-0-ativo": "on",
                "inscricoes-1-numero": "",
                "inscricoes-1-uf": "",
                "inscricoes-1-tipo": TipoInscricaoOab.SUPLEMENTAR,
            },
        )
        assert resposta.status_code == 302
        advogado.refresh_from_db()
        assert advogado.nome_completo == "Gabriel Mitkawa Souza"
        assert advogado.nome_consulta == "Gabriel Souza"
        assert advogado.inscricoes.filter(numero="496901", uf="SP").exists()


@pytest.mark.django_db
class TestConsultasDjenView:
    def test_exige_login(self, client):
        resposta = client.get(reverse("integracoes:consultas_djen"))
        assert resposta.status_code == 302
        assert reverse("contas:login") in resposta.url

    def test_consulta_mockada_exibe_payload(self, client, usuario_advogado, monkeypatch):
        usuario, org, advogado = usuario_advogado
        client.force_login(usuario)

        resultado = MagicMock()
        resultado.ok = True
        resultado.mensagem = "Sucesso"
        resultado.erro = ""
        resultado.itens_enriquecidos = [
            {
                "mapeado": mapear_item_comunicacao(SAMPLE_ITEM),
                "advogados_origem": [
                    {
                        "id": "1",
                        "nome": "Outro Nome",
                        "numero_oab": "496901",
                        "uf_oab": "SP",
                    }
                ],
                "campos_achatados": [("hash", "abcHASH123")],
                "bruto": SAMPLE_ITEM,
            }
        ]
        resultado.resposta = MagicMock(
            status="success",
            message="Sucesso",
            count=1,
            items=[SAMPLE_ITEM],
            pagina=1,
            itens_por_pagina=20,
            headers_rate_limit={"x-ratelimit-limit": "20"},
            url="https://comunicaapi.pje.jus.br/api/v1/comunicacao",
            parametros={"numeroOab": "496901"},
            bruto={"status": "success", "count": 1, "items": [SAMPLE_ITEM]},
        )

        fake_servico = MagicMock()
        fake_servico.consultar_para_teste.return_value = resultado
        fake_servico.cliente.close = MagicMock()

        monkeypatch.setattr(
            "apps.integracoes.views.ServicoConsultaDjen",
            lambda: fake_servico,
        )

        hoje = date.today()
        resposta = client.post(
            reverse("integracoes:consultas_djen"),
            {
                "numero_oab": "496901",
                "uf_oab": "SP",
                "data_inicio": (hoje - timedelta(days=3)).isoformat(),
                "data_fim": hoje.isoformat(),
                "pagina": "1",
                "itens_por_pagina": "20",
                "usar_perfil": "on",
            },
        )
        assert resposta.status_code == 200
        assert b"abcHASH123" in resposta.content
        assert b"destinatarioadvogados" in resposta.content
