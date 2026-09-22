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
            name="Cliente",
            fields=[
                (
                    "id",
                    models.UUIDField(
                        default=uuid.uuid4, editable=False, primary_key=True, serialize=False
                    ),
                ),
                ("nome", models.CharField(max_length=255, verbose_name="nome")),
                ("documento", models.CharField(blank=True, max_length=14, verbose_name="CPF/CNPJ")),
                ("email", models.EmailField(blank=True, max_length=254, verbose_name="e-mail")),
                ("telefone", models.CharField(blank=True, max_length=20, verbose_name="telefone")),
                ("observacoes", models.TextField(blank=True, verbose_name="observações")),
                ("ativo", models.BooleanField(default=True, verbose_name="ativo")),
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
                        related_name="clientes",
                        to="advogados.advogado",
                        verbose_name="advogado",
                    ),
                ),
                (
                    "organizacao",
                    models.ForeignKey(
                        db_column="organizacao_id",
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="clientes",
                        to="organizacoes.organizacao",
                        verbose_name="organização",
                    ),
                ),
            ],
            options={
                "verbose_name": "cliente",
                "verbose_name_plural": "clientes",
                "db_table": "clientes",
                "ordering": ("nome",),
            },
        ),
        migrations.CreateModel(
            name="Processo",
            fields=[
                (
                    "id",
                    models.UUIDField(
                        default=uuid.uuid4, editable=False, primary_key=True, serialize=False
                    ),
                ),
                ("numero", models.CharField(max_length=40, verbose_name="número do processo")),
                (
                    "numero_mascarado",
                    models.CharField(blank=True, max_length=60, verbose_name="número com máscara"),
                ),
                ("tribunal", models.CharField(blank=True, max_length=32, verbose_name="tribunal")),
                ("classe", models.CharField(blank=True, max_length=255, verbose_name="classe")),
                ("assunto", models.CharField(blank=True, max_length=255, verbose_name="assunto")),
                ("ativo", models.BooleanField(default=True, verbose_name="ativo")),
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
                        related_name="processos",
                        to="advogados.advogado",
                        verbose_name="advogado",
                    ),
                ),
                (
                    "cliente",
                    models.ForeignKey(
                        db_column="cliente_id",
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="processos",
                        to="clientes.cliente",
                        verbose_name="cliente",
                    ),
                ),
                (
                    "organizacao",
                    models.ForeignKey(
                        db_column="organizacao_id",
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="processos",
                        to="organizacoes.organizacao",
                        verbose_name="organização",
                    ),
                ),
            ],
            options={
                "verbose_name": "processo",
                "verbose_name_plural": "processos",
                "db_table": "processos",
                "ordering": ("-data_criacao",),
            },
        ),
        migrations.AddIndex(
            model_name="cliente",
            index=models.Index(fields=["organizacao"], name="idx_clientes_organizacao"),
        ),
        migrations.AddIndex(
            model_name="cliente",
            index=models.Index(fields=["advogado"], name="idx_clientes_advogado"),
        ),
        migrations.AddIndex(
            model_name="cliente",
            index=models.Index(fields=["documento"], name="idx_clientes_documento"),
        ),
        migrations.AddIndex(
            model_name="processo",
            index=models.Index(fields=["organizacao"], name="idx_processos_organizacao"),
        ),
        migrations.AddIndex(
            model_name="processo",
            index=models.Index(fields=["cliente"], name="idx_processos_cliente"),
        ),
        migrations.AddIndex(
            model_name="processo",
            index=models.Index(fields=["advogado"], name="idx_processos_advogado"),
        ),
        migrations.AddIndex(
            model_name="processo",
            index=models.Index(fields=["numero"], name="idx_processos_numero"),
        ),
        migrations.AddConstraint(
            model_name="processo",
            constraint=models.UniqueConstraint(
                fields=("organizacao", "numero"),
                name="uq_processos_org_numero",
            ),
        ),
    ]
