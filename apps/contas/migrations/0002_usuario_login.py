from django.db import migrations, models


def popular_login(apps, schema_editor):
    Usuario = apps.get_model("contas", "Usuario")
    for usuario in Usuario.objects.all():
        login = (usuario.email or f"user-{usuario.pk}").strip().lower()
        base = login
        contador = 2
        while Usuario.objects.filter(login=login).exclude(pk=usuario.pk).exists():
            login = f"{base}-{contador}"
            contador += 1
        Usuario.objects.filter(pk=usuario.pk).update(login=login)


def noop_reverse(apps, schema_editor):
    pass


class Migration(migrations.Migration):
    dependencies = [
        ("contas", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="usuario",
            name="login",
            field=models.CharField(default="", max_length=150, verbose_name="login"),
            preserve_default=False,
        ),
        migrations.RunPython(popular_login, noop_reverse),
        migrations.AlterField(
            model_name="usuario",
            name="login",
            field=models.CharField(
                max_length=150, unique=True, verbose_name="login"
            ),
        ),
        migrations.AlterField(
            model_name="usuario",
            name="email",
            field=models.EmailField(
                blank=True,
                db_index=True,
                max_length=254,
                null=True,
                unique=True,
                verbose_name="e-mail",
            ),
        ),
        migrations.AlterField(
            model_name="usuario",
            name="nome",
            field=models.CharField(
                blank=True, default="", max_length=150, verbose_name="nome"
            ),
        ),
        migrations.AlterModelOptions(
            name="usuario",
            options={
                "ordering": ("login",),
                "verbose_name": "usuário",
                "verbose_name_plural": "usuários",
            },
        ),
    ]
