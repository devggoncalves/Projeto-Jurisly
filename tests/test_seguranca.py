import pytest
from django.contrib.auth import get_user_model
from django.urls import reverse

Usuario = get_user_model()


@pytest.mark.django_db
class TestSeguranca:
    def test_dashboard_exige_autenticacao(self, client):
        resposta = client.get(reverse("core:dashboard"))
        assert resposta.status_code == 302
        assert reverse("contas:login") in resposta.url
        assert "next=" in resposta.url

    def test_csrf_ativo_no_login(self, client):
        client.handler.enforce_csrf_checks = True
        resposta = client.post(
            reverse("contas:login"),
            {"username": "a@b.com", "password": "x"},
        )
        assert resposta.status_code == 403

    def test_logout_somente_post(self, client):
        usuario = Usuario.objects.create_user(
            email="csrf@jurisly.com",
            password="SenhaForte123!",
            nome="Csrf",
        )
        client.force_login(usuario)
        resposta = client.get(reverse("contas:logout"))
        assert resposta.status_code == 405
