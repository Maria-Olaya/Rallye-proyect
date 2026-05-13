"""
Script para agregar coordenadas geográficas a las sedes si no existen.
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from core.models import Sede

# Coordenadas aproximadas de algunas ciudades/municipios en Colombia
COORDENADAS = {
    'Bogotá': {'lat': 4.7110, 'lng': -74.0721},
    'Medellín': {'lat': 6.2443, 'lng': -75.5812},
    'Cali': {'lat': 3.4372, 'lng': -76.5225},
    'Barranquilla': {'lat': 10.9639, 'lng': -74.7964},
    'Cartagena': {'lat': 10.3932, 'lng': -75.4891},
    'Bucaramanga': {'lat': 7.1268, 'lng': -73.1229},
    'Cúcuta': {'lat': 7.8765, 'lng': -72.4472},
    'Pasto': {'lat': 1.2136, 'lng': -77.2811},
    'Pereira': {'lat': 4.8133, 'lng': -75.6969},
    'Santa Marta': {'lat': 11.2437, 'lng': -74.2267},
    'Apartadó': {'lat': 7.8136, 'lng': -76.6275},
    'Ibagué': {'lat': 4.4381, 'lng': -75.2345},
    'Armenia': {'lat': 4.5339, 'lng': -75.7314},
    'Manizales': {'lat': 5.0686, 'lng': -75.5159},
    'Villavicencio': {'lat': 4.1431, 'lng': -73.6253},
}

sedes = Sede.objects.all()
for sede in sedes:
    if not sede.lat or not sede.lng:
        municipio_nombre = sede.municipio.nombre if sede.municipio else sede.nombre
        coords = COORDENADAS.get(municipio_nombre)
        
        if coords:
            sede.lat = coords['lat']
            sede.lng = coords['lng']
            sede.save()
            print(f"✓ Coordenadas agregadas a {sede.nombre} ({municipio_nombre})")
        else:
            print(f"⚠ No se encontraron coordenadas para {municipio_nombre}")

print("\n✓ Script completado")
