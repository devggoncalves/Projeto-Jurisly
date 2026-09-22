import django.db.models.deletion
import django.utils.timezone
import uuid
from django.conf import settings
from django.db import migrations, models

import apps.advogados.models


def migrar_nome_e_oab(apps, schema_editor):
    Advogado = apps.get_model("advogados", "Advogado")
    InscricaoOab = apps.get_model("advogados", "InscricaoOab")

    for advogado in Advogado.objects.all():
        nome = (getattr(advogado, "nome", "") or "").strip()
        sobrenome = (getattr(advogado, "sobrenome", "") or "").strip()
        nome_completo = f"{nome} {sobrenome}".strip() or (advogado.email or "Advogado")
        Advogado.objects.filter(pk=advogado.pk).update(nome_completo=nome_completo)

        numero = (getattr(advogado, "numero_oab", "") or "").strip()
        uf = (getattr(advogado, "uf_oab", "") or "").strip().upper()
        if numero and uf:
            InscricaoOab.objects.get_or_create(
                advogado_id=advogado.pk,
                numero=numero,
                uf=uf,
                defaults={
                    "tipo": "PRINCIPAL",
                    "principal": True,
                    "ativo": True,
                },
            )


def reverter_nome_e_oab(apps, schema_editor):
    Advogado = apps.get_model("advogados", "Advogado")
    InscricaoOab = apps.get_model("advogados", "InscricaoOab")

    for advogado in Advogado.objects.all():
        partes = (advogado.nome_completo or "").split(" ", 1)
        nome = partes[0] if partes else ""
        sobrenome = partes[1] if len(partes) > 1 else ""
        inscricao = (
            InscricaoOab.objects.filter(advogado_id=advogado.pk, principal=True).first()
            or InscricaoOab.objects.filter(advogado_id=advogado.pk).first()
        )
        updates = {"nome": nome[:150], "sobrenome": sobrenome[:150]}
        if inscricao:
            updates["numero_oab"] = inscricao.numero
            updates["uf_oab"] = inscricao.uf
        Advogado.objects.filter(pk=advogado.pk).update(**updates)


class Migration(migrations.Migration):
    dependencies = [
        ("advogados", "0002_advogado_usuario_onetoone"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AddField(
            model_name="advogado",
            name="nome_completo",
            field=models.CharField(default="", max_length=255, verbose_name="nome completo"),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name="advogado",
            name="nome_consulta",
            field=models.CharField(
                blank=True,
                help_text="Opcional. Se vazio, usa o nome completo nas consultas por nome.",
                max_length=255,
                verbose_name="nome para consulta DJEN",
            ),
        ),
        migrations.CreateModel(
            name="InscricaoOab",
            fields=[
                (
                    "id",
                    models.UUIDField(
                        default=uuid.uuid4, editable=False, primary_key=True, serialize=False
                    ),
                ),
                (
                    "numero",
                    models.CharField(
                        max_length=16,
                        validators=[apps.advogados.models.validar_numero_oab],
                        verbose_name="número",
                    ),
                ),
                (
                    "uf",
                    models.CharField(
                        choices=[
                            ("AC", "AC"),
                            ("AL", "AL"),
                            ("AP", "AP"),
                            ("AM", "AM"),
                            ("BA", "BA"),
                            ("CE", "CE"),
                            ("DF", "DF"),
                            ("ES", "ES"),
                            ("GO", "GO"),
                            ("MA", "MA"),
                            ("MT", "MT"),
                            ("MS", "MS"),
                            ("MG", "MG"),
                            ("PA", "PA"),
                            ("PB", "PB"),
                            ("PR", "PR"),
                            ("PE", "PE"),
                            ("PI", "PI"),
                            ("RJ", "RJ"),
                            ("RN", "RN"),
                            ("RS", "RS"),
                            ("RO", "RO"),
                            ("RR", "RR"),
                            ("SC", "SC"),
                            ("SP", "SP"),
                            ("SE", "SE"),
                            ("TO", "TO"),
                        ],
                        max_length=2,
                        verbose_name="UF",
                    ),
                ),
                (
                    "tipo",
                    models.CharField(
                        choices=[
                            ("PRINCIPAL", "Principal"),
                            ("SUPLEMENTAR", "Suplementar"),
                            ("OUTRA", "Outra"),
                        ],
                        default="PRINCIPAL",
                        max_length=20,
                        verbose_name="tipo",
                    ),
                ),
                ("principal", models.BooleanField(default=False, verbose_name="principal")),
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
                        related_name="inscricoes",
                        to="advogados.advogado",
                        verbose_name="advogado",
                    ),
                ),
            ],
            options={
                "verbose_name": "inscrição OAB",
                "verbose_name_plural": "inscrições OAB",
                "db_table": "inscricoes_oab",
                "ordering": ("-principal", "uf", "numero"),
            },
        ),
        migrations.RunPython(migrar_nome_e_oab, reverter_nome_e_oab),
        migrations.RemoveConstraint(
            model_name="advogado",
            name="uq_advogados_org_oab_uf",
        ),
        migrations.RemoveIndex(
            model_name="advogado",
            name="idx_advogados_oab_uf",
        ),
        migrations.RemoveField(
            model_name="advogado",
            name="nome",
        ),
        migrations.RemoveField(
            model_name="advogado",
            name="sobrenome",
        ),
        migrations.RemoveField(
            model_name="advogado",
            name="numero_oab",
        ),
        migrations.RemoveField(
            model_name="advogado",
            name="uf_oab",
        ),
        migrations.AlterField(
            model_name="advogado",
            name="cpf",
            field=models.CharField(
                blank=True,
                max_length=11,
                validators=[apps.advogados.models.validar_cpf],
                verbose_name="CPF",
            ),
        ),
        migrations.AlterField(
            model_name="advogado",
            name="usuario",
            field=models.OneToOneField(
                blank=True,
                db_column="usuario_id",
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="advogado",
                to=settings.AUTH_USER_MODEL,
                verbose_name="usuário",
            ),
        ),
        migrations.AlterModelOptions(
            name="advogado",
            options={
                "ordering": ("nome_completo",),
                "verbose_name": "advogado",
                "verbose_name_plural": "advogados",
            },
        ),
        migrations.AddIndex(
            model_name="advogado",
            index=models.Index(fields=["cpf"], name="idx_advogados_cpf"),
        ),
        migrations.AddIndex(
            model_name="inscricaooab",
            index=models.Index(fields=["advogado"], name="idx_inscricoes_oab_advogado"),
        ),
        migrations.AddIndex(
            model_name="inscricaooab",
            index=models.Index(fields=["numero", "uf"], name="idx_inscricoes_oab_numero_uf"),
        ),
        migrations.AddConstraint(
            model_name="inscricaooab",
            constraint=models.UniqueConstraint(
                fields=("advogado", "numero", "uf"),
                name="uq_inscricoes_oab_advogado_numero_uf",
            ),
        ),
    ]
