from __future__ import annotations

import re
import uuid

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone


class UnidadeFederativa(models.TextChoices):
    AC = "AC", "AC"
    AL = "AL", "AL"
    AP = "AP", "AP"
    AM = "AM", "AM"
    BA = "BA", "BA"
    CE = "CE", "CE"
    DF = "DF", "DF"
    ES = "ES", "ES"
    GO = "GO", "GO"
    MA = "MA", "MA"
    MT = "MT", "MT"
    MS = "MS", "MS"
    MG = "MG", "MG"
    PA = "PA", "PA"
    PB = "PB", "PB"
    PR = "PR", "PR"
    PE = "PE", "PE"
    PI = "PI", "PI"
    RJ = "RJ", "RJ"
    RN = "RN", "RN"
    RS = "RS", "RS"
    RO = "RO", "RO"
    RR = "RR", "RR"
    SC = "SC", "SC"
    SP = "SP", "SP"
    SE = "SE", "SE"
    TO = "TO", "TO"


class TipoInscricaoOab(models.TextChoices):
    PRINCIPAL = "PRINCIPAL", "Principal"
    SUPLEMENTAR = "SUPLEMENTAR", "Suplementar"
    OUTRA = "OUTRA", "Outra"


def normalizar_cpf(valor: str) -> str:
    return re.sub(r"\D", "", valor or "")


def mascarar_cpf(valor: str) -> str:
    digitos = normalizar_cpf(valor)
    if len(digitos) != 11:
        return "***.***.***-**"
    return f"***.***.***-{digitos[-2:]}"


def validar_cpf(valor: str) -> None:
    digitos = normalizar_cpf(valor)
    if not digitos:
        return
    if len(digitos) != 11 or digitos == digitos[0] * 11:
        raise ValidationError("CPF inválido.")

    def _digito(base: str, pesos: list[int]) -> str:
        total = sum(int(n) * p for n, p in zip(base, pesos, strict=True))
        resto = total % 11
        return "0" if resto < 2 else str(11 - resto)

    d1 = _digito(digitos[:9], list(range(10, 1, -1)))
    d2 = _digito(digitos[:10], list(range(11, 1, -1)))
    if digitos[-2:] != f"{d1}{d2}":
        raise ValidationError("CPF inválido.")


def normalizar_numero_oab(valor: str) -> str:
    """
    Normaliza para consulta DJEN.
    Mantém dígitos; sufixos conhecidos (-O, -A, etc.) podem ser gerados na integração.
    """
    bruto = (valor or "").strip().upper().replace(" ", "")
    return bruto


def normalizar_uf(valor: str) -> str:
    return (valor or "").strip().upper()


def validar_numero_oab(valor: str) -> None:
    normalizado = normalizar_numero_oab(valor)
    if not normalizado:
        raise ValidationError("Informe o número da OAB.")
    # Aceita dígitos e sufixo opcional tipo 123456-O (formato visto em tribunais).
    if not re.fullmatch(r"\d{1,8}(-[A-Z])?", normalizado):
        raise ValidationError("OAB inválida. Use números (e sufixo opcional, ex.: 123456-O).")


class Advogado(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    organizacao = models.ForeignKey(
        "organizacoes.Organizacao",
        on_delete=models.PROTECT,
        related_name="advogados",
        db_column="organizacao_id",
        verbose_name="organização",
    )
    usuario = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="advogado",
        db_column="usuario_id",
        verbose_name="usuário",
    )
    nome_completo = models.CharField("nome completo", max_length=255)
    cpf = models.CharField("CPF", max_length=11, blank=True, validators=[validar_cpf])
    email = models.EmailField("e-mail", blank=True)
    telefone = models.CharField("telefone", max_length=20, blank=True)
    # Nome usado em filtros DJEN (nomeAdvogado), quando diferente do cadastral.
    nome_consulta = models.CharField(
        "nome para consulta DJEN",
        max_length=255,
        blank=True,
        help_text="Opcional. Se vazio, usa o nome completo nas consultas por nome.",
    )
    ativo = models.BooleanField("ativo", default=True)
    data_criacao = models.DateTimeField("data de criação", default=timezone.now, editable=False)
    data_atualizacao = models.DateTimeField("data de atualização", auto_now=True)

    class Meta:
        db_table = "advogados"
        verbose_name = "advogado"
        verbose_name_plural = "advogados"
        ordering = ("nome_completo",)
        indexes = [
            models.Index(fields=["organizacao"], name="idx_advogados_organizacao"),
            models.Index(fields=["cpf"], name="idx_advogados_cpf"),
            models.Index(fields=["email"], name="idx_advogados_email"),
        ]

    def __str__(self) -> str:
        return self.nome_completo

    @property
    def cpf_mascarado(self) -> str:
        return mascarar_cpf(self.cpf)

    @property
    def nome_para_api(self) -> str:
        return (self.nome_consulta or self.nome_completo).strip()

    def inscricao_principal(self):
        return self.inscricoes.filter(ativo=True, principal=True).first() or self.inscricoes.filter(
            ativo=True
        ).first()

    def clean(self) -> None:
        super().clean()
        if self.cpf:
            self.cpf = normalizar_cpf(self.cpf)
        if self.email:
            self.email = self.email.strip().lower()
        if self.nome_completo:
            self.nome_completo = re.sub(r"\s+", " ", self.nome_completo).strip()
        if self.nome_consulta:
            self.nome_consulta = re.sub(r"\s+", " ", self.nome_consulta).strip()

    def save(self, *args, **kwargs) -> None:
        if self.cpf:
            self.cpf = normalizar_cpf(self.cpf)
        if self.email:
            self.email = self.email.strip().lower()
        if self.nome_completo:
            self.nome_completo = re.sub(r"\s+", " ", self.nome_completo).strip()
        if self.nome_consulta:
            self.nome_consulta = re.sub(r"\s+", " ", self.nome_consulta).strip()
        super().save(*args, **kwargs)


class InscricaoOab(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    advogado = models.ForeignKey(
        Advogado,
        on_delete=models.CASCADE,
        related_name="inscricoes",
        db_column="advogado_id",
        verbose_name="advogado",
    )
    numero = models.CharField("número", max_length=16, validators=[validar_numero_oab])
    uf = models.CharField("UF", max_length=2, choices=UnidadeFederativa.choices)
    tipo = models.CharField(
        "tipo",
        max_length=20,
        choices=TipoInscricaoOab.choices,
        default=TipoInscricaoOab.PRINCIPAL,
    )
    principal = models.BooleanField("principal", default=False)
    ativo = models.BooleanField("ativo", default=True)
    data_criacao = models.DateTimeField("data de criação", default=timezone.now, editable=False)
    data_atualizacao = models.DateTimeField("data de atualização", auto_now=True)

    class Meta:
        db_table = "inscricoes_oab"
        verbose_name = "inscrição OAB"
        verbose_name_plural = "inscrições OAB"
        ordering = ("-principal", "uf", "numero")
        constraints = [
            models.UniqueConstraint(
                fields=["advogado", "numero", "uf"],
                name="uq_inscricoes_oab_advogado_numero_uf",
            ),
        ]
        indexes = [
            models.Index(fields=["advogado"], name="idx_inscricoes_oab_advogado"),
            models.Index(fields=["numero", "uf"], name="idx_inscricoes_oab_numero_uf"),
        ]

    def __str__(self) -> str:
        return f"OAB/{self.uf} {self.numero}"

    @property
    def oab_formatada(self) -> str:
        return f"OAB/{self.uf} {self.numero}"

    def clean(self) -> None:
        super().clean()
        self.numero = normalizar_numero_oab(self.numero)
        self.uf = normalizar_uf(self.uf)

    def save(self, *args, **kwargs) -> None:
        self.numero = normalizar_numero_oab(self.numero)
        self.uf = normalizar_uf(self.uf)
        super().save(*args, **kwargs)
        if self.principal and self.advogado_id:
            InscricaoOab.objects.filter(advogado_id=self.advogado_id, principal=True).exclude(
                pk=self.pk
            ).update(principal=False)
