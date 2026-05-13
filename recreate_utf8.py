#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para limpiar y recrear sedes con ortografía correcta.
"""
import os
import sys
import django

# Asegurar UTF-8
if sys.stdout.encoding != 'utf-8':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from core.models import Municipio, Sede

# Limpiar datos existentes
Sede.objects.all().delete()
Municipio.objects.all().delete()

# Datos con ortografía correcta
datos = [
    ('Bogotá', 'Cundinamarca', [
        ('Sede Bogotá - Zona Centro', 'Carrera 7 # 32-45, Bogotá', 4.7110, -74.0721),
        ('Sede Bogotá - Zona Occidente', 'Calle 26 # 68-90, Bogotá', 4.7200, -74.1500),
    ]),
    ('Medellín', 'Antioquia', [
        ('Sede Medellín - Centro', 'Carrera 49 # 52-36, Medellín', 6.2443, -75.5812),
    ]),
    ('Apartadó', 'Antioquia', [
        ('Sede Apartadó', 'Calle Principal # 10-30, Apartadó', 7.8136, -76.6275),
    ]),
    ('Cali', 'Valle del Cauca', [
        ('Sede Cali', 'Avenida 6N # 15-45, Cali', 3.4372, -76.5225),
    ]),
]

for municipio_nombre, depto, sedes in datos:
    municipio = Municipio.objects.create(
        nombre=municipio_nombre,
        departamento=depto
    )
    for sede_nombre, direccion, lat, lng in sedes:
        Sede.objects.create(
            nombre=sede_nombre,
            municipio=municipio,
            direccion=direccion,
            lat=lat,
            lng=lng,
            activa=True,
        )
        print(f"✓ {sede_nombre}")

print("\n✓ Datos recreados")
