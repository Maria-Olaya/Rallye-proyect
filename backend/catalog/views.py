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


class CatalogoMotocicletasView(APIView):
    """GET /api/catalog/motocicletas/ — HU-11 + HU-12

    Filtros opcionales (query params):
        ?referencia=FZ        → búsqueda parcial, insensible a mayúsculas
        ?tipo=DEPORTIVA       → filtro exacto por tipo
        ?cilindraje_min=150   → cilindraje mayor o igual
        ?cilindraje_max=650   → cilindraje menor o igual
    """

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
