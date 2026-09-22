import pytest
from django.urls import reverse


@pytest.mark.django_db
def test_health_ok(client):
    resposta = client.get(reverse("core:health"))
    assert resposta.status_code == 200
    assert resposta.json() == {"status": "ok"}
