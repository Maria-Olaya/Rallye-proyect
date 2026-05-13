"""
Script para agregar datos de prueba a la base de datos.
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from core.models import Municipio, Sede

# Crear municipios y sedes de prueba
municipios_sedes = [
    {
        'municipio': 'Bogotá',
        'departamento': 'Cundinamarca',
        'sedes': [
            {
                'nombre': 'Sede Bogotá - Zona Centro',
                'direccion': 'Carrera 7 # 32-45, Bogotá',
                'lat': 4.7110,
                'lng': -74.0721,
            },
            {
                'nombre': 'Sede Bogotá - Zona Occidente',
                'direccion': 'Calle 26 # 68-90, Bogotá',
                'lat': 4.7200,
                'lng': -74.1500,
            }
        ]
    },
    {
        'municipio': 'Medellín',
        'departamento': 'Antioquia',
        'sedes': [
            {
                'nombre': 'Sede Medellín - Centro',
                'direccion': 'Carrera 49 # 52-36, Medellín',
                'lat': 6.2443,
                'lng': -75.5812,
            }
        ]
    },
    {
        'municipio': 'Apartadó',
        'departamento': 'Antioquia',
        'sedes': [
            {
                'nombre': 'Sede Apartadó',
                'direccion': 'Calle Principal # 10-30, Apartadó',
                'lat': 7.8136,
                'lng': -76.6275,
            }
        ]
    },
    {
        'municipio': 'Cali',
        'departamento': 'Valle del Cauca',
        'sedes': [
            {
                'nombre': 'Sede Cali',
                'direccion': 'Avenida 6N # 15-45, Cali',
                'lat': 3.4372,
                'lng': -76.5225,
            }
        ]
    },
]

for mun_data in municipios_sedes:
    municipio, created = Municipio.objects.get_or_create(
        nombre=mun_data['municipio'],
        departamento=mun_data['departamento']
    )
    
    for sede_data in mun_data['sedes']:
        sede, created = Sede.objects.get_or_create(
            nombre=sede_data['nombre'],
            municipio=municipio,
            defaults={
                'direccion': sede_data['direccion'],
                'lat': sede_data['lat'],
                'lng': sede_data['lng'],
                'activa': True,
            }
        )
        if created:
            print(f"✓ Sede creada: {sede.nombre}")
        else:
            print(f"✓ Sede existente: {sede.nombre}")

print("\n✓ Datos de prueba agregados correctamente")
