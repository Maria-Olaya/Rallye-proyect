from django.urls import path
from scheduling.views import (
    AgendarCitaView,
    CancelarCitaView,
    CitasDisponiblesView,
    CitaPorPlacaView,
)

urlpatterns = [
    path("disponibles/", CitasDisponiblesView.as_view(), name="citas-disponibles"),
    path("agendar/<int:cita_id>/", AgendarCitaView.as_view(), name="agendar-cita"),
    path("cita-por-placa/", CitaPorPlacaView.as_view(), name="cita-por-placa"),
    path("cancelar/<int:cita_id>/", CancelarCitaView.as_view(), name="cancelar-cita"),
]
