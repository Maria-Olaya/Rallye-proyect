from django.contrib import admin
from django.urls import path, include
from django.views.generic import TemplateView

urlpatterns = [
    # ✅ FRONT (como tus pantallas)
    path("", TemplateView.as_view(template_name="home.html"), name="home"),
    path("sedes/", TemplateView.as_view(template_name="public/sedes.html"), name="sedes"),
    path("motos/", TemplateView.as_view(template_name="public/motos.html"), name="motos"),
    path("repuestos/", TemplateView.as_view(template_name="public/repuestos.html"), name="repuestos"),

    # Login admin (tu pantalla roja)
    path("login/", TemplateView.as_view(template_name="login.html"), name="login"),

    # Panel admin (tus pantallas internas)
    path("panel/", TemplateView.as_view(template_name="admin_panel/dashboard.html"), name="panel_dashboard"),
    path("panel/disponibilidad/", TemplateView.as_view(template_name="admin_panel/disponibilidad.html"), name="panel_disponibilidad"),
    path("panel/agenda/", TemplateView.as_view(template_name="admin_panel/agenda.html"), name="panel_agenda"),
    path("panel/diagnostico/", TemplateView.as_view(template_name="admin_panel/diagnostico.html"), name="panel_diagnostico"),
    path("panel/graficos/", TemplateView.as_view(template_name="admin_panel/graficos.html"), name="panel_graficos"),
    path("panel/motocicletas/", TemplateView.as_view(template_name="admin_panel/crud_motocicleta.html"), name="panel_motos_crud"),

    # Django admin (opcional)
    path("admin/", admin.site.urls),

    # ✅ API (tu arquitectura por apps)
    path("api/core/", include("core.urls")),
    path("api/users/", include("users.urls")),
    path("api/scheduling/", include("scheduling.urls")),
    path("api/diagnostics/", include("diagnostics.urls")),
    path("api/catalog/", include("catalog.urls")),
]