import re
from datetime import date, datetime, timedelta

from django.utils import timezone
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from core.models import Local
from scheduling.models import Cita
from scheduling.serializers import (
    AgendarCitaSerializer,
    CitaDisponibleSerializer,
    CitaParaCancelarSerializer,
)
from scheduling.services import (
    enviar_correo_cancelacion_admin,
    enviar_correo_confirmacion,
    generar_citas_para_local,
    marcar_citas_atendidas,
)


def _liberar_cita(cita: Cita) -> None:
    """Deja una cita nuevamente disponible y limpia los datos asociados."""
    cita.estado = Cita.Estado.LIBRE
    cita.tipo_servicio = None
    cita.tipo_documento = ""
    cita.cliente_nombre = ""
    cita.cliente_documento = ""
    cita.cliente_telefono = ""
    cita.cliente_correo = ""
    cita.placa_moto = ""
    cita.referencia_moto = ""
    cita.anio_moto = None
    cita.save()


def _normalizar_placa(valor: str) -> str:
    return (valor or "").strip().upper()


class CitasDisponiblesView(APIView):
    """GET /api/scheduling/disponibles/?local=<id>&fecha=<YYYY-MM-DD>"""

    permission_classes = [AllowAny]

    def get(self, request):
        local_id = request.query_params.get("local")
        fecha_str = request.query_params.get("fecha")

        if not local_id or not fecha_str:
            return Response(
                {"error": "Parámetros requeridos: local, fecha"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            fecha = date.fromisoformat(fecha_str)
            local = Local.objects.get(pk=local_id, activo=True)
        except (ValueError, Local.DoesNotExist):
            return Response(
                {"error": "Local o fecha inválidos."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Actualiza citas vencidas a ATENDIDO antes de mostrar disponibles
        marcar_citas_atendidas()

        # Genera los slots del día si aún no existen
        generar_citas_para_local(local, fecha)

        citas = Cita.objects.filter(
            local=local,
            fecha=fecha,
            estado=Cita.Estado.LIBRE,
        ).order_by("hora_inicio")

        serializer = CitaDisponibleSerializer(citas, many=True)
        return Response(serializer.data)


class AgendarCitaView(APIView):
    """PATCH /api/scheduling/agendar/<cita_id>/"""

    permission_classes = [AllowAny]

    def patch(self, request, cita_id):
        try:
            cita = Cita.objects.get(pk=cita_id)
        except Cita.DoesNotExist:
            return Response(
                {"error": "Cita no encontrada."},
                status=status.HTTP_404_NOT_FOUND,
            )

        serializer = AgendarCitaSerializer(cita, data=request.data, partial=False)
        if serializer.is_valid():
            serializer.save()

            # HU-03: enviar correo de confirmación — si falla, revertir la cita a LIBRE
            enviado = enviar_correo_confirmacion(cita)

            if not enviado:
                _liberar_cita(cita)
                return Response(
                    {
                        "error": "No pudimos enviar el correo de confirmación. "
                        "Por favor verifica tu correo e intenta de nuevo."
                    },
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR,
                )

            return Response(
                {
                    "mensaje": "Cita agendada correctamente.",
                    "cita_id": cita.id,
                    "correo_enviado": True,
                },
                status=status.HTTP_200_OK,
            )

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class CitaPorPlacaView(APIView):
    """GET /api/scheduling/cita-por-placa/?placa=IGK80F"""

    permission_classes = [AllowAny]

    def get(self, request):
        placa = _normalizar_placa(request.query_params.get("placa", ""))

        if not placa:
            return Response(
                {"error": "La placa es requerida."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if not re.match(r"^[A-Z]{3}\d{2}[A-Z]$", placa):
            return Response(
                {"error": "Formato de placa inválido. Ejemplo: IGK80F"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        citas = (
            Cita.objects.filter(
                placa_moto=placa,
                estado=Cita.Estado.ASIGNADA,
                fecha__gte=date.today(),
            )
            .select_related("local", "local__sede")
            .order_by("fecha", "hora_inicio")
        )

        serializer = CitaParaCancelarSerializer(citas, many=True)
        return Response(serializer.data)


class CancelarCitaView(APIView):
    """POST /api/scheduling/cancelar/<cita_id>/"""

    permission_classes = [AllowAny]

    def post(self, request, cita_id):
        try:
            cita = Cita.objects.select_related("local").get(pk=cita_id)
        except Cita.DoesNotExist:
            return Response(
                {"error": "Cita no encontrada."},
                status=status.HTTP_404_NOT_FOUND,
            )

        placa = _normalizar_placa(request.data.get("placa_moto", ""))

        if not placa:
            return Response(
                {"error": "La placa es requerida para cancelar."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if cita.estado != Cita.Estado.ASIGNADA:
            return Response(
                {"error": "Esta cita no está agendada o ya fue cancelada."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if cita.placa_moto != placa:
            return Response(
                {"error": "La placa no coincide con la cita."},
                status=status.HTTP_403_FORBIDDEN,
            )

        # Regla: solo se puede cancelar con mínimo 24 horas de anticipación
        fecha_hora_cita = datetime.combine(cita.fecha, cita.hora_inicio)
        fecha_hora_cita = timezone.make_aware(
            fecha_hora_cita,
            timezone.get_current_timezone(),
        )

        if fecha_hora_cita - timezone.now() < timedelta(hours=24):
            return Response(
                {"error": "Solo se puede cancelar con mínimo 24 horas de anticipación."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # 1. Cambiar temporalmente a CANCELADA para notificar correctamente
        cita.estado = Cita.Estado.CANCELADA
        cita.save(update_fields=["estado"])

        # 2. Enviar correo al administrador con la cita marcada como cancelada
        enviar_correo_cancelacion_admin(cita)

        # 3. Liberar el slot para que vuelva a quedar disponible
        _liberar_cita(cita)

        return Response(
            {"mensaje": "Cita cancelada. El horario volvió a quedar disponible."},
            status=status.HTTP_200_OK,
        )