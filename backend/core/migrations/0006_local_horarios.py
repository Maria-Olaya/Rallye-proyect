from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("core", "0005_local_horarios"),
    ]

    operations = [
        migrations.RemoveField(model_name="local", name="hora_apertura"),
        migrations.RemoveField(model_name="local", name="hora_cierre"),
        migrations.RemoveField(model_name="local", name="dias_atencion"),
        migrations.AddField(
            model_name="local",
            name="horarios",
            field=models.JSONField(
                blank=True,
                default=list,
                help_text=('Lista de franjas: [{"dias":["lun","mar"], "apertura":"08:00", "cierre":"17:00"}]'),
            ),
        ),
    ]
