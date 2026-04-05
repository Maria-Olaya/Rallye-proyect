# catalog/views.py

from rest_framework import status
from rest_framework.parsers import FormParser, JSONParser, MultiPartParser
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from catalog.models import Motocicleta
from catalog.serializers import MotocicletaSerializer, MotocicletaListSerializer


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
    """GET /api/catalog/motocicletas/ — HU-11"""

    permission_classes = [AllowAny]

    def get(self, request):
        motos = Motocicleta.objects.filter(activa=True).order_by("id")
        serializer = MotocicletaListSerializer(motos, many=True, context={"request": request})
        return Response(serializer.data, status=status.HTTP_200_OK)
