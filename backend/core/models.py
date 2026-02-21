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