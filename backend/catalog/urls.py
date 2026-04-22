# catalog/urls.py
 
from django.urls import path
 
from catalog.views import (
    ActivarMotocicletaView,
    AgregarMotocicletaView,
    AniosModeloView,
    CatalogoMotocicletasView,
    CotizarMotocicletaView,
    DesactivarMotocicletaView,
    EditarMotocicletaView,
    ListadoAdminMotocicletasView,
    ModelosMotoView,
    RegistrarConsultaRepuestoView,
)
 
urlpatterns = [
  
    path("cotizaciones/motocicletas/", CotizarMotocicletaView.as_view(), name="cotizar_moto"),
 
   
    path("motocicletas/agregar/",             AgregarMotocicletaView.as_view(),       name="agregar_moto"),
    path("motocicletas/admin/",               ListadoAdminMotocicletasView.as_view(), name="admin_motos"),
    path("motocicletas/<int:pk>/editar/",     EditarMotocicletaView.as_view(),        name="editar_moto"),
    path("motocicletas/<int:pk>/desactivar/", DesactivarMotocicletaView.as_view(),    name="desactivar_moto"),
    path("motocicletas/<int:pk>/activar/",    ActivarMotocicletaView.as_view(),       name="activar_moto"),
    path("motocicletas/",                     CatalogoMotocicletasView.as_view(),     name="catalogo_motos"),
 
 
    path("repuestos/modelos/",                        ModelosMotoView.as_view(),               name="modelos_moto"),
    path("repuestos/modelos/<str:referencia>/anios/", AniosModeloView.as_view(),               name="anios_modelo"),
    path("repuestos/consulta/",                       RegistrarConsultaRepuestoView.as_view(), name="consulta_repuesto"),
]