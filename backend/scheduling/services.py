# scheduling/services.py

from datetime import date, datetime, timedelta

from django.conf import settings
from django.core.mail import send_mail
from django.db import models as db_models
from django.utils import timezone

from core.models import Local
from scheduling.models import Cita

from datetime import time

ALMUERZO_INICIO = time(12, 0)
ALMUERZO_FIN = time(13, 0)
SLOT_DURACION = timedelta(hours=2)


DIAS_MAP = {
    0: "lun",
    1: "mar",
    2: "mie",
    3: "jue",
    4: "vie",
    5: "sab",
    6: "dom",
}


def _franjas_del_dia(local, fecha: date) -> list[tuple[time, time]]:
    """
    Retorna solo las franjas cuyo campo 'dias' incluye el día de la semana
    correspondiente a 'fecha'.
    """
    dia_semana = DIAS_MAP[fecha.weekday()]
    franjas = []
    for f in local.horarios or []:
        try:
            if dia_semana not in f.get("dias", []):
                continue
            ap = time.fromisoformat(f["apertura"])
            ci = time.fromisoformat(f["cierre"])
            if ap < ci:
                franjas.append((ap, ci))
        except (KeyError, ValueError):
            continue
    return franjas


def _slots_en_franja(fecha: date, apertura: time, cierre: time) -> list[tuple[datetime, datetime]]:
    slots = []
    inicio = datetime.combine(fecha, apertura)
    fin_franja = datetime.combine(fecha, cierre)
    almuerzo_ini = datetime.combine(fecha, ALMUERZO_INICIO)
    almuerzo_fin = datetime.combine(fecha, ALMUERZO_FIN)

    while inicio + SLOT_DURACION <= fin_franja:
        fin_slot = inicio + SLOT_DURACION

        # Si el slot solapa con el almuerzo, saltar al fin del almuerzo y reintentar
        if inicio < almuerzo_fin and fin_slot > almuerzo_ini:
            inicio = almuerzo_fin
            continue  # vuelve al while, que verifica si inicio + SLOT_DURACION <= fin_franja

        slots.append((inicio, fin_slot))
        inicio = fin_slot

    return slots


def citas_por_dia(local, fecha: date = None) -> int:
    if fecha is None:
        fecha = date.today()
    franjas = _franjas_del_dia(local, fecha)
    total_slots = sum(len(_slots_en_franja(fecha, ap, ci)) for ap, ci in franjas)
    return total_slots * local.num_mecanicos


def generar_citas_para_local(local, fecha: date) -> list:
    from scheduling.models import Cita

    if Cita.objects.filter(local=local, fecha=fecha).exists():
        return []

    franjas = _franjas_del_dia(local, fecha)  # <-- ahora pasa fecha
    if not franjas:
        return []

    citas_creadas = []
    for apertura, cierre in franjas:
        for inicio, fin in _slots_en_franja(fecha, apertura, cierre):
            for _ in range(local.num_mecanicos):
                cita = Cita.objects.create(
                    local=local,
                    fecha=fecha,
                    hora_inicio=inicio.time(),
                    hora_fin=fin.time(),
                    estado=Cita.Estado.LIBRE,
                )
                citas_creadas.append(cita)

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


# ── Actualización automática de estado ATENDIDO ───────────────────────


def marcar_citas_atendidas() -> int:
    """
    Marca como ATENDIDO todas las citas ASIGNADAS cuya fecha y hora_fin
    ya hayan pasado en hora colombiana.
    Retorna el número de citas actualizadas.
    """
    ahora = timezone.localtime()
    fecha_hoy = ahora.date()
    hora_ahora = ahora.time()

    citas = Cita.objects.filter(estado=Cita.Estado.ASIGNADA).filter(
        db_models.Q(fecha__lt=fecha_hoy) | db_models.Q(fecha=fecha_hoy, hora_fin__lte=hora_ahora)
    )
    total = citas.update(estado=Cita.Estado.ATENDIDO)
    return total
