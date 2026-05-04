from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("core", "0003_alter_local_id_alter_municipio_id_alter_sede_id"),
    ]

    operations = [
        migrations.AddField(
            model_name="local",
            name="dias_atencion",
            field=models.JSONField(blank=True, default=list),
        ),
    ]
