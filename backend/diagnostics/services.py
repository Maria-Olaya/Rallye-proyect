from io import BytesIO
from textwrap import wrap

from django.conf import settings
from django.core.mail import EmailMessage
from django.utils import timezone
from reportlab.lib.pagesizes import LETTER
from reportlab.pdfgen import canvas

from diagnostics.models import Diagnostico


_NOMBRE_SERVICIO = {
    "MANTENIMIENTO": "Mantenimiento General",
    "REVISION": "Revisión General",
    "ALISTAMIENTO": "Alistamiento",
    "GARANTIA": "Revisión por Garantía",
}


def generar_radicado() -> str:
    base = timezone.localtime().strftime("RAD-%Y%m%d-%H%M%S")
    sufijo = 1
    codigo = f"{base}-{sufijo:02d}"
    while Diagnostico.objects.filter(radicado=codigo).exists():
        sufijo += 1
        codigo = f"{base}-{sufijo:02d}"
    return codigo


def _dibujar_titulo(pdf: canvas.Canvas, y: int, titulo: str, subtitulo: str) -> int:
    pdf.setFont("Helvetica-Bold", 18)
    pdf.drawString(50, y, titulo)
    y -= 22
    pdf.setFont("Helvetica", 10)
    pdf.drawString(50, y, subtitulo)
    y -= 12
    pdf.line(50, y, 560, y)
    return y - 20


def _dibujar_seccion(pdf: canvas.Canvas, y: int, titulo: str) -> int:
    pdf.setFont("Helvetica-Bold", 12)
    pdf.drawString(50, y, titulo)
    y -= 8
    pdf.line(50, y, 260, y)
    return y - 18


def _dibujar_campo(pdf: canvas.Canvas, y: int, etiqueta: str, valor: str) -> int:
    pdf.setFont("Helvetica-Bold", 10)
    pdf.drawString(50, y, f"{etiqueta}:")
    pdf.setFont("Helvetica", 10)
    pdf.drawString(145, y, valor)
    return y - 18


def _dibujar_parrafo(pdf: canvas.Canvas, y: int, texto: str, ancho: int = 78) -> int:
    pdf.setFont("Helvetica", 10)
    for linea in wrap(texto, width=ancho):
        if y < 70:
            pdf.showPage()
            y = 750
            pdf.setFont("Helvetica", 10)
        pdf.drawString(50, y, linea)
        y -= 16
    return y


def generar_pdf_radicado(diagnostico: Diagnostico) -> bytes:
    """
    Genera el PDF del radicado en memoria y retorna su contenido en bytes.
    """
    buffer = BytesIO()
    pdf = canvas.Canvas(buffer, pagesize=LETTER)
    _, height = LETTER

    cita = diagnostico.cita
    nombre_servicio = _NOMBRE_SERVICIO.get(
        cita.tipo_servicio,
        cita.tipo_servicio or "No especificado",
    )
    fecha_registro = timezone.localtime(diagnostico.fecha_registro).strftime("%d/%m/%Y %I:%M %p")

    y = height - 50

    y = _dibujar_titulo(
        pdf,
        y,
        "Radicado de Servicio Técnico",
        "Rallye Motor's · Documento soporte del servicio realizado",
    )

    y = _dibujar_campo(pdf, y, "Radicado", diagnostico.radicado)
    y = _dibujar_campo(pdf, y, "Fecha de registro", fecha_registro)
    y = _dibujar_campo(pdf, y, "Registrado por", str(diagnostico.registrado_por or "No registrado"))

    y -= 10
    y = _dibujar_seccion(pdf, y, "Datos del cliente")
    y = _dibujar_campo(pdf, y, "Nombre", cita.cliente_nombre or "No registrado")
    y = _dibujar_campo(pdf, y, "Documento", cita.cliente_documento or "No registrado")
    y = _dibujar_campo(pdf, y, "Teléfono", cita.cliente_telefono or "No registrado")
    y = _dibujar_campo(pdf, y, "Correo", cita.cliente_correo or "No registrado")

    y -= 10
    y = _dibujar_seccion(pdf, y, "Datos de la motocicleta")
    y = _dibujar_campo(pdf, y, "Placa", cita.placa_moto or "No registrada")
    y = _dibujar_campo(pdf, y, "Referencia", cita.referencia_moto or "No registrada")
    y = _dibujar_campo(pdf, y, "Año/modelo", str(cita.anio_moto or "No registrado"))

    y -= 10
    y = _dibujar_seccion(pdf, y, "Datos del servicio")
    y = _dibujar_campo(pdf, y, "Categoría", nombre_servicio)
    y = _dibujar_campo(pdf, y, "Fecha de la cita", cita.fecha.strftime("%d/%m/%Y"))
    y = _dibujar_campo(
        pdf,
        y,
        "Hora",
        f"{cita.hora_inicio.strftime('%I:%M %p')} - {cita.hora_fin.strftime('%I:%M %p')}",
    )
    y = _dibujar_campo(pdf, y, "Local", cita.local.nombre)
    y = _dibujar_campo(pdf, y, "Dirección", cita.local.direccion)

    y -= 10
    y = _dibujar_seccion(pdf, y, "Diagnóstico técnico")
    y = _dibujar_parrafo(pdf, y, diagnostico.descripcion)

    y -= 20
    if y < 90:
        pdf.showPage()
        y = 750

    pdf.line(50, y, 560, y)
    y -= 18
    pdf.setFont("Helvetica", 9)
    pdf.drawString(
        50,
        y,
        "Este documento constituye soporte del servicio técnico realizado por Rallye Motor's.",
    )

    pdf.showPage()
    pdf.save()

    buffer.seek(0)
    return buffer.getvalue()


def enviar_radicado_por_correo(diagnostico: Diagnostico) -> bool:
    """
    Envía el radicado al correo del cliente con el PDF adjunto.
    Usa el radicado que ya fue generado y guardado en HU-04.
    Registra resultado en correo_radicado_enviado y fecha_envio_radicado.
    Retorna True si fue exitoso, False si falló.
    """
    if not diagnostico:
        return False

    cita = diagnostico.cita

    if not cita.cliente_correo:
        diagnostico.correo_radicado_enviado = False
        diagnostico.fecha_envio_radicado = None
        diagnostico.save(update_fields=["correo_radicado_enviado", "fecha_envio_radicado"])
        return False

    try:
        pdf_bytes = generar_pdf_radicado(diagnostico)

        asunto = f"Radicado de servicio técnico {diagnostico.radicado} — Rallye Motor's"

        mensaje = f"""Hola, {cita.cliente_nombre},

Te informamos que el servicio del diagnóstico de tu motocicleta ha sido registrado exitosamente.
Adjunto a este correo encontrarás el radicado del servicio, el cual incluye el diagnóstico técnico en formato PDF.
Este documento sirve como soporte del servicio efectuado y referencia para cualquier consulta posterior.

Este correo confirma el envío exitoso del radicado y constituye un soporte del servicio realizado.

Gracias por confiar en Rallye Motor's.

Atentamente,
Rallye Motor's
Servicio Técnico Yamaha
"""

        correo = EmailMessage(
            subject=asunto,
            body=mensaje,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[cita.cliente_correo],
        )
        correo.attach(
            filename=f"{diagnostico.radicado}.pdf",
            content=pdf_bytes,
            mimetype="application/pdf",
        )
        correo.send(fail_silently=False)

        diagnostico.correo_radicado_enviado = True
        diagnostico.fecha_envio_radicado = timezone.now()
        diagnostico.save(update_fields=["correo_radicado_enviado", "fecha_envio_radicado"])
        return True

    except Exception:
        diagnostico.correo_radicado_enviado = False
        diagnostico.fecha_envio_radicado = None
        diagnostico.save(update_fields=["correo_radicado_enviado", "fecha_envio_radicado"])
        return False
