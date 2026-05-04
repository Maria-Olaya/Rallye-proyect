# apply_hu16_horarios_v2.py
# Ejecutar desde la RAÍZ del repo: python apply_hu16_horarios_v2.py
#
# Estrategia: agrega horarios JSONField SIN quitar hora_apertura/hora_cierre
# (esos campos siguen en el modelo para no romper tests ni BD existente).
# El serializer de edición expone horarios; hora_apertura/hora_cierre quedan
# solo en el serializer público del mapa (ya existían).

from pathlib import Path

ROOT = Path(__file__).parent
BACKEND = ROOT / "backend"
FRONTEND = ROOT / "frontend"

OK = "\033[92m✔\033[0m"
ERR = "\033[91m✘\033[0m"
INF = "\033[94m→\033[0m"


def patch(path: Path, old: str, new: str, label: str) -> bool:
    text = path.read_text(encoding="utf-8")
    if old not in text:
        print(f"  {ERR} {label}: fragmento no encontrado")
        return False
    path.write_text(text.replace(old, new, 1), encoding="utf-8")
    print(f"  {OK} {label}")
    return True


def write(path: Path, content: str, label: str):
    if path.exists():
        print(f"  {ERR} {label}: ya existe, se omite")
        return
    path.write_text(content, encoding="utf-8")
    print(f"  {OK} {label}")


# ── 1. models.py — agregar horarios conservando hora_apertura/hora_cierre ──
print(f"\n{INF} Parcheando models.py …")
patch(
    BACKEND / "core" / "models.py",
    old="    activo = models.BooleanField(default=True)\n\n    def __str__(self):",
    new=(
        "    activo = models.BooleanField(default=True)\n"
        "    horarios = models.JSONField(\n"
        "        default=list,\n"
        "        blank=True,\n"
        "        help_text=(\n"
        "            'Lista de franjas: '\n"
        '            \'[{"dias":["lun","mar"], "apertura":"08:00", "cierre":"17:00"}]\'\n'
        "        ),\n"
        "    )\n\n"
        "    def __str__():"
    ),
    label="Local.horarios JSONField añadido (conserva hora_apertura/hora_cierre)",
)
# fallback sin \n\n antes de def __str__
patch(
    BACKEND / "core" / "models.py",
    old="    activo = models.BooleanField(default=True)\n\n    def __str__(self):\n        return self.nombre",
    new=(
        "    activo = models.BooleanField(default=True)\n"
        "    horarios = models.JSONField(\n"
        "        default=list,\n"
        "        blank=True,\n"
        "        help_text=(\n"
        "            'Lista de franjas: '\n"
        '            \'[{"dias":["lun","mar"], "apertura":"08:00", "cierre":"17:00"}]\'\n'
        "        ),\n"
        "    )\n\n"
        "    def __str__(self):\n"
        "        return self.nombre"
    ),
    label="Local.horarios JSONField (fallback con return)",
)

# ── 2. Migración ──────────────────────────────────────────────────────────────
print(f"\n{INF} Creando migración …")
mig_dir = BACKEND / "core" / "migrations"
existing = sorted(f.stem for f in mig_dir.glob("0*.py") if "__" not in f.stem)
last_dep = (
    existing[-1] if existing else "0003_alter_local_id_alter_municipio_id_alter_sede_id"
)

# Determinar número siguiente
last_num = int(existing[-1][:4]) if existing else 3
next_num = str(last_num + 1).zfill(4)
mig_name = f"{next_num}_local_horarios"
mig_path = mig_dir / f"{mig_name}.py"

write(
    mig_path,
    f"""\
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("core", "{last_dep}"),
    ]

    operations = [
        migrations.AddField(
            model_name="local",
            name="horarios",
            field=models.JSONField(
                blank=True,
                default=list,
                help_text=(
                    "Lista de franjas: "
                    '[{{"dias":["lun","mar"], "apertura":"08:00", "cierre":"17:00"}}]'
                ),
            ),
        ),
    ]
""",
    f"{mig_name}.py",
)

# ── 3. serializers.py ─────────────────────────────────────────────────────────
print(f"\n{INF} Parcheando serializers.py …")
ser = BACKEND / "core" / "serializers.py"

# LocalUpdateSerializer: reemplazar hora_apertura/hora_cierre por horarios
# Con dias_atencion previo
patch(
    ser,
    old=(
        '            "hora_apertura",\n'
        '            "hora_cierre",\n'
        '            "correo_admin",\n'
        '            "num_mecanicos",\n'
        '            "activo",\n'
        '            "dias_atencion",\n'
    ),
    new=(
        '            "correo_admin",\n'
        '            "num_mecanicos",\n'
        '            "activo",\n'
        '            "horarios",\n'
    ),
    label="LocalUpdateSerializer: horarios (desde dias_atencion)",
)
# Sin dias_atencion (estado main limpio)
patch(
    ser,
    old=(
        '            "hora_apertura",\n'
        '            "hora_cierre",\n'
        '            "correo_admin",\n'
        '            "num_mecanicos",\n'
        '            "activo",\n'
    ),
    new=(
        '            "correo_admin",\n'
        '            "num_mecanicos",\n'
        '            "activo",\n'
        '            "horarios",\n'
    ),
    label="LocalUpdateSerializer: horarios (estado main)",
)

# ── 4. editar_local.html ──────────────────────────────────────────────────────
print(f"\n{INF} Parcheando editar_local.html …")
tmpl = FRONTEND / "templates" / "admin_panel" / "editar_local.html"
text = tmpl.read_text(encoding="utf-8")

# ── 4a. CSS ──────────────────────────────────────────────────────────────────
CSS_FRANJAS = """\
    /* franjas horarias */
    .franja-card { background:#111; border:1.5px solid #2d2d2d; border-radius:12px; padding:1rem 1.2rem; margin-bottom:0.75rem; position:relative; }
    .franja-remove { position:absolute; top:0.6rem; right:0.7rem; background:transparent; border:none; color:#444; font-size:1rem; cursor:pointer; transition:color 0.15s; padding:0.2rem 0.4rem; border-radius:6px; }
    .franja-remove:hover { color:#f87171; background:rgba(239,68,68,0.1); }
    .franja-dias { display:flex; gap:0.4rem; flex-wrap:wrap; margin-bottom:0.75rem; }
    .franja-dia { display:inline-flex; }
    .franja-dia input[type=checkbox] { display:none; }
    .franja-dia label { display:inline-block; padding:0.3rem 0.65rem; border:1.5px solid #2d2d2d; border-radius:6px; font-family:'Barlow Condensed',sans-serif; font-size:0.78rem; font-weight:700; letter-spacing:0.07em; text-transform:uppercase; color:#555; background:#0d0d0d; cursor:pointer; transition:all 0.13s; user-select:none; }
    .franja-dia input[type=checkbox]:checked + label { background:#cc0000; border-color:#cc0000; color:#fff; }
    .franja-dia label:hover { border-color:#cc0000; color:#ccc; }
    .franja-horas { display:grid; grid-template-columns:1fr 1fr; gap:0.6rem; }
    .franja-horas label { font-size:0.65rem; font-weight:700; letter-spacing:0.1em; text-transform:uppercase; color:#666; display:block; margin-bottom:0.25rem; }
    .franja-horas input[type=time] { background:#0d0d0d; border:1.5px solid #2d2d2d; border-radius:8px; color:#f0f0f0; font-size:0.85rem; padding:0.5rem 0.75rem; outline:none; width:100%; transition:border-color 0.15s; }
    .franja-horas input[type=time]:focus { border-color:#cc0000; }
    .btn-add-franja { display:inline-flex; align-items:center; gap:0.4rem; padding:0.5rem 1rem; background:transparent; border:1.5px dashed #333; border-radius:10px; color:#555; font-family:'Barlow Condensed',sans-serif; font-size:0.8rem; font-weight:700; letter-spacing:0.08em; text-transform:uppercase; cursor:pointer; transition:all 0.15s; margin-top:0.5rem; width:100%; justify-content:center; }
    .btn-add-franja:hover { border-color:#cc0000; color:#cc0000; }
"""

# Insertar CSS justo antes de .ml-preview-label (sea cual sea el bloque que ya exista)
if "/* franjas horarias */" not in text:
    # Buscar el ancla .ml-preview-label (siempre existe)
    anchor = "    .ml-preview-label"
    if anchor in text:
        text = text.replace(anchor, CSS_FRANJAS + anchor, 1)
        print(f"  {OK} CSS franjas insertado")
    else:
        print(f"  {ERR} CSS: no se encontró ancla .ml-preview-label")
else:
    print(f"  — CSS franjas ya presente")

# ── 4b. HTML: reemplazar sección horarios (con o sin días) por franjas ────────

# Caso A: ya tiene las dos secciones del script anterior (días + horarios separados)
OLD_HTML_A = (
    "      <!-- Días de atención -->\n"
    '      <div class="ml-card-section">\n'
    '        <div class="ml-section-title"><i class="fas fa-calendar-week"></i> Días de atención</div>\n'
    '        <div class="dias-grid" id="diasGrid">\n'
    '          <div class="dia-chip"><input type="checkbox" id="dia-lun" value="lun"><label for="dia-lun">Lun</label></div>\n'
    '          <div class="dia-chip"><input type="checkbox" id="dia-mar" value="mar"><label for="dia-mar">Mar</label></div>\n'
    '          <div class="dia-chip"><input type="checkbox" id="dia-mie" value="mie"><label for="dia-mie">Mié</label></div>\n'
    '          <div class="dia-chip"><input type="checkbox" id="dia-jue" value="jue"><label for="dia-jue">Jue</label></div>\n'
    '          <div class="dia-chip"><input type="checkbox" id="dia-vie" value="vie"><label for="dia-vie">Vie</label></div>\n'
    '          <div class="dia-chip"><input type="checkbox" id="dia-sab" value="sab"><label for="dia-sab">Sáb</label></div>\n'
    '          <div class="dia-chip"><input type="checkbox" id="dia-dom" value="dom"><label for="dia-dom">Dom</label></div>\n'
    "        </div>\n"
    "      </div>\n"
    "\n"
    "      <!-- Horarios -->\n"
    '      <div class="ml-card-section">\n'
    '        <div class="ml-section-title"><i class="fas fa-clock"></i> Horarios y operación</div>\n'
    '        <div class="ml-grid-2">\n'
    '          <div class="ml-field">\n'
    '            <label class="ml-label"><i class="fas fa-sun"></i> Hora de apertura <span class="req">*</span></label>\n'
    '            <input type="time" class="ml-input" id="hora_apertura">\n'
    "          </div>\n"
    '          <div class="ml-field">\n'
    '            <label class="ml-label"><i class="fas fa-moon"></i> Hora de cierre <span class="req">*</span></label>\n'
    '            <input type="time" class="ml-input" id="hora_cierre">\n'
    "          </div>\n"
    "        </div>\n"
    '        <div class="ml-field" style="margin-top:1rem;">\n'
    '          <label class="ml-label"><i class="fas fa-wrench"></i> Número de mecánicos <span class="req">*</span></label>\n'
    '          <input type="number" class="ml-input" id="num_mecanicos" min="1" max="200" style="max-width:180px;">\n'
    "        </div>\n"
    "      </div>"
)

# Caso B: solo la sección horarios original (sin días) — estado más cercano a main
OLD_HTML_B = (
    "      <!-- Horarios -->\n"
    '      <div class="ml-card-section">\n'
    '        <div class="ml-section-title"><i class="fas fa-clock"></i> Horarios y operación</div>\n'
    '        <div class="ml-grid-2">\n'
    '          <div class="ml-field">\n'
    '            <label class="ml-label"><i class="fas fa-sun"></i> Hora de apertura <span class="req">*</span></label>\n'
    '            <input type="time" class="ml-input" id="hora_apertura">\n'
    "          </div>\n"
    '          <div class="ml-field">\n'
    '            <label class="ml-label"><i class="fas fa-moon"></i> Hora de cierre <span class="req">*</span></label>\n'
    '            <input type="time" class="ml-input" id="hora_cierre">\n'
    "          </div>\n"
    "        </div>\n"
    '        <div class="ml-field" style="margin-top:1rem;">\n'
    '          <label class="ml-label"><i class="fas fa-wrench"></i> Número de mecánicos <span class="req">*</span></label>\n'
    '          <input type="number" class="ml-input" id="num_mecanicos" min="1" max="200" style="max-width:180px;">\n'
    "        </div>\n"
    "      </div>"
)

NEW_HTML = (
    "      <!-- Horarios con franjas -->\n"
    '      <div class="ml-card-section">\n'
    '        <div class="ml-section-title"><i class="fas fa-calendar-week"></i> Horarios de atención</div>\n'
    '        <div id="franjasContainer"></div>\n'
    '        <button type="button" class="btn-add-franja" onclick="agregarFranja()">\n'
    '          <i class="fas fa-plus"></i> Agregar franja horaria\n'
    "        </button>\n"
    "      </div>\n"
    "\n"
    "      <!-- Operación -->\n"
    '      <div class="ml-card-section">\n'
    '        <div class="ml-section-title"><i class="fas fa-wrench"></i> Operación</div>\n'
    '        <div class="ml-field">\n'
    '          <label class="ml-label"><i class="fas fa-wrench"></i> Número de mecánicos <span class="req">*</span></label>\n'
    '          <input type="number" class="ml-input" id="num_mecanicos" min="1" max="200" style="max-width:180px;">\n'
    "        </div>\n"
    "      </div>"
)

if "franjasContainer" in text:
    print("  — HTML franjas ya presente")
elif OLD_HTML_A in text:
    text = text.replace(OLD_HTML_A, NEW_HTML, 1)
    print(f"  {OK} HTML: reemplazado (caso A: días + horarios)")
elif OLD_HTML_B in text:
    text = text.replace(OLD_HTML_B, NEW_HTML, 1)
    print(f"  {OK} HTML: reemplazado (caso B: solo horarios)")
else:
    print(f"  {ERR} HTML: no se encontró sección de horarios — edítalo manualmente")

# ── 4c. Vista previa ──────────────────────────────────────────────────────────
PV_TARGETS = [
    # con días
    (
        '          <div class="ml-preview-row"><i class="fas fa-clock"></i><span id="pvHorario">--:-- — --:--</span></div>\n'
        '          <div class="ml-preview-row"><i class="fas fa-calendar-week"></i><span id="pvDias">Sin días configurados</span></div>',
        "A",
    ),
    # solo horario
    (
        '          <div class="ml-preview-row"><i class="fas fa-clock"></i><span id="pvHorario">--:-- — --:--</span></div>',
        "B",
    ),
]
PV_NEW = '          <div class="ml-preview-row"><i class="fas fa-calendar-week"></i><span id="pvHorarios">Sin horarios configurados</span></div>'

if "pvHorarios" in text:
    print("  — Vista previa ya actualizada")
else:
    replaced = False
    for pv_old, caso in PV_TARGETS:
        if pv_old in text:
            text = text.replace(pv_old, PV_NEW, 1)
            print(f"  {OK} Vista previa: pvHorarios (caso {caso})")
            replaced = True
            break
    if not replaced:
        print(f"  {ERR} Vista previa: no encontrada — edita manualmente")

# ── 4d. JS: reemplazar bloque completo de script ─────────────────────────────
# Detectar si ya tiene getFranjas (script nuevo ya aplicado)
if "getFranjas" in text:
    print("  — JS franjas ya presente")
else:
    # Buscar inicio del bloque (function(){ ) y fin }</script>
    # Reemplazar todo el <script>...</script> del panel
    import re

    # Buscar el <script> que contiene "var localId"
    script_match = re.search(
        r"<script>\s*\(function\(\) \{.*?</script>", text, re.DOTALL
    )
    if script_match:
        OLD_SCRIPT = script_match.group(0)
        NEW_SCRIPT = """\
<script>
(function () {
    var localId = null;
    var activoVal = false;
    var franjaCount = 0;

    var DIAS = ["lun", "mar", "mie", "jue", "vie", "sab", "dom"];
    var DIAS_LABEL = { lun: "Lun", mar: "Mar", mie: "Mié", jue: "Jue", vie: "Vie", sab: "Sáb", dom: "Dom" };

    function getToken() {
        return sessionStorage.getItem("access_token") || sessionStorage.getItem("access");
    }

    function getCsrf() {
        var m = document.cookie.match(/csrftoken=([^;]+)/);
        return m ? m[1] : "";
    }

    function toast(msg, tipo, dur) {
        tipo = tipo || "success";
        dur = dur || 4000;
        var icons = { success: "fa-check-circle", error: "fa-exclamation-circle", info: "fa-info-circle" };
        var c = document.getElementById("toastContainer");
        var el = document.createElement("div");
        el.className = "ml-toast-item " + tipo;
        el.innerHTML = '<i class="fas ' + (icons[tipo] || icons.info) + '"></i><span>' + msg + "</span>";
        c.appendChild(el);
        if (dur > 0) {
            setTimeout(function () {
                el.style.opacity = "0";
                el.style.transition = "opacity 0.3s";
                setTimeout(function () { el.remove(); }, 300);
            }, dur);
        }
    }

    function setBusy(id, busy, label) {
        var btn = document.getElementById(id);
        if (!btn) return;
        btn.disabled = busy;
        if (busy) {
            btn._orig = btn.innerHTML;
            btn.innerHTML = '<span class="spinner"></span> ' + (label || "");
        } else {
            if (btn._orig) btn.innerHTML = btn._orig;
        }
    }

    // ── Franjas horarias ──────────────────────────────────────────────────────

    window.agregarFranja = function (franja) {
        franjaCount++;
        var id = franjaCount;
        var dias = (franja && franja.dias) || [];
        var apertura = (franja && franja.apertura) || "";
        var cierre = (franja && franja.cierre) || "";

        var diasHtml = DIAS.map(function (d) {
            var uid = "f" + id + "-" + d;
            var checked = dias.indexOf(d) !== -1 ? "checked" : "";
            return (
                '<div class="franja-dia">' +
                '<input type="checkbox" id="' + uid + '" value="' + d + '" ' + checked + ">" +
                '<label for="' + uid + '">' + DIAS_LABEL[d] + "</label>" +
                "</div>"
            );
        }).join("");

        var card = document.createElement("div");
        card.className = "franja-card";
        card.dataset.id = id;
        card.innerHTML =
            '<button type="button" class="franja-remove" onclick="eliminarFranja(' + id + ')" title="Eliminar franja">' +
            '<i class="fas fa-times"></i></button>' +
            '<div class="franja-dias">' + diasHtml + "</div>" +
            '<div class="franja-horas">' +
            "<div><label>Apertura</label>" +
            '<input type="time" id="ap-' + id + '" value="' + apertura + '" onchange="actualizarPreviewHorarios()"></div>' +
            "<div><label>Cierre</label>" +
            '<input type="time" id="ci-' + id + '" value="' + cierre + '" onchange="actualizarPreviewHorarios()"></div>' +
            "</div>";

        card.querySelectorAll("input[type=checkbox]").forEach(function (cb) {
            cb.addEventListener("change", actualizarPreviewHorarios);
        });

        document.getElementById("franjasContainer").appendChild(card);
        actualizarPreviewHorarios();
    };

    window.eliminarFranja = function (id) {
        var card = document.querySelector('.franja-card[data-id="' + id + '"]');
        if (card) card.remove();
        actualizarPreviewHorarios();
    };

    function getFranjas() {
        var result = [];
        document.querySelectorAll(".franja-card").forEach(function (card) {
            var id = card.dataset.id;
            var dias = Array.from(card.querySelectorAll("input[type=checkbox]:checked")).map(function (cb) { return cb.value; });
            var ap = document.getElementById("ap-" + id);
            var ci = document.getElementById("ci-" + id);
            result.push({ dias: dias, apertura: ap ? ap.value : "", cierre: ci ? ci.value : "" });
        });
        return result;
    }

    function setFranjas(horarios) {
        document.getElementById("franjasContainer").innerHTML = "";
        franjaCount = 0;
        if (!Array.isArray(horarios) || horarios.length === 0) {
            agregarFranja();
            return;
        }
        horarios.forEach(function (f) { agregarFranja(f); });
    }

    function actualizarPreviewHorarios() {
        var franjas = getFranjas();
        var el = document.getElementById("pvHorarios");
        if (!el) return;
        if (franjas.length === 0) { el.textContent = "Sin horarios configurados"; return; }
        el.textContent = franjas.map(function (f) {
            var dias = f.dias.map(function (d) { return DIAS_LABEL[d] || d; }).join(", ") || "Sin días";
            var hr = (f.apertura || "--:--") + " - " + (f.cierre || "--:--");
            return dias + ": " + hr;
        }).join(" | ");
    }

    // ── Toggle activo ─────────────────────────────────────────────────────────

    window.toggleActivo = function () {
        activoVal = !activoVal;
        syncToggleUI();
    };

    function syncToggleUI() {
        var t = document.getElementById("toggleActivo");
        var lbl = document.getElementById("toggleLabel");
        var pvStatus = document.getElementById("pvStatus");
        if (t) t.classList.toggle("on", activoVal);
        if (lbl) lbl.textContent = activoVal ? "Abierto al público" : "Cerrado temporalmente";
        if (pvStatus) {
            pvStatus.textContent = activoVal ? "Abierto" : "Cerrado";
            pvStatus.style.color = activoVal ? "#22c55e" : "#ef4444";
        }
    }

    // ── Vista previa ──────────────────────────────────────────────────────────

    function actualizarPreview() {
        var fld = function (id) { var el = document.getElementById(id); return el ? el.value.trim() : ""; };
        var pvNombre = document.getElementById("pvNombre");
        var pvTel = document.getElementById("pvTel");
        var pvDir = document.getElementById("pvDir");
        var pvDesc = document.getElementById("pvDesc");
        var nombre = document.getElementById("pvNombreStatic");
        if (pvNombre && nombre) pvNombre.textContent = nombre.textContent || "—";
        if (pvTel) pvTel.textContent = fld("telefono") || "—";
        if (pvDir) pvDir.textContent = fld("direccion") || "—";
        if (pvDesc) pvDesc.textContent = fld("descripcion") || "Sin descripción";
        actualizarPreviewHorarios();
    }

    function actualizarContador() {
        var el = document.getElementById("descripcion");
        var cnt = document.getElementById("descCount");
        if (el && cnt) cnt.textContent = el.value.length;
    }

    // ── Cargar datos ──────────────────────────────────────────────────────────

    function cargarDatos() {
        var token = getToken();
        if (!token) { window.location.href = "/login/"; return; }
        var parts = window.location.pathname.split("/").filter(Boolean);
        localId = parseInt(parts[parts.length - 1], 10) || parseInt(parts[parts.length - 2], 10);
        if (!localId) { toast("No se pudo determinar el ID del local.", "error"); return; }

        setBusy("btnGuardar", true, "Cargando…");
        fetch("/api/core/locales/" + localId + "/editar/", {
            headers: { Authorization: "Bearer " + token, "X-CSRFToken": getCsrf() },
        })
            .then(function (r) {
                if (r.status === 401) { window.location.href = "/login/"; return null; }
                if (!r.ok) { toast("Error al cargar datos del local.", "error"); setBusy("btnGuardar", false); return null; }
                return r.json();
            })
            .then(function (d) {
                if (!d) return;
                var set = function (id, val) { var el = document.getElementById(id); if (el) el.value = val || ""; };
                set("telefono", d.telefono);
                set("correo_admin", d.correo_admin);
                set("direccion", d.direccion);
                set("descripcion", d.descripcion);
                set("num_mecanicos", d.num_mecanicos);
                var ns = document.getElementById("pvNombreStatic");
                if (ns) ns.textContent = d.nombre || "";
                activoVal = !!d.activo;
                syncToggleUI();
                setFranjas(d.horarios || []);
                actualizarContador();
                actualizarPreview();
                setBusy("btnGuardar", false);
            })
            .catch(function () { toast("Error de conexión al cargar datos.", "error"); setBusy("btnGuardar", false); });
    }

    // ── Validar ───────────────────────────────────────────────────────────────

    function validar() {
        var campos = [
            { id: "telefono",     test: function (v) { return /^[0-9+\\-\\s]{7,20}$/.test(v); }, msg: "Teléfono inválido (7-20 dígitos)." },
            { id: "correo_admin", test: function (v) { return /^[^@]+@[^@]+\\.[^@]+$/.test(v); }, msg: "Correo electrónico inválido." },
            { id: "direccion",    test: function (v) { return v.length >= 5; },                  msg: "Dirección demasiado corta (mín. 5 caracteres)." },
            { id: "num_mecanicos",test: function (v) { return parseInt(v, 10) >= 1; },           msg: "Debe haber al menos 1 mecánico." },
        ];
        var ok = true;
        document.querySelectorAll(".ml-input").forEach(function (el) { el.classList.remove("field-error"); });
        campos.forEach(function (c) {
            var el = document.getElementById(c.id);
            if (!el) return;
            if (!c.test(el.value.trim())) {
                el.classList.add("field-error");
                toast(c.msg, "error");
                ok = false;
            }
        });
        var franjas = getFranjas();
        var franjaOk = franjas.length > 0 && franjas.every(function (f) {
            return f.dias.length > 0 && f.apertura && f.cierre && f.apertura < f.cierre;
        });
        if (!franjaOk) {
            toast("Agrega al menos una franja con días seleccionados y apertura antes del cierre.", "error");
            ok = false;
        }
        return ok;
    }

    // ── Guardar ───────────────────────────────────────────────────────────────

    window.guardarCambios = function () {
        if (!validar()) return;
        var token = getToken();
        if (!token) { window.location.href = "/login/"; return; }
        var fld = function (id) { var el = document.getElementById(id); return el ? el.value.trim() : ""; };

        var payload = {
            telefono:     fld("telefono"),
            correo_admin: fld("correo_admin"),
            direccion:    fld("direccion"),
            descripcion:  fld("descripcion"),
            num_mecanicos: parseInt(fld("num_mecanicos"), 10),
            activo:       activoVal,
            horarios:     getFranjas(),
        };

        setBusy("btnGuardar", true, "Guardando…");
        fetch("/api/core/locales/" + localId + "/editar/", {
            method: "PATCH",
            headers: {
                "Content-Type": "application/json",
                Authorization: "Bearer " + token,
                "X-CSRFToken": getCsrf(),
            },
            body: JSON.stringify(payload),
        })
            .then(function (r) { return r.json().then(function (d) { return { ok: r.ok, data: d }; }); })
            .then(function (res) {
                setBusy("btnGuardar", false);
                if (res.ok) {
                    toast("Información actualizada correctamente.", "success");
                } else {
                    var msgs = [];
                    Object.keys(res.data).forEach(function (k) {
                        var v = res.data[k];
                        msgs.push((Array.isArray(v) ? v.join(", ") : String(v)));
                    });
                    toast(msgs.join(" | ") || "Error al guardar.", "error");
                }
            })
            .catch(function () { setBusy("btnGuardar", false); toast("Error de conexión al guardar.", "error"); });
    };

    // ── Init ──────────────────────────────────────────────────────────────────

    document.addEventListener("DOMContentLoaded", function () {
        cargarDatos();
        ["telefono", "correo_admin", "direccion"].forEach(function (id) {
            var el = document.getElementById(id);
            if (el) { el.addEventListener("input", actualizarPreview); el.addEventListener("change", actualizarPreview); }
        });
        document.getElementById("descripcion")?.addEventListener("input", function () { actualizarContador(); actualizarPreview(); });
    });
})();
</script>"""
        text = text.replace(OLD_SCRIPT, NEW_SCRIPT, 1)
        print(f"  {OK} JS: bloque completo reemplazado")
    else:
        print(
            f"  {ERR} JS: no se encontró bloque <script>(function(){{}} — edita manualmente"
        )

# Guardar template
tmpl.write_text(text, encoding="utf-8")
print(f"  {OK} editar_local.html guardado")

# ── 5. tests.py — actualizar make_local para que no use hora_apertura/hora_cierre como único path ──
# Los tests existentes siguen funcionando (hora_apertura/hora_cierre siguen en el modelo).
# Solo agregamos un test de horarios.
print(f"\n{INF} Parcheando tests.py …")
patch(
    BACKEND / "core" / "tests.py",
    old='    def test_get_retorna_datos_actuales(self):\n        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {get_token(self.admin)}")\n        resp = self.client.get(self.url)\n        self.assertEqual(resp.status_code, 200)\n        self.assertEqual(resp.data["telefono"], "3001234567")',
    new=(
        "    def test_get_retorna_datos_actuales(self):\n"
        '        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {get_token(self.admin)}")\n'
        "        resp = self.client.get(self.url)\n"
        "        self.assertEqual(resp.status_code, 200)\n"
        '        self.assertEqual(resp.data["telefono"], "3001234567")\n'
        "\n"
        "    def test_admin_puede_actualizar_horarios(self):\n"
        '        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {get_token(self.admin)}")\n'
        "        horarios = [\n"
        '            {"dias": ["lun", "mar", "mie", "jue", "vie"], "apertura": "08:00", "cierre": "17:00"},\n'
        '            {"dias": ["sab"], "apertura": "07:00", "cierre": "12:00"},\n'
        "        ]\n"
        '        resp = self.client.patch(self.url, {"horarios": horarios}, format="json")\n'
        "        self.assertEqual(resp.status_code, 200)\n"
        "        self.local.refresh_from_db()\n"
        "        self.assertEqual(len(self.local.horarios), 2)\n"
        '        self.assertIn("lun", self.local.horarios[0]["dias"])'
    ),
    label="tests.py: test_admin_puede_actualizar_horarios añadido",
)

# ──────────────────────────────────────────────────────────────────────────────
print(f"\n{OK} Listo. Próximos pasos:")
print("  1. cd backend && python manage.py migrate")
print("  2. ruff check . && ruff format .")
print("  3. python manage.py test core")
print(
    "  4. git add -A && git commit -m 'feat(HU-16): horarios multiples por franja dias/apertura/cierre'"
)
print("  5. git push\n")
