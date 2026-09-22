from __future__ import annotations

from typing import Any

from django.contrib.auth.base_user import BaseUserManager
from django.utils import timezone


def normalizar_login(valor: str) -> str:
    return (valor or "").strip().lower()


class GerenciadorUsuario(BaseUserManager):
    """Gerenciador do modelo Usuario com login + senha."""

    use_in_migrations = True

    def normalizar_email(self, email: str) -> str:
        return super().normalize_email(email).strip().lower()

    def _criar_usuario(
        self,
        login: str,
        senha: str | None = None,
        **extra_fields: Any,
    ):
        if not login:
            raise ValueError("O login é obrigatório.")

        login = normalizar_login(login)
        email = extra_fields.pop("email", None)
        if email:
            email = self.normalizar_email(email)
        else:
            email = None

        usuario = self.model(login=login, email=email, **extra_fields)
        usuario.set_password(senha)
        usuario.save(using=self._db)
        return usuario

    def create_user(self, login: str | None = None, password: str | None = None, **extra_fields: Any):
        """
        Aceita `login=` ou, por compatibilidade, `email=` como identificador
        (nesse caso login = e-mail).
        """
        email = extra_fields.get("email")
        if login is None and email:
            login = email
        if login is None:
            raise ValueError("O login é obrigatório.")

        extra_fields.setdefault("ativo", True)
        extra_fields.setdefault("is_staff", False)
        extra_fields.setdefault("is_superuser", False)
        extra_fields.setdefault("nome", extra_fields.pop("nome", "") or "")
        return self._criar_usuario(login, password, **extra_fields)

    def create_superuser(self, login: str | None = None, password: str | None = None, **extra_fields: Any):
        email = extra_fields.get("email")
        if login is None and email:
            login = email
        if login is None:
            raise ValueError("O login é obrigatório.")

        extra_fields.setdefault("ativo", True)
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("nome", extra_fields.pop("nome", "Administrador"))
        if not email:
            # Superuser precisa de e-mail para recuperação/admin
            if "@" in str(login):
                extra_fields["email"] = login
            else:
                raise ValueError("Superusuário precisa de e-mail.")

        if extra_fields.get("is_staff") is not True:
            raise ValueError("Superusuário precisa ter is_staff=True.")
        if extra_fields.get("is_superuser") is not True:
            raise ValueError("Superusuário precisa ter is_superuser=True.")
        if not password:
            raise ValueError("Superusuário precisa de senha.")

        return self._criar_usuario(login, password, **extra_fields)

    def atualizar_ultimo_acesso(self, usuario) -> None:
        usuario.ultimo_acesso = timezone.now()
        usuario.save(update_fields=["ultimo_acesso", "data_atualizacao"])
