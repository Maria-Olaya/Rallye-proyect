# core/models.py

from django.db import models


class Municipio(models.Model):
    nombre = models.CharField(max_length=120)
    departamento = models.CharField(max_length=120)

    def __str__(self):
        return f"{self.nombre}, {self.departamento}"


class Sede(models.Model):
    nombre = models.CharField(max_length=120)
    direccion = models.CharField(max_length=200)
    municipio = models.ForeignKey(Municipio, on_delete=models.PROTECT, related_name="sedes")

    lat = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    lng = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)

    activa = models.BooleanField(default=True)

    def __str__(self):
        return self.nombre


class Local(models.Model):
    nombre = models.CharField(max_length=120)
    sede = models.ForeignKey(Sede, on_delete=models.PROTECT, related_name="locales")
    direccion = models.CharField(max_length=200)
    telefono = models.CharField(max_length=20)
    correo_admin = models.EmailField()
    descripcion = models.TextField(blank=True, default="")
    num_mecanicos = models.PositiveIntegerField()
    activo = models.BooleanField(default=True)
    horarios = models.JSONField(
        default=list,
        blank=True,
        help_text=('Lista de franjas: [{"dias":["lun","mar"], "apertura":"08:00", "cierre":"17:00"}]'),
    )
    # HU: Consultar info del local desde el mapa
    tiene_comercio = models.BooleanField(
        default=False,
        help_text="El local ofrece servicio de venta (comercio).",
    )
    tiene_taller = models.BooleanField(
        default=False,
        help_text="El local ofrece servicio de taller mecánico.",
    )

    def __str__(self):
        return self.nombre