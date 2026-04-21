# catalog/views.py

from rest_framework import status
from rest_framework.parsers import FormParser, JSONParser, MultiPartParser
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from catalog.models import CotizacionMotocicleta, Motocicleta
from catalog.serializers import (
    CotizacionMotocicletaResponseSerializer,
    CotizarMotocicletaSerializer,
    MotocicletaEstadoSerializer,
    MotocicletaListSerializer,
    MotocicletaSerializer,
)
from catalog.services import (
    calcular_desglose_cotizacion,
    construir_enlace_whatsapp,
    enviar_cotizacion_por_correo,
    generar_radicado_cotizacion,
)


class AgregarMotocicletaView(APIView):
    """POST /api/catalog/motocicletas/agregar/ - HU-13"""

    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser, JSONParser]

    def post(self, request):
        serializer = MotocicletaSerializer(data=request.data)
        if serializer.is_valid():
            motocicleta = serializer.save(activa=True)
            return Response(
                {
                    "mensaje": "Motocicleta agregada al catalogo correctamente.",
                    "id": motocicleta.id,
                },
                status=status.HTTP_201_CREATED,
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class CotizarMotocicletaView(APIView):
    """POST /api/catalog/cotizaciones/motocicletas/ - HU-10"""

    permission_classes = [AllowAny]

    def post(self, request):
        serializer = CotizarMotocicletaSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        motocicleta = serializer.context["motocicleta"]
        local = serializer.context.get("local")
        desglose = calcular_desglose_cotizacion(motocicleta.precio)
        radicado = generar_radicado_cotizacion()

        cotizacion = CotizacionMotocicleta.objects.create(
            usuario=request.user if request.user.is_authenticated else None,
            motocicleta=motocicleta,
            local=local,
            radicado=radicado,
            precio_base=desglose["precio_base"],
            impuestos_estimados=desglose["impuestos_estimados"],
            tramites_estimados=desglose["tramites_estimados"],
            total_estimado=desglose["total_estimado"],
            cliente_nombre=serializer.validated_data.get("cliente_nombre", ""),
            cliente_correo=serializer.validated_data.get("cliente_correo", ""),
            cliente_telefono=serializer.validated_data.get("cliente_telefono", ""),
            comentario=serializer.validated_data.get("comentario", ""),
        )

        correo_enviado = enviar_cotizacion_por_correo(cotizacion)
        whatsapp_url = construir_enlace_whatsapp(
            local.telefono if local else "",
            cotizacion.radicado,
            f"{motocicleta.marca} {motocicleta.referencia} {motocicleta.anio}",
            cotizacion.total_estimado,
        )

        response_data = CotizacionMotocicletaResponseSerializer(cotizacion).data
        response_data["whatsapp_url"] = whatsapp_url
        response_data["correo_cotizacion_enviado"] = correo_enviado
        return Response(response_data, status=status.HTTP_201_CREATED)


class EditarMotocicletaView(APIView):
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser, JSONParser]

    def _get_motocicleta(self, pk):
        try:
            return Motocicleta.objects.get(pk=pk)
        except Motocicleta.DoesNotExist:
            return None

    def get(self, request, pk):
        moto = self._get_motocicleta(pk)
        if moto is None:
            return Response(
                {"error": "Motocicleta no encontrada."},
                status=status.HTTP_404_NOT_FOUND,
            )
        serializer = MotocicletaSerializer(moto, context={"request": request})
        data = dict(serializer.data)
        if moto.imagen:
            data["imagen"] = request.build_absolute_uri(moto.imagen.url)
        return Response(data, status=status.HTTP_200_OK)

    def put(self, request, pk):
        moto = self._get_motocicleta(pk)
        if moto is None:
            return Response(
                {"error": "Motocicleta no encontrada."},
                status=status.HTTP_404_NOT_FOUND,
            )
        tiene_imagen_nueva = "imagen" in request.FILES
        serializer = MotocicletaSerializer(
            moto,
            data=request.data,
            partial=not tiene_imagen_nueva,
            context={"request": request},
        )
        if serializer.is_valid():
            serializer.save()
            return Response(
                {
                    "mensaje": "Motocicleta actualizada correctamente.",
                    "motocicleta": serializer.data,
                },
                status=status.HTTP_200_OK,
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def patch(self, request, pk):
        moto = self._get_motocicleta(pk)
        if moto is None:
            return Response(
                {"error": "Motocicleta no encontrada."},
                status=status.HTTP_404_NOT_FOUND,
            )
        serializer = MotocicletaSerializer(
            moto,
            data=request.data,
            partial=True,
            context={"request": request},
        )
        if serializer.is_valid():
            serializer.save()
            return Response(
                {
                    "mensaje": "Motocicleta actualizada correctamente.",
                    "motocicleta": serializer.data,
                },
                status=status.HTTP_200_OK,
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class CatalogoMotocicletasView(APIView):
    """GET /api/catalog/motocicletas/ - HU-11 + HU-12"""

    permission_classes = [AllowAny]

    def get(self, request):
        motos = Motocicleta.objects.filter(activa=True).order_by("id")

        referencia = request.query_params.get("referencia", "").strip()
        tipo = request.query_params.get("tipo", "").strip().upper()
        cilindraje_min = request.query_params.get("cilindraje_min", "").strip()
        cilindraje_max = request.query_params.get("cilindraje_max", "").strip()

        if referencia:
            motos = motos.filter(referencia__icontains=referencia)

        if tipo:
            tipos_validos = [opcion[0] for opcion in Motocicleta.TipoMotocicleta.choices]
            if tipo not in tipos_validos:
                return Response([], status=status.HTTP_200_OK)
            motos = motos.filter(tipo=tipo)

        if cilindraje_min.isdigit():
            motos = motos.filter(cilindraje__gte=int(cilindraje_min))

        if cilindraje_max.isdigit():
            motos = motos.filter(cilindraje__lte=int(cilindraje_max))

        serializer = MotocicletaListSerializer(motos, many=True, context={"request": request})
        return Response(serializer.data, status=status.HTTP_200_OK)


class DesactivarMotocicletaView(APIView):
    permission_classes = [IsAuthenticated]

    def _get_motocicleta(self, pk):
        try:
            return Motocicleta.objects.get(pk=pk)
        except Motocicleta.DoesNotExist:
            return None

    def patch(self, request, pk):
        moto = self._get_motocicleta(pk)
        if moto is None:
            return Response(
                {"error": "Motocicleta no encontrada."},
                status=status.HTTP_404_NOT_FOUND,
            )
        if not moto.activa:
            return Response(
                {"error": "La motocicleta ya se encuentra inactiva."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        moto.activa = False
        moto.save(update_fields=["activa"])
        serializer = MotocicletaEstadoSerializer(moto)
        return Response(
            {
                "mensaje": "Motocicleta desactivada correctamente.",
                "motocicleta": serializer.data,
            },
            status=status.HTTP_200_OK,
        )


class ActivarMotocicletaView(APIView):
    permission_classes = [IsAuthenticated]

    def _get_motocicleta(self, pk):
        try:
            return Motocicleta.objects.get(pk=pk)
        except Motocicleta.DoesNotExist:
            return None

    def patch(self, request, pk):
        moto = self._get_motocicleta(pk)
        if moto is None:
            return Response(
                {"error": "Motocicleta no encontrada."},
                status=status.HTTP_404_NOT_FOUND,
            )
        if moto.activa:
            return Response(
                {"error": "La motocicleta ya se encuentra activa."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        moto.activa = True
        moto.save(update_fields=["activa"])
        serializer = MotocicletaEstadoSerializer(moto)
        return Response(
            {
                "mensaje": "Motocicleta activada correctamente.",
                "motocicleta": serializer.data,
            },
            status=status.HTTP_200_OK,
        )


class ListadoAdminMotocicletasView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        motos = Motocicleta.objects.all().order_by("id")
        serializer = MotocicletaListSerializer(motos, many=True, context={"request": request})
        return Response(serializer.data, status=status.HTTP_200_OK)
