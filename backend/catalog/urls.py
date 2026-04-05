# catalog/urls.py

from django.urls import path
from catalog.views import AgregarMotocicletaView

urlpatterns = [
    path("motocicletas/agregar/", AgregarMotocicletaView.as_view(), name="agregar_moto"),
]
