import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("diagnostics", "0002_initial"),
        ("scheduling", "0005_cita_estado_atendido"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.RenameField(
            model_name="diagnostico",
            old_name="created_at",
            new_name="fecha_registro",
        ),
        migrations.AddField(
            model_name="diagnostico",
            name="correo_radicado_enviado",
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name="diagnostico",
            name="fecha_envio_radicado",
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="diagnostico",
            name="radicado",
            field=models.CharField(blank=True, max_length=30, null=True, unique=True),
        ),
        migrations.AddField(
            model_name="diagnostico",
            name="registrado_por",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name="diagnosticos_registrados",
                to=settings.AUTH_USER_MODEL,
            ),
        ),
    ]
