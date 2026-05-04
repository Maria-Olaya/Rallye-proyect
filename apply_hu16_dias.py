"""
apply_hu16_dias.py
==================
Agrega campo `dias_atencion` (JSONField) al modelo Local.

Ejecutar desde la raíz del repo:
    python apply_hu16_dias.py

Qué hace:
  1. Parchea backend/core/models.py
  2. Parchea backend/core/serializers.py
  3. Crea la migración backend/core/migrations/0004_local_dias_atencion.py
  4. Parchea frontend/templates/admin_panel/editar_local.html
"""

from pathlib import Path

ROOT = Path(__file__).parent
BACKEND = ROOT / "backend"
FRONTEND = ROOT / "frontend"

OK = "\033[92m✔\033[0m"
ERR = "\033[91m✘\033[0m"
INF = "\033[94m→\033[0m"


def patch_file(path: Path, old: str, new: str, label: str):
    text = path.read_text(encoding="utf-8")
    if old not in text:
        print(f"  {ERR} {label}: fragmento no encontrado — ¿ya aplicado?")
        return False
    path.write_text(text.replace(old, new, 1), encoding="utf-8")
    print(f"  {OK} {label}")
    return True


# ──────────────────────────────────────────────────────────────────────────────
# 1. models.py
# ──────────────────────────────────────────────────────────────────────────────
print(f"\n{INF} Parcheando models.py …")
patch_file(
    BACKEND / "core" / "models.py",
    old="    activo = models.BooleanField(default=True)\n\n    def __str__(self):\n        return self.nombre",
    new=(
        "    activo = models.BooleanField(default=True)\n"
        "    dias_atencion = models.JSONField(\n"
        "        default=list,\n"
        "        blank=True,\n"
        "        help_text=\"Lista de días: ['lun','mar','mie','jue','vie','sab','dom']\",\n"
        "    )\n\n"
        "    def __str__(self):\n"
        "        return self.nombre"
    ),
    label="Local.dias_atencion añadido",
)

# ──────────────────────────────────────────────────────────────────────────────
# 2. serializers.py — LocalUpdateSerializer y LocalSerializer
# ──────────────────────────────────────────────────────────────────────────────
print(f"\n{INF} Parcheando serializers.py …")
ser_path = BACKEND / "core" / "serializers.py"

# LocalSerializer (vista pública): añadir dias_atencion
patch_file(
    ser_path,
    old='            "hora_apertura",\n            "hora_cierre",\n        ]',
    new='            "hora_apertura",\n            "hora_cierre",\n            "dias_atencion",\n        ]',
    label="LocalSerializer: dias_atencion en vista pública",
)

# LocalUpdateSerializer: añadir dias_atencion
patch_file(
    ser_path,
    old='            "activo",\n        ]\n        read_only_fields = ["nombre"]',
    new='            "activo",\n            "dias_atencion",\n        ]\n        read_only_fields = ["nombre"]',
    label="LocalUpdateSerializer: dias_atencion en edición",
)

# ──────────────────────────────────────────────────────────────────────────────
# 3. Migración
# ──────────────────────────────────────────────────────────────────────────────
print(f"\n{INF} Creando migración 0004 …")
mig_path = BACKEND / "core" / "migrations" / "0004_local_dias_atencion.py"
if mig_path.exists():
    print(f"  {ERR} La migración ya existe, se omite.")
else:
    mig_path.write_text(
        """\
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0003_alter_local_id_alter_municipio_id_alter_sede_id"),
    ]

    operations = [
        migrations.AddField(
            model_name="local",
            name="dias_atencion",
            field=models.JSONField(
                blank=True,
                default=list,
                help_text="Lista de días: ['lun','mar','mie','jue','vie','sab','dom']",
            ),
        ),
    ]
""",
        encoding="utf-8",
    )
    print(f"  {OK} 0004_local_dias_atencion.py creada")

# ──────────────────────────────────────────────────────────────────────────────
# 4. editar_local.html — sección checkboxes + JS
# ──────────────────────────────────────────────────────────────────────────────
print(f"\n{INF} Parcheando editar_local.html …")
tmpl_path = FRONTEND / "templates" / "admin_panel" / "editar_local.html"

# 4a. CSS para los checkboxes de días
CSS_OLD = "    .ml-preview-label { font-size:0.68rem;"
CSS_NEW = """\
    /* días de atención */
    .dias-grid { display:flex; gap:0.5rem; flex-wrap:wrap; }
    .dia-chip input[type=checkbox] { display:none; }
    .dia-chip label {
        display:inline-block; padding:0.45rem 0.9rem;
        border:1.5px solid #2d2d2d; border-radius:8px;
        font-family:'Barlow Condensed',sans-serif; font-size:0.85rem;
        font-weight:700; letter-spacing:0.08em; text-transform:uppercase;
        color:#666; background:#111; cursor:pointer; transition:all 0.15s;
        user-select:none;
    }
    .dia-chip input[type=checkbox]:checked + label {
        background:#cc0000; border-color:#cc0000; color:#fff;
    }
    .dia-chip label:hover { border-color:#cc0000; color:#ccc; }

    .ml-preview-label { font-size:0.68rem;"""

patch_file(tmpl_path, CSS_OLD, CSS_NEW, "CSS checkboxes días")

# 4b. HTML — insertar sección días antes de la sección horarios
SECTION_HORARIOS = '      <!-- Horarios -->\n      <div class="ml-card-section">'
DIAS_HTML = """\
      <!-- Días de atención -->
      <div class="ml-card-section">
        <div class="ml-section-title"><i class="fas fa-calendar-week"></i> Días de atención</div>
        <div class="dias-grid" id="diasGrid">
          <div class="dia-chip"><input type="checkbox" id="dia-lun" value="lun"><label for="dia-lun">Lun</label></div>
          <div class="dia-chip"><input type="checkbox" id="dia-mar" value="mar"><label for="dia-mar">Mar</label></div>
          <div class="dia-chip"><input type="checkbox" id="dia-mie" value="mie"><label for="dia-mie">Mié</label></div>
          <div class="dia-chip"><input type="checkbox" id="dia-jue" value="jue"><label for="dia-jue">Jue</label></div>
          <div class="dia-chip"><input type="checkbox" id="dia-vie" value="vie"><label for="dia-vie">Vie</label></div>
          <div class="dia-chip"><input type="checkbox" id="dia-sab" value="sab"><label for="dia-sab">Sáb</label></div>
          <div class="dia-chip"><input type="checkbox" id="dia-dom" value="dom"><label for="dia-dom">Dom</label></div>
        </div>
      </div>

"""
patch_file(
    tmpl_path, SECTION_HORARIOS, DIAS_HTML + SECTION_HORARIOS, "HTML sección días"
)

# 4c. Vista previa — agregar fila de días después de la fila del horario
PV_HORARIO_ROW = (
    '          <div class="ml-preview-row"><i class="fas fa-clock"></i>'
    '<span id="pvHorario">--:-- — --:--</span></div>'
)
PV_DIAS_ROW = (
    '          <div class="ml-preview-row"><i class="fas fa-calendar-week"></i>'
    '<span id="pvDias">Sin días configurados</span></div>'
)
patch_file(
    tmpl_path,
    PV_HORARIO_ROW,
    PV_HORARIO_ROW + "\n" + PV_DIAS_ROW,
    "Vista previa: fila días",
)

# 4d. JS — funciones de días (leer, escribir, preview)
JS_TOGGLE = "    window.toggleActivo = function() {"
JS_DIAS = """\
    function getDiasSeleccionados() {
        return Array.from(document.querySelectorAll('#diasGrid input[type=checkbox]:checked'))
            .map(function(cb){ return cb.value; });
    }

    function setDias(dias) {
        document.querySelectorAll('#diasGrid input[type=checkbox]').forEach(function(cb){
            cb.checked = Array.isArray(dias) && dias.includes(cb.value);
        });
    }

    var DIAS_LABEL = { lun:'Lun', mar:'Mar', mie:'Mié', jue:'Jue', vie:'Vie', sab:'Sáb', dom:'Dom' };

    function actualizarPreviewDias() {
        var dias = getDiasSeleccionados();
        var el = document.getElementById('pvDias');
        if (el) el.textContent = dias.length
            ? dias.map(function(d){ return DIAS_LABEL[d]||d; }).join(', ')
            : 'Sin días configurados';
    }

    window.toggleActivo = function() {"""

patch_file(tmpl_path, JS_TOGGLE, JS_DIAS, "JS funciones días")

# 4e. JS — cargarDatos: setDias tras cargar activo
JS_SYNC = "            activoVal = !!d.activo;\n            syncToggleUI();"
JS_SYNC_NEW = "            activoVal = !!d.activo;\n            syncToggleUI();\n            setDias(d.dias_atencion || []);\n            actualizarPreviewDias();"
patch_file(tmpl_path, JS_SYNC, JS_SYNC_NEW, "JS cargarDatos: setDias")

# 4f. JS — guardarCambios: incluir dias_atencion en payload
JS_PAYLOAD_ACTIVO = "            activo:        activoVal,"
JS_PAYLOAD_NEW = "            activo:        activoVal,\n            dias_atencion: getDiasSeleccionados(),"
patch_file(
    tmpl_path,
    JS_PAYLOAD_ACTIVO,
    JS_PAYLOAD_NEW,
    "JS guardarCambios: dias_atencion en payload",
)

# 4g. JS — actualizarPreview: llamar actualizarPreviewDias
JS_PREVIEW_CALL = "        document.getElementById('descripcion')?.addEventListener('input', function(){ actualizarContador(); actualizarPreview(); });"
JS_PREVIEW_NEW = "        document.getElementById('descripcion')?.addEventListener('input', function(){ actualizarContador(); actualizarPreview(); });\n        document.querySelectorAll('#diasGrid input[type=checkbox]').forEach(function(cb){\n            cb.addEventListener('change', actualizarPreviewDias);\n        });"
patch_file(tmpl_path, JS_PREVIEW_CALL, JS_PREVIEW_NEW, "JS listeners checkboxes días")

# ──────────────────────────────────────────────────────────────────────────────
print(f"\n{OK} Listo. Próximos pasos:")
print("  1. cd backend && python manage.py migrate")
print("  2. ruff check . && ruff format .")
print("  3. git add -A && git commit -m 'feat(HU-16): agregar dias_atencion al local'")
print("  4. git push\n")
