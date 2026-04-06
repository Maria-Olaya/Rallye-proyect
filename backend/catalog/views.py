# catalog/views.py

from rest_framework import status
from rest_framework.parsers import FormParser, JSONParser, MultiPartParser
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from catalog.models import Motocicleta
from catalog.serializers import MotocicletaListSerializer, MotocicletaSerializer


class AgregarMotocicletaView(APIView):
    """POST /api/catalog/motocicletas/agregar/ — HU-13"""

    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser, JSONParser]

    def post(self, request):
        serializer = MotocicletaSerializer(data=request.data)
        if serializer.is_valid():
            motocicleta = serializer.save(activa=True)
            return Response(
                {
                    "mensaje": "Motocicleta agregada al catálogo correctamente.",
                    "id": motocicleta.id,
                },
                status=status.HTTP_201_CREATED,
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# ── HU-14 ─────────────────────────────────────────────────────────────────────
class EditarMotocicletaView(APIView):
    """
    GET   /api/catalog/motocicletas/<pk>/editar/  — Carga datos actuales
    PUT   /api/catalog/motocicletas/<pk>/editar/  — Actualiza todos los campos
    PATCH /api/catalog/motocicletas/<pk>/editar/  — Actualiza campos parcialmente
    """

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
        serializer = MotocicletaSerializer(moto, data=request.data, partial=True, context={"request": request})
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


# ──────────────────────────────────────────────────────────────────────────────


class CatalogoMotocicletasView(APIView):
    """GET /api/catalog/motocicletas/ — HU-11 + HU-12"""

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
            tipos_validos = [t[0] for t in Motocicleta.TipoMotocicleta.choices]
            if tipo not in tipos_validos:
                return Response([], status=status.HTTP_200_OK)
            motos = motos.filter(tipo=tipo)

        if cilindraje_min.isdigit():
            motos = motos.filter(cilindraje__gte=int(cilindraje_min))

        if cilindraje_max.isdigit():
            motos = motos.filter(cilindraje__lte=int(cilindraje_max))

        serializer = MotocicletaListSerializer(motos, many=True, context={"request": request})
        return Response(serializer.data, status=status.HTTP_200_OK)
