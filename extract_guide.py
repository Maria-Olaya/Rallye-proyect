#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import zipfile
import xml.etree.ElementTree as ET

# Abrir el docx
with zipfile.ZipFile('Guia_Desarrollo_Equipo_RallyeMotors.docx', 'r') as zip_ref:
    # Leer el documento.xml
    xml_content = zip_ref.read('word/document.xml').decode('utf-8')

# Parse XML
root = ET.fromstring(xml_content)

# Extraer textos
ns = {'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'}
texts = []
for t in root.findall('.//w:t', ns):
    if t.text:
        texts.append(t.text)

# Mostrar contenido
print('\n'.join(texts))
