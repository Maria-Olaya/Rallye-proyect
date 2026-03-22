import re

from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from diagnostics.serializers import CitaAtendidaLookupSerializer, DiagnosticoCreateSerializer
from diagnostics.services import enviar_radicado_por_correo, generar_radicado
from scheduling.models import Cita
from scheduling.services import marcar_citas_atendidas


class DiagnosticoLookupByPlacaView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        # Actualiza citas vencidas a ATENDIDO antes de buscar
        marcar_citas_atendidas()

        placa = (request.query_params.get("placa") or "").strip().upper()
        if not placa:
            return Response({"error": "El parámetro placa es obligatorio."}, status=status.HTTP_400_BAD_REQUEST)

        if not re.match(r"^[A-Z]{3}\d{2}[A-Z]$", placa):
            return Response({"error": "Formato de placa inválido. Ejemplo: AXA39C"}, status=status.HTTP_400_BAD_REQUEST)

        citas = Cita.objects.select_related("local").filter(
            placa_moto=placa,
            estado=Cita.Estado.ATENDIDO,
        )

        if request.user.local_id:
            citas = citas.filter(local_id=request.user.local_id)

        cita = citas.exclude(diagnostico__isnull=False).order_by("-fecha", "-hora_inicio").first()
        if not cita:
            return Response(
                {"error": "No existe una cita atendida pendiente de diagnóstico para esa placa."},
                status=status.HTTP_404_NOT_FOUND,
            )

        return Response(CitaAtendidaLookupSerializer(cita).data)


class DiagnosticoCreateView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = DiagnosticoCreateSerializer(data=request.data, context={"request": request})
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        # HU-04: guarda el diagnóstico y genera el radicado
        diagnostico = serializer.save(radicado=generar_radicado())

        # HU-05: envía el PDF del radicado al correo del cliente
        correo_enviado = enviar_radicado_por_correo(diagnostico)

        return Response(
            {
                "id": diagnostico.id,
                "radicado": diagnostico.radicado,
                "fecha_registro": diagnostico.fecha_registro,
                "cita_id": diagnostico.cita_id,
                "correo_radicado_enviado": correo_enviado,
            },
            status=status.HTTP_201_CREATED,
        )
