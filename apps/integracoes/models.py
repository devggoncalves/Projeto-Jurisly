from __future__ import annotations

import uuid

from django.db import models
from django.utils import timezone


class FonteIntegracao(models.TextChoices):
    DJEN = "DJEN", "DJEN / CNJ"


class StatusComunicacaoAdvogado(models.TextChoices):
    PENDENTE = "PENDENTE", "Pendente"
    CONFIRMADA = "CONFIRMADA", "Confirmada"
    REJEITADA = "REJEITADA", "Rejeitada"


class StatusSincronizacao(models.TextChoices):
    EM_ANDAMENTO = "EM_ANDAMENTO", "Em andamento"
    SUCESSO = "SUCESSO", "Sucesso"
    ERRO = "ERRO", "Erro"
    PARCIAL = "PARCIAL", "Parcial"


class ComunicacaoJudicial(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    organizacao = models.ForeignKey(
        "organizacoes.Organizacao",
        on_delete=models.PROTECT,
        related_name="comunicacoes_judiciais",
        db_column="organizacao_id",
        verbose_name="organização",
    )
    fonte = models.CharField(
        "fonte",
        max_length=20,
        choices=FonteIntegracao.choices,
        default=FonteIntegracao.DJEN,
    )
    identificador_externo = models.CharField("identificador externo", max_length=128)
    hash = models.CharField("hash", max_length=128, blank=True)
    tipo_comunicacao = models.CharField("tipo de comunicação", max_length=80, blank=True)
    tipo_documento = models.CharField("tipo de documento", max_length=80, blank=True)
    tribunal = models.CharField("tribunal", max_length=32, blank=True)
    orgao = models.CharField("órgão", max_length=255, blank=True)
    id_orgao = models.CharField("id do órgão", max_length=64, blank=True)
    numero_processo = models.CharField("número do processo", max_length=40, blank=True)
    numero_processo_mascarado = models.CharField(
        "número do processo (máscara)", max_length=60, blank=True
    )
    numero_comunicacao = models.CharField("número da comunicação", max_length=64, blank=True)
    meio = models.CharField("meio", max_length=120, blank=True)
    link = models.URLField("link", max_length=500, blank=True)
    nome_classe = models.CharField("classe", max_length=255, blank=True)
    codigo_classe = models.CharField("código da classe", max_length=32, blank=True)
    texto = models.TextField("texto", blank=True)
    data_disponibilizacao = models.DateField("data de disponibilização", null=True, blank=True)
    data_cancelamento = models.DateField("data de cancelamento", null=True, blank=True)
    motivo_cancelamento = models.CharField("motivo do cancelamento", max_length=255, blank=True)
    ativo_origem = models.BooleanField("ativo na origem", null=True, blank=True)
    status_origem = models.CharField("status na origem", max_length=80, blank=True)
    dados_originais = models.JSONField("dados originais", default=dict, blank=True)
    data_criacao = models.DateTimeField("data de criação", default=timezone.now, editable=False)
    data_atualizacao = models.DateTimeField("data de atualização", auto_now=True)

    class Meta:
        db_table = "comunicacoes_judiciais"
        verbose_name = "comunicação judicial"
        verbose_name_plural = "comunicações judiciais"
        ordering = ("-data_disponibilizacao", "-data_criacao")
        constraints = [
            models.UniqueConstraint(
                fields=["organizacao", "fonte", "identificador_externo"],
                name="uq_comunicacoes_org_fonte_identificador",
            ),
        ]
        indexes = [
            models.Index(fields=["organizacao"], name="idx_comunicacoes_organizacao"),
            models.Index(fields=["hash"], name="idx_comunicacoes_hash"),
            models.Index(fields=["numero_processo"], name="idx_comunicacoes_processo"),
            models.Index(
                fields=["data_disponibilizacao"],
                name="idx_comunicacoes_data_disp",
            ),
        ]

    def __str__(self) -> str:
        return f"{self.fonte}:{self.identificador_externo}"


class ComunicacaoAdvogado(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    organizacao = models.ForeignKey(
        "organizacoes.Organizacao",
        on_delete=models.PROTECT,
        related_name="comunicacoes_advogados",
        db_column="organizacao_id",
        verbose_name="organização",
    )
    comunicacao = models.ForeignKey(
        ComunicacaoJudicial,
        on_delete=models.CASCADE,
        related_name="vinculos_advogado",
        db_column="comunicacao_id",
        verbose_name="comunicação",
    )
    advogado = models.ForeignKey(
        "advogados.Advogado",
        on_delete=models.CASCADE,
        related_name="comunicacoes",
        db_column="advogado_id",
        verbose_name="advogado",
    )
    inscricao_oab = models.ForeignKey(
        "advogados.InscricaoOab",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="comunicacoes",
        db_column="inscricao_oab_id",
        verbose_name="inscrição OAB",
    )
    status = models.CharField(
        "status",
        max_length=20,
        choices=StatusComunicacaoAdvogado.choices,
        default=StatusComunicacaoAdvogado.PENDENTE,
    )
    visualizado = models.BooleanField("visualizado", default=False)
    visualizado_em = models.DateTimeField("visualizado em", null=True, blank=True)
    nome_advogado_origem = models.CharField("nome do advogado na origem", max_length=255, blank=True)
    numero_oab_origem = models.CharField("OAB na origem", max_length=32, blank=True)
    uf_oab_origem = models.CharField("UF OAB na origem", max_length=2, blank=True)
    data_criacao = models.DateTimeField("data de criação", default=timezone.now, editable=False)
    data_atualizacao = models.DateTimeField("data de atualização", auto_now=True)

    class Meta:
        db_table = "comunicacoes_advogados"
        verbose_name = "comunicação × advogado"
        verbose_name_plural = "comunicações × advogados"
        ordering = ("-data_criacao",)
        constraints = [
            models.UniqueConstraint(
                fields=["comunicacao", "advogado"],
                name="uq_comunicacao_advogado",
            ),
        ]
        indexes = [
            models.Index(fields=["organizacao"], name="idx_com_adv_organizacao"),
            models.Index(fields=["status"], name="idx_com_adv_status"),
            models.Index(fields=["visualizado"], name="idx_com_adv_visualizado"),
        ]

    def __str__(self) -> str:
        return f"{self.comunicacao_id} → {self.advogado_id} ({self.status})"


class SincronizacaoIntegracao(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    organizacao = models.ForeignKey(
        "organizacoes.Organizacao",
        on_delete=models.PROTECT,
        related_name="sincronizacoes",
        db_column="organizacao_id",
        verbose_name="organização",
    )
    fonte = models.CharField(
        "fonte",
        max_length=20,
        choices=FonteIntegracao.choices,
        default=FonteIntegracao.DJEN,
    )
    status = models.CharField(
        "status",
        max_length=20,
        choices=StatusSincronizacao.choices,
        default=StatusSincronizacao.EM_ANDAMENTO,
    )
    parametros = models.JSONField("parâmetros", default=dict, blank=True)
    total_encontrado = models.PositiveIntegerField("total encontrado", default=0)
    total_novos = models.PositiveIntegerField("total novos", default=0)
    total_atualizados = models.PositiveIntegerField("total atualizados", default=0)
    total_erros = models.PositiveIntegerField("total erros", default=0)
    mensagem = models.TextField("mensagem", blank=True)
    detalhes = models.JSONField("detalhes", default=dict, blank=True)
    iniciado_em = models.DateTimeField("iniciado em", default=timezone.now)
    finalizado_em = models.DateTimeField("finalizado em", null=True, blank=True)
    data_criacao = models.DateTimeField("data de criação", default=timezone.now, editable=False)

    class Meta:
        db_table = "sincronizacoes_integracao"
        verbose_name = "sincronização de integração"
        verbose_name_plural = "sincronizações de integração"
        ordering = ("-iniciado_em",)
        indexes = [
            models.Index(fields=["organizacao", "fonte"], name="idx_sync_org_fonte"),
            models.Index(fields=["status"], name="idx_sync_status"),
        ]

    def __str__(self) -> str:
        return f"{self.fonte} {self.status} @ {self.iniciado_em:%Y-%m-%d %H:%M}"
