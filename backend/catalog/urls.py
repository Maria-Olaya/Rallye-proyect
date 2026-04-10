# catalog/urls.py

from django.urls import path
from catalog.views import (
    AgregarMotocicletaView,
    ActivarMotocicletaView,
    CatalogoMotocicletasView,
    DesactivarMotocicletaView,
    EditarMotocicletaView,
    ListadoAdminMotocicletasView,
)

urlpatterns = [
    path("motocicletas/agregar/", AgregarMotocicletaView.as_view(), name="agregar_moto"),
    path("motocicletas/admin/", ListadoAdminMotocicletasView.as_view(), name="admin_motos"),
    path("motocicletas/<int:pk>/editar/", EditarMotocicletaView.as_view(), name="editar_moto"),
    path("motocicletas/<int:pk>/desactivar/", DesactivarMotocicletaView.as_view(), name="desactivar_moto"),
    path("motocicletas/<int:pk>/activar/", ActivarMotocicletaView.as_view(), name="activar_moto"),
    path("motocicletas/", CatalogoMotocicletasView.as_view(), name="catalogo_motos"),
]
