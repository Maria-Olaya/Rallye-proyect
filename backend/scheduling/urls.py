from django.urls import path
from scheduling.views import AgendarCitaView, CitasDisponiblesView

urlpatterns = [
    path("disponibles/", CitasDisponiblesView.as_view(), name="citas-disponibles"),
    path("agendar/<int:cita_id>/", AgendarCitaView.as_view(), name="agendar-cita"),
]