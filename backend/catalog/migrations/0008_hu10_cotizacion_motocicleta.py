from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ("core", "0002_alter_municipio_id_alter_sede_id_local"),
        ("catalog", "0007_alter_cotizacionmotocicleta_id_and_more"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AlterField(
            model_name="cotizacionmotocicleta",
            name="usuario",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                to=settings.AUTH_USER_MODEL,
            ),
        ),
        migrations.AddField(
            model_name="cotizacionmotocicleta",
            name="cliente_correo",
            field=models.EmailField(blank=True, default="", max_length=254),
        ),
        migrations.AddField(
            model_name="cotizacionmotocicleta",
            name="cliente_nombre",
            field=models.CharField(blank=True, default="", max_length=120),
        ),
        migrations.AddField(
            model_name="cotizacionmotocicleta",
            name="cliente_telefono",
            field=models.CharField(blank=True, default="", max_length=20),
        ),
        migrations.AddField(
            model_name="cotizacionmotocicleta",
            name="correo_cotizacion_enviado",
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name="cotizacionmotocicleta",
            name="error_envio_cotizacion",
            field=models.TextField(blank=True, default=""),
        ),
        migrations.AddField(
            model_name="cotizacionmotocicleta",
            name="fecha_envio_cotizacion",
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="cotizacionmotocicleta",
            name="impuestos_estimados",
            field=models.DecimalField(decimal_places=2, default=0, max_digits=12),
        ),
        migrations.AddField(
            model_name="cotizacionmotocicleta",
            name="local",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name="cotizaciones_motocicletas",
                to="core.local",
            ),
        ),
        migrations.AddField(
            model_name="cotizacionmotocicleta",
            name="precio_base",
            field=models.DecimalField(decimal_places=2, default=0, max_digits=12),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name="cotizacionmotocicleta",
            name="radicado",
            field=models.CharField(blank=True, max_length=30, null=True, unique=True),
        ),
        migrations.AddField(
            model_name="cotizacionmotocicleta",
            name="total_estimado",
            field=models.DecimalField(decimal_places=2, default=0, max_digits=12),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name="cotizacionmotocicleta",
            name="tramites_estimados",
            field=models.DecimalField(decimal_places=2, default=0, max_digits=12),
        ),
        migrations.AlterModelOptions(
            name="cotizacionmotocicleta",
            options={"ordering": ["-created_at", "-id"]},
        ),
    ]
