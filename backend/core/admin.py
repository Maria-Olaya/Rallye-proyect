# core/admin.py

from django.contrib import admin
from core.models import Local, Municipio, Sede


@admin.register(Municipio)
class MunicipioAdmin(admin.ModelAdmin):
    list_display = ["nombre", "departamento"]
    search_fields = ["nombre", "departamento"]


@admin.register(Sede)
class SedeAdmin(admin.ModelAdmin):
    list_display = ["nombre", "municipio", "activa"]
    list_filter = ["activa", "municipio__departamento"]
    search_fields = ["nombre"]


@admin.register(Local)
class LocalAdmin(admin.ModelAdmin):
    list_display = ["nombre", "sede", "telefono", "tiene_comercio", "tiene_taller", "activo"]
    list_filter = ["activo", "tiene_comercio", "tiene_taller", "sede"]
    search_fields = ["nombre", "direccion", "telefono"]
    fieldsets = (
        ("Información general", {
            "fields": ("nombre", "sede", "direccion", "telefono", "correo_admin", "descripcion")
        }),
        ("Servicios", {
            "fields": ("tiene_comercio", "tiene_taller", "num_mecanicos"),
            "description": "Indica qué servicios ofrece este local.",
        }),
        ("Horarios y estado", {
            "fields": ("horarios", "activo"),
        }),
    )