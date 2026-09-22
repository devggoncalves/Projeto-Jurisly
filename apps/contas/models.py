from __future__ import annotations

import re
import uuid
from typing import Any

from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from django.db import models
from django.utils import timezone

from apps.contas.managers import GerenciadorUsuario, normalizar_login


class Usuario(AbstractBaseUser, PermissionsMixin):
    """Usuário autenticável do Jurisly (login + senha; e-mail no onboarding)."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    login = models.CharField("login", max_length=150, unique=True, db_index=True)
    email = models.EmailField("e-mail", unique=True, db_index=True, blank=True, null=True)
    nome = models.CharField("nome", max_length=150, blank=True, default="")
    sobrenome = models.CharField("sobrenome", max_length=150, blank=True)
    ativo = models.BooleanField("ativo", default=True)
    is_staff = models.BooleanField("acesso ao admin", default=False)
    is_superuser = models.BooleanField("superusuário", default=False)
    data_criacao = models.DateTimeField("data de criação", default=timezone.now, editable=False)
    data_atualizacao = models.DateTimeField("data de atualização", auto_now=True)
    ultimo_acesso = models.DateTimeField("último acesso", blank=True, null=True)

    objects = GerenciadorUsuario()

    USERNAME_FIELD = "login"
    REQUIRED_FIELDS: list[str] = []

    class Meta:
        db_table = "usuarios"
        verbose_name = "usuário"
        verbose_name_plural = "usuários"
        ordering = ("login",)

    def __str__(self) -> str:
        return self.login

    @property
    def is_active(self) -> bool:
        return self.ativo

    @is_active.setter
    def is_active(self, value: bool) -> None:
        self.ativo = value

    def get_full_name(self) -> str:
        completo = f"{self.nome} {self.sobrenome}".strip()
        return completo or self.login

    def get_short_name(self) -> str:
        return self.nome or self.login

    def registrar_acesso(self, *, salvar: bool = True) -> None:
        self.ultimo_acesso = timezone.now()
        if salvar:
            self.save(update_fields=["ultimo_acesso", "data_atualizacao"])

    @property
    def precisa_completar_cadastro(self) -> bool:
        """Admin/staff isentos; demais precisam de e-mail + OAB ativa."""
        if self.is_staff or self.is_superuser:
            return False
        if not self.email:
            return True
        advogado = getattr(self, "advogado", None)
        if advogado is None:
            return True
        return not advogado.inscricoes.filter(ativo=True).exists()

    def save(self, *args: Any, **kwargs: Any) -> None:
        if self.login:
            self.login = normalizar_login(self.login)
        if self.email:
            self.email = self.__class__.objects.normalizar_email(self.email)
        else:
            self.email = None
        if self.nome:
            self.nome = re.sub(r"\s+", " ", self.nome).strip()
        super().save(*args, **kwargs)
