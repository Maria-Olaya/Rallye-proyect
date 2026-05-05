# core/admin.py
from django.contrib import admin

from core.models import Local, Municipio, Sede

admin.site.register(Municipio)
admin.site.register(Sede)


@admin.register(Local)
class LocalAdmin(admin.ModelAdmin):
    list_display = ("nombre", "sede", "correo_admin", "num_mecanicos", "activo")
    list_filter = ("activo", "sede")
    search_fields = ("nombre", "correo_admin")

    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)

        from users.models import User

        if obj.correo_admin:
            User.objects.filter(email=obj.correo_admin).update(local=obj)
