# scheduling/services.py

from datetime import datetime, timedelta, date

from django.conf import settings
from django.core.mail import send_mail
from django.utils import timezone

from core.models import Local
from scheduling.models import Cita


def citas_por_dia(local: Local) -> int:
    apertura = local.hora_apertura.hour * 60 + local.hora_apertura.minute
    cierre = local.hora_cierre.hour * 60 + local.hora_cierre.minute
    slots = (cierre - apertura) // 120
    return slots * local.num_mecanicos


def generar_citas_para_local(local: Local, fecha: date) -> list[Cita]:
    # Si ya hay citas para ese local y fecha, no generamos nada
    if Cita.objects.filter(local=local, fecha=fecha).exists():
        return []

    apertura = datetime.combine(fecha, local.hora_apertura)
    cierre = datetime.combine(fecha, local.hora_cierre)
    slot_duration = timedelta(hours=2)

    citas_creadas = []
    hora_actual = apertura

    while hora_actual + slot_duration <= cierre:
        hora_fin = hora_actual + slot_duration
        for _ in range(local.num_mecanicos):
            cita = Cita.objects.create(
                local=local,
                fecha=fecha,
                hora_inicio=hora_actual.time(),
                hora_fin=hora_fin.time(),
                estado=Cita.Estado.LIBRE,
            )
            citas_creadas.append(cita)
        hora_actual += slot_duration

    return citas_creadas


def generar_citas_rango(local: Local, fecha_inicio: date, dias: int = 30) -> int:
    """
    Genera citas para un local durante N días a partir de fecha_inicio.
    Omite fechas que ya tienen citas. Retorna total de citas creadas.
    """
    total = 0
    for i in range(dias):
        fecha = fecha_inicio + timedelta(days=i)
        citas = generar_citas_para_local(local, fecha)
        total += len(citas)
    return total


# ── Catálogos auxiliares de nombres ───────────────────────────────────

_NOMBRE_SERVICIO = {
    "MANTENIMIENTO": "Mantenimiento General",
    "REVISION": "Revisión General",
    "ALISTAMIENTO": "Alistamiento",
    "GARANTIA": "Revisión por Garantía",
}

_DURACION_ESTIMADA = {
    "MANTENIMIENTO": "2 horas",
    "REVISION": "2 horas",
    "ALISTAMIENTO": "2 horas",
    "GARANTIA": "2 horas",
}


# ── HU-03 · Enviar correo de confirmación ─────────────────────────────


def enviar_correo_confirmacion(cita: Cita) -> bool:
    """
    Envía correo de confirmación al cliente tras el agendamiento.
    Registra resultado en correo_confirmacion_enviado,
    fecha_envio_confirmacion y error_envio_confirmacion.
    Retorna True si fue exitoso, False si falló.
    """
    try:
        nombre_servicio = _NOMBRE_SERVICIO.get(cita.tipo_servicio, cita.tipo_servicio)
        duracion = _DURACION_ESTIMADA.get(cita.tipo_servicio, "2 horas")
        sede_nombre = cita.local.sede.nombre if cita.local.sede else ""

        asunto = "Confirmación de cita — Rallye Motor's · "

        mensaje = f"""Hola {cita.cliente_nombre},

Tu cita de servicio técnico ha sido registrada exitosamente.

──────────────────────────────
DETALLES DE TU CITA
──────────────────────────────
Categoría:         {nombre_servicio}
Fecha:             {cita.fecha.strftime("%d/%m/%Y")}
Hora:              {cita.hora_inicio.strftime("%I:%M %p")} – {cita.hora_fin.strftime("%I:%M %p")}
Duración:          Max. {duracion}
Sede:              {sede_nombre}
Local:             {cita.local.nombre}
Dirección:         {cita.local.direccion}
──────────────────────────────

Recuerda que puedes cancelar tu cita hasta un día antes de la fecha programada dentro de la app web.

Para más información contáctanos:
✉ sistemas@rallyemotors.com.co

¡Te esperamos!
Equipo Rallye Motor's
"""

        send_mail(
            subject=asunto,
            message=mensaje,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[cita.cliente_correo],
            fail_silently=False,
        )

        cita.correo_confirmacion_enviado = True
        cita.fecha_envio_confirmacion = timezone.now()
        cita.error_envio_confirmacion = ""
        cita.save(
            update_fields=[
                "correo_confirmacion_enviado",
                "fecha_envio_confirmacion",
                "error_envio_confirmacion",
            ]
        )
        return True

    except Exception as e:
        cita.correo_confirmacion_enviado = False
        cita.fecha_envio_confirmacion = timezone.now()
        cita.error_envio_confirmacion = str(e)
        cita.save(
            update_fields=[
                "correo_confirmacion_enviado",
                "fecha_envio_confirmacion",
                "error_envio_confirmacion",
            ]
        )
        return False


# ── HU-06 · Notificación de cancelación al administrador ──────────────


def enviar_correo_cancelacion_admin(cita: Cita) -> bool:
    """
    Envía un correo al administrador del local cuando una cita ha sido cancelada.

    Solo envía si la cita existe y está en estado CANCELADA.
    Registra resultado en correo_cancelacion_enviado,
    fecha_envio_cancelacion y error_envio_cancelacion.

    Retorna True si fue exitoso, False si no aplica o si falló.
    """
    if not cita:
        return False

    if cita.estado != Cita.Estado.CANCELADA:
        return False

    try:
        nombre_servicio = _NOMBRE_SERVICIO.get(cita.tipo_servicio, cita.tipo_servicio or "No especificada")
        sede_nombre = cita.local.sede.nombre if cita.local.sede else ""
        correo_admin = cita.local.correo_admin

        asunto = "Cancelación de cita — Rallye Motor's"

        mensaje = f"""Hola administrador(a) de {cita.local.nombre},

Se ha cancelado una cita de servicio técnico y es necesario reorganizar la agenda de atención.

──────────────────────────────
DETALLES DE LA CITA CANCELADA
──────────────────────────────
Categoría:         {nombre_servicio}
Fecha:             {cita.fecha.strftime("%d/%m/%Y")}
Hora:              {cita.hora_inicio.strftime("%I:%M %p")} – {cita.hora_fin.strftime("%I:%M %p")}
Sede:              {sede_nombre}
Local:             {cita.local.nombre}
Dirección:         {cita.local.direccion}
Cliente:           {cita.cliente_nombre or "No registrado"}
Documento:         {cita.cliente_documento or "No registrado"}
Teléfono:          {cita.cliente_telefono or "No registrado"}
Correo cliente:    {cita.cliente_correo or "No registrado"}
Placa:             {cita.placa_moto or "No registrada"}
Referencia moto:   {cita.referencia_moto or "No registrada"}
──────────────────────────────

Este correo fue generado automáticamente por el sistema de Rallye Motor's.
"""

        send_mail(
            subject=asunto,
            message=mensaje,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[correo_admin],
            fail_silently=False,
        )

        cita.correo_cancelacion_enviado = True
        cita.fecha_envio_cancelacion = timezone.now()
        cita.error_envio_cancelacion = ""
        cita.save(
            update_fields=[
                "correo_cancelacion_enviado",
                "fecha_envio_cancelacion",
                "error_envio_cancelacion",
            ]
        )
        return True

    except Exception as e:
        cita.correo_cancelacion_enviado = False
        cita.fecha_envio_cancelacion = timezone.now()
        cita.error_envio_cancelacion = str(e)
        cita.save(
            update_fields=[
                "correo_cancelacion_enviado",
                "fecha_envio_cancelacion",
                "error_envio_cancelacion",
            ]
        )
        return False
