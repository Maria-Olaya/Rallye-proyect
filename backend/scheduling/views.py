# Create your views here.
from datetime import date
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView
from scheduling.models import Cita
from scheduling.serializers import AgendarCitaSerializer, CitaDisponibleSerializer
from scheduling.services import generar_citas_para_local
from core.models import Local


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
            return Response(
                {"mensaje": "Cita agendada correctamente.", "cita_id": cita.id},
                status=status.HTTP_200_OK,
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)