# catalog/models.py

from django.conf import settings
from django.db import models


class Motocicleta(models.Model):
    class TipoMotocicleta(models.TextChoices):
        DEPORTIVA = "DEPORTIVA", "Deportiva"
        URBANA = "URBANA", "Urbana"
        TODOTERRENO = "TODOTERRENO", "Todoterreno"
        CUATRIMOTOS = "CUATRIMOTOS", "Cuatrimotos"
        AUTOMATICA = "AUTOMATICA", "Automáticas y Semiautomáticas"

    marca = models.CharField(max_length=80, default="Yamaha", editable=False)
    referencia = models.CharField(max_length=80)
    anio = models.IntegerField()
    tipo = models.CharField(
        max_length=20,
        choices=TipoMotocicleta.choices,
        default=TipoMotocicleta.URBANA,
    )
    cilindraje = models.PositiveIntegerField()
    precio = models.DecimalField(max_digits=12, decimal_places=2)
    caracteristicas = models.TextField(blank=True, default="")
    imagen = models.ImageField(upload_to="motocicletas/", null=True, blank=True)
    activa = models.BooleanField(default=True)

    def __str__(self):
        return f"Yamaha {self.referencia} ({self.anio})"


class Repuesto(models.Model):
    nombre = models.CharField(max_length=120)
    referencia = models.CharField(max_length=80, blank=True, default="")
    precio = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    stock = models.IntegerField(default=0)
    activo = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.nombre} ({self.referencia})"


class InteresRepuesto(models.Model):
    usuario = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    repuesto = models.ForeignKey(Repuesto, on_delete=models.PROTECT)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.usuario} — {self.repuesto} ({self.created_at.date()})"


class CotizacionMotocicleta(models.Model):
    usuario = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    motocicleta = models.ForeignKey(Motocicleta, on_delete=models.PROTECT)
    comentario = models.CharField(max_length=255, blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Cotización {self.motocicleta} — {self.usuario} ({self.created_at.date()})"
