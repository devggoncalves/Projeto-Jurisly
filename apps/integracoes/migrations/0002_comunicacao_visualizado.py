# Generated manually

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("integracoes", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="comunicacaoadvogado",
            name="visualizado",
            field=models.BooleanField(default=False, verbose_name="visualizado"),
        ),
        migrations.AddField(
            model_name="comunicacaoadvogado",
            name="visualizado_em",
            field=models.DateTimeField(blank=True, null=True, verbose_name="visualizado em"),
        ),
        migrations.AddIndex(
            model_name="comunicacaoadvogado",
            index=models.Index(fields=["visualizado"], name="idx_com_adv_visualizado"),
        ),
    ]
