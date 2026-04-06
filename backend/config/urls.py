from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path, include
from django.views.generic import TemplateView

urlpatterns = [
    path("", TemplateView.as_view(template_name="home.html"), name="home"),
    path("sedes/", TemplateView.as_view(template_name="public/sedes.html"), name="sedes"),
    path("motos/", TemplateView.as_view(template_name="public/motos.html"), name="motos"),
    path(
        "repuestos/",
        TemplateView.as_view(template_name="public/repuestos.html"),
        name="repuestos",
    ),
    path("agendamientos/", TemplateView.as_view(template_name="public/agendamientos.html"), name="agendamientos"),
    path(
        "cancelar-cita/",
        TemplateView.as_view(template_name="public/cancelar_cita.html"),
        name="cancelar_cita",
    ),
    path("login/", TemplateView.as_view(template_name="login.html"), name="login"),
    path(
        "panel/",
        TemplateView.as_view(template_name="admin_panel/dashboard.html"),
        name="panel_dashboard",
    ),
    path(
        "panel/disponibilidad/",
        TemplateView.as_view(template_name="admin_panel/disponibilidad.html"),
        name="panel_disponibilidad",
    ),
    path(
        "panel/agenda/",
        TemplateView.as_view(template_name="admin_panel/agenda.html"),
        name="panel_agenda",
    ),
    path(
        "panel/diagnostico/",
        TemplateView.as_view(template_name="admin_panel/diagnostico.html"),
        name="panel_diagnostico",
    ),
    path(
        "panel/graficos/",
        TemplateView.as_view(template_name="admin_panel/graficos.html"),
        name="panel_graficos",
    ),
    path(
        "panel/motocicletas/",
        TemplateView.as_view(template_name="admin_panel/crud_motocicleta.html"),
        name="panel_motos_crud",
    ),
    path(
        "panel/motocicletas/agregar/",
        TemplateView.as_view(template_name="admin_panel/agregar_motocicleta.html"),
        name="panel_agregar_moto",
    ),
    path(
        "panel/motocicletas/<int:pk>/editar/",
        TemplateView.as_view(template_name="admin_panel/editar_motocicleta.html"),
        name="panel_editar_moto",
    ),
    path("admin/", admin.site.urls),
    path("api/core/", include("core.urls")),
    path("api/users/", include("users.urls")),
    path("api/scheduling/", include("scheduling.urls")),
    path("api/diagnostics/", include("diagnostics.urls")),
    path("api/catalog/", include("catalog.urls")),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
