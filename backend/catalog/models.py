# catalog/models.py

from django.conf import settings
from django.db import models

from core.models import Local


class Motocicleta(models.Model):
    class TipoMotocicleta(models.TextChoices):
        DEPORTIVA = "DEPORTIVA", "Deportiva"
        URBANA = "URBANA", "Urbana"
        TODOTERRENO = "TODOTERRENO", "Todoterreno"
        CUATRIMOTOS = "CUATRIMOTOS", "Cuatrimotos"
        AUTOMATICA = "AUTOMATICA", "Automaticas y Semiautomaticas"

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
        return f"{self.usuario} - {self.repuesto} ({self.created_at.date()})"


class CotizacionMotocicleta(models.Model):
    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
    )
    motocicleta = models.ForeignKey(Motocicleta, on_delete=models.PROTECT)
    local = models.ForeignKey(
        Local,
        on_delete=models.PROTECT,
        related_name="cotizaciones_motocicletas",
        null=True,
        blank=True,
    )
    radicado = models.CharField(max_length=30, unique=True, null=True, blank=True)
    precio_base = models.DecimalField(max_digits=12, decimal_places=2)
    impuestos_estimados = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    tramites_estimados = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    total_estimado = models.DecimalField(max_digits=12, decimal_places=2)
    cliente_nombre = models.CharField(max_length=120, blank=True, default="")
    cliente_correo = models.EmailField(blank=True, default="")
    cliente_telefono = models.CharField(max_length=20, blank=True, default="")
    correo_cotizacion_enviado = models.BooleanField(default=False)
    fecha_envio_cotizacion = models.DateTimeField(null=True, blank=True)
    error_envio_cotizacion = models.TextField(blank=True, default="")
    comentario = models.CharField(max_length=255, blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at", "-id"]

    def __str__(self):
        return f"{self.radicado or 'SIN-RADICADO'} - {self.motocicleta}"


# ── HU: Registrar interés en repuesto ────────────────────────────────────────


class ConsultaRepuesto(models.Model):
    """Tabla estadística — registra cada consulta de repuesto realizada."""

    repuesto_nombre = models.CharField(max_length=200)
    repuesto_referencia = models.CharField(max_length=80, blank=True, default="")
    modelo_moto = models.CharField(max_length=120, blank=True, default="")
    local = models.ForeignKey(
        Local,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="consultas_repuestos",
    )
    fecha = models.DateField(auto_now_add=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Consulta de repuesto"
        verbose_name_plural = "Consultas de repuestos"

    def __str__(self):
        return f"{self.repuesto_nombre} [{self.modelo_moto}] — {self.fecha}"
