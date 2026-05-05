from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from users.models import User


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    """
    Panel de administración para usuarios de Rallye Motor's.
    Los superusers crean administradores desde aquí.
    """

    list_display = ("username", "is_active", "is_staff", "is_superuser", "date_joined")
    list_filter = ("is_active", "is_staff", "is_superuser")
    search_fields = ("username",)
    ordering = ("-date_joined",)
