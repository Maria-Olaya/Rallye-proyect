# catalog/admin.py

from django.contrib import admin
from catalog.models import Motocicleta, Repuesto, InteresRepuesto, CotizacionMotocicleta

admin.site.register(Motocicleta)
admin.site.register(Repuesto)
admin.site.register(InteresRepuesto)
admin.site.register(CotizacionMotocicleta)
