# core/admin.py
from django.contrib import admin
from core.models import Municipio, Sede, Local

admin.site.register(Municipio)
admin.site.register(Sede)
admin.site.register(Local)
