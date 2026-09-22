from __future__ import annotations

import uuid

from django.conf import settings
from django.db import models
from django.utils import timezone


class AcaoAuditoria(models.TextChoices):
    LOGIN_SUCESSO = "LOGIN_SUCESSO", "Login com sucesso"
    LOGIN_FALHA = "LOGIN_FALHA", "Falha de login"
    LOGOUT = "LOGOUT", "Logout"


class LogAuditoria(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    organizacao = models.ForeignKey(
        "organizacoes.Organizacao",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="logs_auditoria",
        db_column="organizacao_id",
        verbose_name="organização",
    )
    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="logs_auditoria",
        db_column="usuario_id",
        verbose_name="usuário",
    )
    acao = models.CharField("ação", max_length=64, choices=AcaoAuditoria.choices)
    tipo_entidade = models.CharField("tipo da entidade", max_length=64, blank=True)
    entidade_id = models.UUIDField("id da entidade", null=True, blank=True)
    metadados = models.JSONField("metadados", default=dict, blank=True)
    endereco_ip = models.GenericIPAddressField("endereço IP", null=True, blank=True)
    agente_usuario = models.TextField("agente do usuário", blank=True)
    data_criacao = models.DateTimeField("data de criação", default=timezone.now, editable=False)

    class Meta:
        db_table = "logs_auditoria"
        verbose_name = "log de auditoria"
        verbose_name_plural = "logs de auditoria"
        ordering = ("-data_criacao",)
        indexes = [
            models.Index(fields=["organizacao"], name="idx_logs_aud_organizacao"),
            models.Index(fields=["usuario"], name="idx_logs_aud_usuario"),
            models.Index(fields=["data_criacao"], name="idx_logs_aud_data_criacao"),
        ]

    def __str__(self) -> str:
        return f"{self.acao} @ {self.data_criacao:%Y-%m-%d %H:%M:%S}"
