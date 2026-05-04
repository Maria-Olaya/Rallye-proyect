# fix_template_js.py
from pathlib import Path

tmpl = Path("frontend/templates/admin_panel/editar_local.html")
text = tmpl.read_text(encoding="utf-8")

# 1. Corregir actualizarPreview: quitar referencias a hora_apertura, hora_cierre, pvHorario
OLD_PREVIEW = """    function actualizarPreview() {
        function v(id, fb) { var el = document.getElementById(id); return (el && el.value.trim()) || fb; }
        document.getElementById('pvNombre').textContent    = v('nombre', '\\u2014');
        document.getElementById('pvTelefono').textContent  = v('telefono', 'No especificado');
        document.getElementById('pvDireccion').textContent = v('direccion', 'No especificada');
        var desc = document.getElementById('descripcion');
        document.getElementById('pvDesc').textContent = (desc && desc.value.trim().substring(0,150)) || 'Sin descripci\\u00f3n';
        var ap = document.getElementById('hora_apertura');
        var ci = document.getElementById('hora_cierre');
        document.getElementById('pvHorario').textContent = (ap&&ap.value||'--:--') + ' \\u2014 ' + (ci&&ci.value||'--:--');
    }"""

NEW_PREVIEW = """    function actualizarPreview() {
        function v(id, fb) { var el = document.getElementById(id); return (el && el.value.trim()) || fb; }
        var elNombre = document.getElementById('pvNombre');
        if (elNombre) elNombre.textContent = v('nombre', '\\u2014');
        var elTel = document.getElementById('pvTelefono');
        if (elTel) elTel.textContent = v('telefono', 'No especificado');
        var elDir = document.getElementById('pvDireccion');
        if (elDir) elDir.textContent = v('direccion', 'No especificada');
        var desc = document.getElementById('descripcion');
        var elDesc = document.getElementById('pvDesc');
        if (elDesc) elDesc.textContent = (desc && desc.value.trim().substring(0,150)) || 'Sin descripci\\u00f3n';
        actualizarPreviewHorarios();
    }"""

# 2. Corregir payload en guardarCambios: quitar hora_apertura y hora_cierre
OLD_PAYLOAD = """        var payload = {
            telefono:      document.getElementById('telefono').value.trim(),
            correo_admin:  document.getElementById('correo_admin').value.trim(),
            direccion:     document.getElementById('direccion').value.trim(),
            descripcion:   document.getElementById('descripcion').value.trim(),
            hora_apertura: document.getElementById('hora_apertura').value,
            hora_cierre:   document.getElementById('hora_cierre').value,
            num_mecanicos: parseInt(document.getElementById('num_mecanicos').value, 10),
            activo:        activoVal,
            horarios:      getFranjas(),
        };"""

NEW_PAYLOAD = """        var payload = {
            telefono:      document.getElementById('telefono').value.trim(),
            correo_admin:  document.getElementById('correo_admin').value.trim(),
            direccion:     document.getElementById('direccion').value.trim(),
            descripcion:   document.getElementById('descripcion').value.trim(),
            num_mecanicos: parseInt(document.getElementById('num_mecanicos').value, 10),
            activo:        activoVal,
            horarios:      getFranjas(),
        };"""

# 3. Corregir cargarDatos: quitar setVal de hora_apertura y hora_cierre
OLD_SET = """            setVal('hora_apertura', d.hora_apertura);
            setVal('hora_cierre',   d.hora_cierre);
            setVal('num_mecanicos', d.num_mecanicos);"""

NEW_SET = """            setVal('num_mecanicos', d.num_mecanicos);"""

OK  = "\033[92m✔\033[0m"
ERR = "\033[91m✘\033[0m"

def patch(old, new, label):
    global text
    # Intentar coincidencia exacta primero
    if old in text:
        text = text.replace(old, new, 1)
        print(f"  {OK} {label}")
        return True
    # Intentar normalizando espacios en blanco
    import re
    old_norm = re.sub(r'\s+', ' ', old).strip()
    text_norm = re.sub(r'\s+', ' ', text)
    if old_norm in text_norm:
        # Reemplazar en el texto normalizado y reconstruir
        text = text_norm.replace(old_norm, re.sub(r'\s+', ' ', new).strip(), 1)
        print(f"  {OK} {label} (normalizado)")
        return True
    print(f"  {ERR} {label}: no encontrado")
    return False

print("\n→ Parcheando editar_local.html …")
patch(OLD_PREVIEW, NEW_PREVIEW, "actualizarPreview: quitar pvHorario/hora_apertura/hora_cierre")
patch(OLD_PAYLOAD, NEW_PAYLOAD, "guardarCambios payload: quitar hora_apertura/hora_cierre")
patch(OLD_SET, NEW_SET, "cargarDatos setVal: quitar hora_apertura/hora_cierre")

tmpl.write_text(text, encoding="utf-8")
print(f"  \033[92m✔\033[0m editar_local.html guardado")

print("\n\033[92m✔\033[0m Listo. Recarga el servidor y prueba el formulario.")