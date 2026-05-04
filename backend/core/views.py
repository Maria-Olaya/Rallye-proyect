# core/views.py
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.viewsets import ReadOnlyModelViewSet
from core.models import Local, Sede
from core.serializers import LocalSerializer, LocalUpdateSerializer, SedeSerializer


class SedeViewSet(ReadOnlyModelViewSet):
    queryset = Sede.objects.filter(activa=True).prefetch_related("locales")
    serializer_class = SedeSerializer
    permission_classes = [AllowAny]


class LocalViewSet(ReadOnlyModelViewSet):
    queryset = Local.objects.filter(activo=True).select_related("sede")
    serializer_class = LocalSerializer
    permission_classes = [AllowAny]


class LocalUpdateView(APIView):
    """
    GET  /api/core/locales/<pk>/editar/  — obtener datos actuales del local
    PATCH /api/core/locales/<pk>/editar/ — actualizar información del local

    Solo el administrador autenticado asignado a ese local puede editarlo.
    """

    permission_classes = [IsAuthenticated]

    def _get_local(self, pk, user):
        """
        BUG FIX (HU-16): Local.administradores es el related_manager inverso
        de User.local (FK). Filtrar Local.objects.get(administradores=user)
        no funciona — genera DoesNotExist siempre.
        La verificación correcta: el usuario autenticado debe tener
        user.local_id == pk para poder editar ese local.
        """
        if user.local_id is None or user.local_id != pk:
            return None
        try:
            return Local.objects.get(pk=pk)
        except Local.DoesNotExist:
            return None

    def get(self, request, pk):
        local = self._get_local(pk, request.user)
        if local is None:
            return Response(
                {"error": "Local no encontrado o sin permisos."},
                status=status.HTTP_404_NOT_FOUND,
            )
        serializer = LocalUpdateSerializer(local)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def patch(self, request, pk):
        local = self._get_local(pk, request.user)
        if local is None:
            return Response(
                {"error": "Local no encontrado o sin permisos."},
                status=status.HTTP_404_NOT_FOUND,
            )
        serializer = LocalUpdateSerializer(local, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(
                {"mensaje": "Información del local actualizada correctamente."},
                status=status.HTTP_200_OK,
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
