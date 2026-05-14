# core/migrations/0011_local_servicios.py

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        # Ajusta el nombre de la migración anterior de core según tu proyecto
        ("core", "0006_local_horarios"),  # <-- reemplaza con el nombre real de la última migración de core
    ]

    operations = [
        migrations.AddField(
            model_name="local",
            name="tiene_comercio",
            field=models.BooleanField(
                default=False,
                help_text="El local ofrece servicio de venta (comercio).",
            ),
        ),
        migrations.AddField(
            model_name="local",
            name="tiene_taller",
            field=models.BooleanField(
                default=False,
                help_text="El local ofrece servicio de taller mecánico.",
            ),
        ),
    ]
