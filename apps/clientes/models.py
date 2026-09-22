from __future__ import annotations

import re
import uuid

from django.db import models
from django.utils import timezone


def normalizar_documento(valor: str) -> str:
    return re.sub(r"\D", "", valor or "")


class Cliente(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    organizacao = models.ForeignKey(
        "organizacoes.Organizacao",
        on_delete=models.PROTECT,
        related_name="clientes",
        db_column="organizacao_id",
        verbose_name="organização",
    )
    advogado = models.ForeignKey(
        "advogados.Advogado",
        on_delete=models.CASCADE,
        related_name="clientes",
        db_column="advogado_id",
        verbose_name="advogado",
    )
    nome = models.CharField("nome", max_length=255)
    documento = models.CharField("CPF/CNPJ", max_length=14, blank=True)
    email = models.EmailField("e-mail", blank=True)
    telefone = models.CharField("telefone", max_length=20, blank=True)
    observacoes = models.TextField("observações", blank=True)
    ativo = models.BooleanField("ativo", default=True)
    data_criacao = models.DateTimeField("data de criação", default=timezone.now, editable=False)
    data_atualizacao = models.DateTimeField("data de atualização", auto_now=True)

    class Meta:
        db_table = "clientes"
        verbose_name = "cliente"
        verbose_name_plural = "clientes"
        ordering = ("nome",)
        indexes = [
            models.Index(fields=["organizacao"], name="idx_clientes_organizacao"),
            models.Index(fields=["advogado"], name="idx_clientes_advogado"),
            models.Index(fields=["documento"], name="idx_clientes_documento"),
        ]

    def __str__(self) -> str:
        return self.nome

    def save(self, *args, **kwargs):
        if self.documento:
            self.documento = normalizar_documento(self.documento)
        if self.nome:
            self.nome = re.sub(r"\s+", " ", self.nome).strip()
        if self.email:
            self.email = self.email.strip().lower()
        super().save(*args, **kwargs)


class Processo(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    organizacao = models.ForeignKey(
        "organizacoes.Organizacao",
        on_delete=models.PROTECT,
        related_name="processos",
        db_column="organizacao_id",
        verbose_name="organização",
    )
    cliente = models.ForeignKey(
        Cliente,
        on_delete=models.CASCADE,
        related_name="processos",
        db_column="cliente_id",
        verbose_name="cliente",
    )
    advogado = models.ForeignKey(
        "advogados.Advogado",
        on_delete=models.CASCADE,
        related_name="processos",
        db_column="advogado_id",
        verbose_name="advogado",
    )
    numero = models.CharField("número do processo", max_length=40)
    numero_mascarado = models.CharField("número com máscara", max_length=60, blank=True)
    tribunal = models.CharField("tribunal", max_length=32, blank=True)
    classe = models.CharField("classe", max_length=255, blank=True)
    assunto = models.CharField("assunto", max_length=255, blank=True)
    ativo = models.BooleanField("ativo", default=True)
    data_criacao = models.DateTimeField("data de criação", default=timezone.now, editable=False)
    data_atualizacao = models.DateTimeField("data de atualização", auto_now=True)

    class Meta:
        db_table = "processos"
        verbose_name = "processo"
        verbose_name_plural = "processos"
        ordering = ("-data_criacao",)
        constraints = [
            models.UniqueConstraint(
                fields=["organizacao", "numero"],
                name="uq_processos_org_numero",
            ),
        ]
        indexes = [
            models.Index(fields=["organizacao"], name="idx_processos_organizacao"),
            models.Index(fields=["cliente"], name="idx_processos_cliente"),
            models.Index(fields=["advogado"], name="idx_processos_advogado"),
            models.Index(fields=["numero"], name="idx_processos_numero"),
        ]

    def __str__(self) -> str:
        return self.numero_mascarado or self.numero

    def save(self, *args, **kwargs):
        self.numero = re.sub(r"\D", "", self.numero or "")
        super().save(*args, **kwargs)
