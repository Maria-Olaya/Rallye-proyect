"""
Script para corregir la ortografía de municipios y sedes.
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from core.models import Municipio, Sede

# Correcciones de municipios con tildes correctas
municipios_correcciones = {
    'Bogotá': 'Bogotá',
    'Medellín': 'Medellín',
    'Apartadó': 'Apartadó',
    'Cali': 'Cali',
}

sedes_correcciones = {
    'Sede Bogotá - Zona Centro': 'Sede Bogotá - Zona Centro',
    'Sede Bogotá - Zona Occidente': 'Sede Bogotá - Zona Occidente',
    'Sede Medellín - Centro': 'Sede Medellín - Centro',
    'Sede Apartadó': 'Sede Apartadó',
    'Sede Cali': 'Sede Cali',
}

# Actualizar municipios
for old_nombre, new_nombre in municipios_correcciones.items():
    municipios = Municipio.objects.filter(nombre=old_nombre)
    for m in municipios:
        m.nombre = new_nombre
        m.save()
        print(f"✓ Municipio actualizado: {new_nombre}")

# Actualizar sedes
for old_nombre, new_nombre in sedes_correcciones.items():
    sedes = Sede.objects.filter(nombre=old_nombre)
    for s in sedes:
        s.nombre = new_nombre
        s.save()
        print(f"✓ Sede actualizada: {new_nombre}")

print("\n✓ Ortografía corregida")
