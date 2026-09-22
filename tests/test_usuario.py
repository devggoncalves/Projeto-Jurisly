import pytest
from django.contrib.auth import get_user_model
from django.db import IntegrityError

Usuario = get_user_model()


@pytest.mark.django_db
class TestUsuario:
    def test_cria_usuario_por_email_legado(self):
        usuario = Usuario.objects.create_user(
            email="Advogado@Exemplo.COM",
            password="SenhaForte123!",
            nome="Ana",
            sobrenome="Silva",
        )
        assert usuario.login == "advogado@exemplo.com"
        assert usuario.email == "advogado@exemplo.com"
        assert usuario.nome == "Ana"
        assert usuario.check_password("SenhaForte123!")
        assert usuario.ativo is True
        assert usuario.is_active is True

    def test_cria_usuario_somente_login(self):
        usuario = Usuario.objects.create_user(
            login="advogado01",
            password="SenhaForte123!",
        )
        assert usuario.login == "advogado01"
        assert usuario.email is None
        assert usuario.precisa_completar_cadastro is True

    def test_login_obrigatorio(self):
        with pytest.raises(ValueError):
            Usuario.objects.create_user(login="", password="SenhaForte123!")

    def test_login_unico(self):
        Usuario.objects.create_user(login="unico", password="SenhaForte123!", nome="A")
        with pytest.raises(IntegrityError):
            Usuario.objects.create_user(login="unico", password="SenhaForte123!", nome="B")

    def test_senha_nao_fica_em_texto_puro(self):
        usuario = Usuario.objects.create_user(
            login="hashuser",
            password="SenhaForte123!",
            nome="Hash",
        )
        assert usuario.password != "SenhaForte123!"
        assert usuario.password.startswith("pbkdf2_") or usuario.password.startswith("argon2")

    def test_cria_superusuario(self):
        admin = Usuario.objects.create_superuser(
            login="admin",
            email="admin@jurisly.com",
            password="SenhaForte123!",
            nome="Admin",
        )
        assert admin.is_staff is True
        assert admin.is_superuser is True
        assert admin.ativo is True
        assert admin.precisa_completar_cadastro is False
