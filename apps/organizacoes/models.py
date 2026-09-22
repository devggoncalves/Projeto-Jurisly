from __future__ import annotations

import re
import uuid

from django.conf import settings
from django.db import models
from django.utils import timezone
from django.utils.text import slugify


class PerfilOrganizacao(models.TextChoices):
    PROPRIETARIO = "PROPRIETARIO", "Proprietário"
    ADMINISTRADOR = "ADMINISTRADOR", "Administrador"
    ADVOGADO = "ADVOGADO", "Advogado"
    ASSISTENTE = "ASSISTENTE", "Assistente"
    VISUALIZADOR = "VISUALIZADOR", "Visualizador"


class Organizacao(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    nome = models.CharField("nome", max_length=255)
    slug = models.SlugField("slug", max_length=255, unique=True)
    ativo = models.BooleanField("ativo", default=True)
    data_criacao = models.DateTimeField("data de criação", default=timezone.now, editable=False)
    data_atualizacao = models.DateTimeField("data de atualização", auto_now=True)

    class Meta:
        db_table = "organizacoes"
        verbose_name = "organização"
        verbose_name_plural = "organizações"
        ordering = ("nome",)
        # unique=True em slug já garante unicidade e índice no PostgreSQL.

    def __str__(self) -> str:
        return self.nome

    def save(self, *args, **kwargs) -> None:
        if not self.slug:
            self.slug = self._gerar_slug(self.nome)
        else:
            self.slug = slugify(self.slug) or self.slug
        super().save(*args, **kwargs)

    @staticmethod
    def _gerar_slug(nome: str) -> str:
        base = slugify(nome) or "organizacao"
        base = re.sub(r"-+", "-", base).strip("-")
        candidato = base
        contador = 2
        while Organizacao.objects.filter(slug=candidato).exists():
            candidato = f"{base}-{contador}"
            contador += 1
        return candidato


class OrganizacaoUsuario(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    organizacao = models.ForeignKey(
        Organizacao,
        on_delete=models.PROTECT,
        related_name="membros",
        db_column="organizacao_id",
        verbose_name="organização",
    )
    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="vinculos_organizacao",
        db_column="usuario_id",
        verbose_name="usuário",
    )
    perfil = models.CharField(
        "perfil",
        max_length=32,
        choices=PerfilOrganizacao.choices,
        default=PerfilOrganizacao.ADVOGADO,
    )
    ativo = models.BooleanField("ativo", default=True)
    data_criacao = models.DateTimeField("data de criação", default=timezone.now, editable=False)
    data_atualizacao = models.DateTimeField("data de atualização", auto_now=True)

    class Meta:
        db_table = "organizacoes_usuarios"
        verbose_name = "usuário da organização"
        verbose_name_plural = "usuários da organização"
        constraints = [
            models.UniqueConstraint(
                fields=["organizacao", "usuario"],
                name="uq_organizacoes_usuarios",
            ),
        ]
        indexes = [
            models.Index(fields=["organizacao"], name="idx_org_usr_organizacao"),
            models.Index(fields=["usuario"], name="idx_org_usr_usuario"),
        ]

    def __str__(self) -> str:
        return f"{self.usuario} @ {self.organizacao} ({self.perfil})"
