# Generated manually for Prompt 02 DJEN

import django.db.models.deletion
import django.utils.timezone
import uuid
from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        ("advogados", "0003_advogado_inscricao_oab"),
        ("organizacoes", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="ComunicacaoJudicial",
            fields=[
                (
                    "id",
                    models.UUIDField(
                        default=uuid.uuid4, editable=False, primary_key=True, serialize=False
                    ),
                ),
                (
                    "fonte",
                    models.CharField(
                        choices=[("DJEN", "DJEN / CNJ")],
                        default="DJEN",
                        max_length=20,
                        verbose_name="fonte",
                    ),
                ),
                (
                    "identificador_externo",
                    models.CharField(max_length=128, verbose_name="identificador externo"),
                ),
                ("hash", models.CharField(blank=True, max_length=128, verbose_name="hash")),
                (
                    "tipo_comunicacao",
                    models.CharField(blank=True, max_length=80, verbose_name="tipo de comunicação"),
                ),
                (
                    "tipo_documento",
                    models.CharField(blank=True, max_length=80, verbose_name="tipo de documento"),
                ),
                ("tribunal", models.CharField(blank=True, max_length=32, verbose_name="tribunal")),
                ("orgao", models.CharField(blank=True, max_length=255, verbose_name="órgão")),
                (
                    "id_orgao",
                    models.CharField(blank=True, max_length=64, verbose_name="id do órgão"),
                ),
                (
                    "numero_processo",
                    models.CharField(blank=True, max_length=40, verbose_name="número do processo"),
                ),
                (
                    "numero_processo_mascarado",
                    models.CharField(
                        blank=True, max_length=60, verbose_name="número do processo (máscara)"
                    ),
                ),
                (
                    "numero_comunicacao",
                    models.CharField(
                        blank=True, max_length=64, verbose_name="número da comunicação"
                    ),
                ),
                ("meio", models.CharField(blank=True, max_length=120, verbose_name="meio")),
                ("link", models.URLField(blank=True, max_length=500, verbose_name="link")),
                ("nome_classe", models.CharField(blank=True, max_length=255, verbose_name="classe")),
                (
                    "codigo_classe",
                    models.CharField(blank=True, max_length=32, verbose_name="código da classe"),
                ),
                ("texto", models.TextField(blank=True, verbose_name="texto")),
                (
                    "data_disponibilizacao",
                    models.DateField(blank=True, null=True, verbose_name="data de disponibilização"),
                ),
                (
                    "data_cancelamento",
                    models.DateField(blank=True, null=True, verbose_name="data de cancelamento"),
                ),
                (
                    "motivo_cancelamento",
                    models.CharField(
                        blank=True, max_length=255, verbose_name="motivo do cancelamento"
                    ),
                ),
                (
                    "ativo_origem",
                    models.BooleanField(blank=True, null=True, verbose_name="ativo na origem"),
                ),
                (
                    "status_origem",
                    models.CharField(blank=True, max_length=80, verbose_name="status na origem"),
                ),
                (
                    "dados_originais",
                    models.JSONField(blank=True, default=dict, verbose_name="dados originais"),
                ),
                (
                    "data_criacao",
                    models.DateTimeField(
                        default=django.utils.timezone.now,
                        editable=False,
                        verbose_name="data de criação",
                    ),
                ),
                (
                    "data_atualizacao",
                    models.DateTimeField(auto_now=True, verbose_name="data de atualização"),
                ),
                (
                    "organizacao",
                    models.ForeignKey(
                        db_column="organizacao_id",
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="comunicacoes_judiciais",
                        to="organizacoes.organizacao",
                        verbose_name="organização",
                    ),
                ),
            ],
            options={
                "verbose_name": "comunicação judicial",
                "verbose_name_plural": "comunicações judiciais",
                "db_table": "comunicacoes_judiciais",
                "ordering": ("-data_disponibilizacao", "-data_criacao"),
            },
        ),
        migrations.CreateModel(
            name="SincronizacaoIntegracao",
            fields=[
                (
                    "id",
                    models.UUIDField(
                        default=uuid.uuid4, editable=False, primary_key=True, serialize=False
                    ),
                ),
                (
                    "fonte",
                    models.CharField(
                        choices=[("DJEN", "DJEN / CNJ")],
                        default="DJEN",
                        max_length=20,
                        verbose_name="fonte",
                    ),
                ),
                (
                    "status",
                    models.CharField(
                        choices=[
                            ("EM_ANDAMENTO", "Em andamento"),
                            ("SUCESSO", "Sucesso"),
                            ("ERRO", "Erro"),
                            ("PARCIAL", "Parcial"),
                        ],
                        default="EM_ANDAMENTO",
                        max_length=20,
                        verbose_name="status",
                    ),
                ),
                (
                    "parametros",
                    models.JSONField(blank=True, default=dict, verbose_name="parâmetros"),
                ),
                (
                    "total_encontrado",
                    models.PositiveIntegerField(default=0, verbose_name="total encontrado"),
                ),
                (
                    "total_novos",
                    models.PositiveIntegerField(default=0, verbose_name="total novos"),
                ),
                (
                    "total_atualizados",
                    models.PositiveIntegerField(default=0, verbose_name="total atualizados"),
                ),
                (
                    "total_erros",
                    models.PositiveIntegerField(default=0, verbose_name="total erros"),
                ),
                ("mensagem", models.TextField(blank=True, verbose_name="mensagem")),
                ("detalhes", models.JSONField(blank=True, default=dict, verbose_name="detalhes")),
                (
                    "iniciado_em",
                    models.DateTimeField(
                        default=django.utils.timezone.now, verbose_name="iniciado em"
                    ),
                ),
                (
                    "finalizado_em",
                    models.DateTimeField(blank=True, null=True, verbose_name="finalizado em"),
                ),
                (
                    "data_criacao",
                    models.DateTimeField(
                        default=django.utils.timezone.now,
                        editable=False,
                        verbose_name="data de criação",
                    ),
                ),
                (
                    "organizacao",
                    models.ForeignKey(
                        db_column="organizacao_id",
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="sincronizacoes",
                        to="organizacoes.organizacao",
                        verbose_name="organização",
                    ),
                ),
            ],
            options={
                "verbose_name": "sincronização de integração",
                "verbose_name_plural": "sincronizações de integração",
                "db_table": "sincronizacoes_integracao",
                "ordering": ("-iniciado_em",),
            },
        ),
        migrations.CreateModel(
            name="ComunicacaoAdvogado",
            fields=[
                (
                    "id",
                    models.UUIDField(
                        default=uuid.uuid4, editable=False, primary_key=True, serialize=False
                    ),
                ),
                (
                    "status",
                    models.CharField(
                        choices=[
                            ("PENDENTE", "Pendente"),
                            ("CONFIRMADA", "Confirmada"),
                            ("REJEITADA", "Rejeitada"),
                        ],
                        default="PENDENTE",
                        max_length=20,
                        verbose_name="status",
                    ),
                ),
                (
                    "nome_advogado_origem",
                    models.CharField(
                        blank=True, max_length=255, verbose_name="nome do advogado na origem"
                    ),
                ),
                (
                    "numero_oab_origem",
                    models.CharField(blank=True, max_length=32, verbose_name="OAB na origem"),
                ),
                (
                    "uf_oab_origem",
                    models.CharField(blank=True, max_length=2, verbose_name="UF OAB na origem"),
                ),
                (
                    "data_criacao",
                    models.DateTimeField(
                        default=django.utils.timezone.now,
                        editable=False,
                        verbose_name="data de criação",
                    ),
                ),
                (
                    "data_atualizacao",
                    models.DateTimeField(auto_now=True, verbose_name="data de atualização"),
                ),
                (
                    "advogado",
                    models.ForeignKey(
                        db_column="advogado_id",
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="comunicacoes",
                        to="advogados.advogado",
                        verbose_name="advogado",
                    ),
                ),
                (
                    "comunicacao",
                    models.ForeignKey(
                        db_column="comunicacao_id",
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="vinculos_advogado",
                        to="integracoes.comunicacaojudicial",
                        verbose_name="comunicação",
                    ),
                ),
                (
                    "inscricao_oab",
                    models.ForeignKey(
                        blank=True,
                        db_column="inscricao_oab_id",
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="comunicacoes",
                        to="advogados.inscricaooab",
                        verbose_name="inscrição OAB",
                    ),
                ),
                (
                    "organizacao",
                    models.ForeignKey(
                        db_column="organizacao_id",
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="comunicacoes_advogados",
                        to="organizacoes.organizacao",
                        verbose_name="organização",
                    ),
                ),
            ],
            options={
                "verbose_name": "comunicação × advogado",
                "verbose_name_plural": "comunicações × advogados",
                "db_table": "comunicacoes_advogados",
                "ordering": ("-data_criacao",),
            },
        ),
        migrations.AddIndex(
            model_name="comunicacaojudicial",
            index=models.Index(fields=["organizacao"], name="idx_comunicacoes_organizacao"),
        ),
        migrations.AddIndex(
            model_name="comunicacaojudicial",
            index=models.Index(fields=["hash"], name="idx_comunicacoes_hash"),
        ),
        migrations.AddIndex(
            model_name="comunicacaojudicial",
            index=models.Index(fields=["numero_processo"], name="idx_comunicacoes_processo"),
        ),
        migrations.AddIndex(
            model_name="comunicacaojudicial",
            index=models.Index(
                fields=["data_disponibilizacao"], name="idx_comunicacoes_data_disp"
            ),
        ),
        migrations.AddConstraint(
            model_name="comunicacaojudicial",
            constraint=models.UniqueConstraint(
                fields=("organizacao", "fonte", "identificador_externo"),
                name="uq_comunicacoes_org_fonte_identificador",
            ),
        ),
        migrations.AddIndex(
            model_name="sincronizacaointegracao",
            index=models.Index(fields=["organizacao", "fonte"], name="idx_sync_org_fonte"),
        ),
        migrations.AddIndex(
            model_name="sincronizacaointegracao",
            index=models.Index(fields=["status"], name="idx_sync_status"),
        ),
        migrations.AddIndex(
            model_name="comunicacaoadvogado",
            index=models.Index(fields=["organizacao"], name="idx_com_adv_organizacao"),
        ),
        migrations.AddIndex(
            model_name="comunicacaoadvogado",
            index=models.Index(fields=["status"], name="idx_com_adv_status"),
        ),
        migrations.AddConstraint(
            model_name="comunicacaoadvogado",
            constraint=models.UniqueConstraint(
                fields=("comunicacao", "advogado"),
                name="uq_comunicacao_advogado",
            ),
        ),
    ]
