#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para actualizar la base de datos SQLite3 con encoding UTF-8 correcto.
"""
import sqlite3

# Conectar a la base de datos
db_path = 'db.sqlite3'
conn = sqlite3.connect(db_path)
conn.execute('PRAGMA encoding="UTF-8"')
cursor = conn.cursor()

# Limpiar datos
cursor.execute('DELETE FROM core_sede')
cursor.execute('DELETE FROM core_municipio')

# Insertar municipios
municipios = [
    ('Bogotá', 'Cundinamarca'),
    ('Medellín', 'Antioquia'),
    ('Apartadó', 'Antioquia'),
    ('Cali', 'Valle del Cauca'),
]

for nombre, depto in municipios:
    cursor.execute('INSERT INTO core_municipio (nombre, departamento) VALUES (?, ?)', (nombre, depto))

conn.commit()

# Obtener IDs de municipios
municipio_ids = {}
cursor.execute('SELECT id, nombre FROM core_municipio')
for mid, nombre in cursor.fetchall():
    municipio_ids[nombre] = mid

# Insertar sedes
sedes = [
    (municipio_ids['Bogotá'], 'Sede Bogotá - Zona Centro', 'Carrera 7 # 32-45, Bogotá', 4.7110, -74.0721),
    (municipio_ids['Bogotá'], 'Sede Bogotá - Zona Occidente', 'Calle 26 # 68-90, Bogotá', 4.7200, -74.1500),
    (municipio_ids['Medellín'], 'Sede Medellín - Centro', 'Carrera 49 # 52-36, Medellín', 6.2443, -75.5812),
    (municipio_ids['Apartadó'], 'Sede Apartadó', 'Calle Principal # 10-30, Apartadó', 7.8136, -76.6275),
    (municipio_ids['Cali'], 'Sede Cali', 'Avenida 6N # 15-45, Cali', 3.4372, -76.5225),
]

for mid, nombre, direccion, lat, lng in sedes:
    cursor.execute(
        'INSERT INTO core_sede (nombre, direccion, municipio_id, lat, lng, activa) VALUES (?, ?, ?, ?, ?, 1)',
        (nombre, direccion, mid, lat, lng)
    )

conn.commit()
print('✓ Base de datos actualizada correctamente')
conn.close()
