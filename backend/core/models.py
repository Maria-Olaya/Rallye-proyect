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
    hora_apertura = models.TimeField()
    hora_cierre = models.TimeField()
    num_mecanicos = models.PositiveIntegerField()
    activo = models.BooleanField(default=True)

    def __str__(self):
        return self.nombre
