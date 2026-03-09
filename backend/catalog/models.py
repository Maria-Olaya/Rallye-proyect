from django.db import models
from django.conf import settings


class Motocicleta(models.Model):
    marca = models.CharField(max_length=80)
    modelo = models.CharField(max_length=80)
    anio = models.IntegerField()
    precio = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    activa = models.BooleanField(default=True)


class Repuesto(models.Model):
    nombre = models.CharField(max_length=120)
    referencia = models.CharField(max_length=80, blank=True, default="")
    precio = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    stock = models.IntegerField(default=0)
    activo = models.BooleanField(default=True)


class InteresRepuesto(models.Model):
    usuario = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    repuesto = models.ForeignKey(Repuesto, on_delete=models.PROTECT)
    created_at = models.DateTimeField(auto_now_add=True)


class CotizacionMotocicleta(models.Model):
    usuario = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    motocicleta = models.ForeignKey(Motocicleta, on_delete=models.PROTECT)
    comentario = models.CharField(max_length=255, blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)
