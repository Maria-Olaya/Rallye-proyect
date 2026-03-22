from django.urls import path

from diagnostics.views import DiagnosticoCreateView, DiagnosticoLookupByPlacaView

urlpatterns = [
    path("buscar-cita/", DiagnosticoLookupByPlacaView.as_view(), name="diagnostics_lookup_by_placa"),
    path("", DiagnosticoCreateView.as_view(), name="diagnostics_create"),
]
