# Generated manually

from django.db import migrations, models


def marcar_existentes(apps, schema_editor):
    Usuario = apps.get_model("contas", "Usuario")
    Advogado = apps.get_model("advogados", "Advogado")
    InscricaoOab = apps.get_model("advogados", "InscricaoOab")

    for usuario in Usuario.objects.all():
        if usuario.is_staff or usuario.is_superuser:
            Usuario.objects.filter(pk=usuario.pk).update(deve_alterar_senha=False)
            continue
        tem_oab = InscricaoOab.objects.filter(
            advogado__usuario_id=usuario.pk, ativo=True
        ).exists()
        Usuario.objects.filter(pk=usuario.pk).update(deve_alterar_senha=not tem_oab)


def noop(apps, schema_editor):
    pass


class Migration(migrations.Migration):
    dependencies = [
        ("contas", "0003_alter_usuario_login_index"),
        ("advogados", "0003_advogado_inscricao_oab"),
    ]

    operations = [
        migrations.AddField(
            model_name="usuario",
            name="deve_alterar_senha",
            field=models.BooleanField(
                default=False,
                help_text="Marcado quando o administrador cria a conta com senha provisória.",
                verbose_name="deve alterar senha no próximo acesso",
            ),
        ),
        migrations.RunPython(marcar_existentes, noop),
    ]
