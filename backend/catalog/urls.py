# catalog/urls.py

from django.urls import path
from catalog.views import AgregarMotocicletaView, CatalogoMotocicletasView

urlpatterns = [
    path("motocicletas/agregar/", AgregarMotocicletaView.as_view(), name="agregar_moto"),
    path("motocicletas/", CatalogoMotocicletasView.as_view(), name="catalogo_motos"),
]