from rest_framework.routers import DefaultRouter
from django.urls import path
from core.views import SedeViewSet, LocalViewSet, LocalUpdateView, mapa_sedes

router = DefaultRouter()
router.register("sedes", SedeViewSet, basename="sede")
router.register("locales", LocalViewSet, basename="local")

urlpatterns = router.urls + [
    path("locales/<int:pk>/editar/", LocalUpdateView.as_view(), name="local-update"),
    path("mapa/", mapa_sedes, name="mapa-sedes"),
]
