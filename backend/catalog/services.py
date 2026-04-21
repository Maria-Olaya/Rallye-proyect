from decimal import Decimal, ROUND_HALF_UP
import re
from urllib.parse import quote

from django.conf import settings
from django.core.mail import send_mail
from django.utils import timezone

from catalog.models import CotizacionMotocicleta

IMPUESTO_RATE = Decimal("0.19")
TRAMITES_RATE = Decimal("0.08")
MONEY_STEP = Decimal("0.01")


def _money(value: Decimal) -> Decimal:
    return value.quantize(MONEY_STEP, rounding=ROUND_HALF_UP)


def generar_radicado_cotizacion() -> str:
    base = timezone.localtime().strftime("COT-%Y%m%d-%H%M%S")
    sufijo = 1
    codigo = f"{base}-{sufijo:02d}"
    while CotizacionMotocicleta.objects.filter(radicado=codigo).exists():
        sufijo += 1
        codigo = f"{base}-{sufijo:02d}"
    return codigo


def calcular_desglose_cotizacion(precio_base: Decimal) -> dict[str, Decimal]:
    impuestos_estimados = _money(precio_base * IMPUESTO_RATE)
    tramites_estimados = _money(precio_base * TRAMITES_RATE)
    total_estimado = _money(precio_base + impuestos_estimados + tramites_estimados)
    return {
        "precio_base": _money(precio_base),
        "impuestos_estimados": impuestos_estimados,
        "tramites_estimados": tramites_estimados,
        "total_estimado": total_estimado,
    }


def construir_enlace_whatsapp(telefono: str, radicado: str, nombre_motocicleta: str) -> str:
    numero = re.sub(r"\D", "", telefono or "")
    if len(numero) == 10:
        numero = f"57{numero}"

    mensaje = (
        f"Hola, quiero continuar la atencion de mi cotizacion {radicado} para la motocicleta {nombre_motocicleta}."
    )
    return f"https://wa.me/{numero}?text={quote(mensaje)}"


def enviar_cotizacion_por_correo(cotizacion: CotizacionMotocicleta) -> bool:
    if not cotizacion.cliente_correo:
        cotizacion.correo_cotizacion_enviado = False
        cotizacion.fecha_envio_cotizacion = None
        cotizacion.error_envio_cotizacion = ""
        cotizacion.save(
            update_fields=[
                "correo_cotizacion_enviado",
                "fecha_envio_cotizacion",
                "error_envio_cotizacion",
            ]
        )
        return False

    try:
        moto = cotizacion.motocicleta
        asunto = f"Cotizacion {cotizacion.radicado} - Rallye Motor's"
        local_nombre = cotizacion.local.nombre if cotizacion.local else "Pendiente por definir"
        local_direccion = cotizacion.local.direccion if cotizacion.local else "Pendiente por definir"
        mensaje = f"""Hola {cotizacion.cliente_nombre or "cliente"},

Tu cotizacion de motocicleta fue generada exitosamente.

DETALLES DE LA COTIZACION
Radicado:           {cotizacion.radicado}
Motocicleta:        Yamaha {moto.referencia} {moto.anio}
Local de interes:   {local_nombre}
Direccion:          {local_direccion}
Precio base:        ${cotizacion.precio_base}
Impuestos:          ${cotizacion.impuestos_estimados}
Tramites:           ${cotizacion.tramites_estimados}
Total estimado:     ${cotizacion.total_estimado}

Cuando haya un local asignado, podras continuar la atencion por WhatsApp.

Equipo Rallye Motor's
"""
        send_mail(
            subject=asunto,
            message=mensaje,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[cotizacion.cliente_correo],
            fail_silently=False,
        )

        cotizacion.correo_cotizacion_enviado = True
        cotizacion.fecha_envio_cotizacion = timezone.now()
        cotizacion.error_envio_cotizacion = ""
        cotizacion.save(
            update_fields=[
                "correo_cotizacion_enviado",
                "fecha_envio_cotizacion",
                "error_envio_cotizacion",
            ]
        )
        return True
    except Exception as exc:
        cotizacion.correo_cotizacion_enviado = False
        cotizacion.fecha_envio_cotizacion = timezone.now()
        cotizacion.error_envio_cotizacion = str(exc)
        cotizacion.save(
            update_fields=[
                "correo_cotizacion_enviado",
                "fecha_envio_cotizacion",
                "error_envio_cotizacion",
            ]
        )
        return False
