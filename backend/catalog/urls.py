# catalog/urls.py

from django.urls import path
from catalog.views import AgregarMotocicletaView, CatalogoMotocicletasView, EditarMotocicletaView

urlpatterns = [
    path("motocicletas/agregar/", AgregarMotocicletaView.as_view(), name="agregar_moto"),
    path("motocicletas/<int:pk>/editar/", EditarMotocicletaView.as_view(), name="editar_moto"),
    path("motocicletas/", CatalogoMotocicletasView.as_view(), name="catalogo_motos"),
]
