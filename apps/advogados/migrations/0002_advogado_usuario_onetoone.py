import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("advogados", "0001_initial"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AlterField(
            model_name="advogado",
            name="usuario",
            field=models.OneToOneField(
                db_column="usuario_id",
                on_delete=django.db.models.deletion.CASCADE,
                related_name="advogado",
                to=settings.AUTH_USER_MODEL,
                verbose_name="usuário",
            ),
        ),
    ]
