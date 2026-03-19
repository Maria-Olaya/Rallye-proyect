# scheduling/views.py

from datetime import date

from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from core.models import Local
from scheduling.models import Cita
from scheduling.serializers import AgendarCitaSerializer, CitaDisponibleSerializer
from scheduling.services import enviar_correo_confirmacion, generar_citas_para_local


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
            return Response({"error": "Local o fecha inválidos."}, status=status.HTTP_400_BAD_REQUEST)

        # Genera los slots del día si aún no existen
        generar_citas_para_local(local, fecha)

        citas = Cita.objects.filter(local=local, fecha=fecha, estado=Cita.Estado.LIBRE)
        serializer = CitaDisponibleSerializer(citas, many=True)
        return Response(serializer.data)


class AgendarCitaView(APIView):
    """PATCH /api/scheduling/agendar/<cita_id>/"""

    permission_classes = [AllowAny]

    def patch(self, request, cita_id):
        try:
            cita = Cita.objects.get(pk=cita_id)
        except Cita.DoesNotExist:
            return Response({"error": "Cita no encontrada."}, status=status.HTTP_404_NOT_FOUND)

        serializer = AgendarCitaSerializer(cita, data=request.data, partial=False)
        if serializer.is_valid():
            serializer.save()

            # HU-03: enviar correo de confirmación — si falla, revertir la cita a LIBRE
            enviado = enviar_correo_confirmacion(cita)

            if not enviado:
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
