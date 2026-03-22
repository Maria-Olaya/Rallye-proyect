# Create your views here.
from rest_framework.permissions import AllowAny
from rest_framework.viewsets import ReadOnlyModelViewSet
from core.models import Local, Sede
from core.serializers import LocalSerializer, SedeSerializer


class SedeViewSet(ReadOnlyModelViewSet):
    queryset = Sede.objects.filter(activa=True).prefetch_related("locales")
    serializer_class = SedeSerializer
    permission_classes = [AllowAny]


class LocalViewSet(ReadOnlyModelViewSet):
    queryset = Local.objects.filter(activo=True).select_related("sede")
    serializer_class = LocalSerializer
    permission_classes = [AllowAny]
