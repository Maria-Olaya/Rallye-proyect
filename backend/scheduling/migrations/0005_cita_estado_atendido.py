from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("scheduling", "0004_cita_correo_cancelacion_enviado_and_more"),
    ]

    operations = [
        migrations.AlterField(
            model_name="cita",
            name="estado",
            field=models.CharField(
                choices=[
                    ("LIBRE", "Libre"),
                    ("ASIGNADA", "Asignada"),
                    ("ATENDIDO", "Atendido"),
                    ("CANCELADA", "Cancelada"),
                ],
                default="LIBRE",
                max_length=20,
            ),
        ),
    ]
