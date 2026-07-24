import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import matplotlib.pyplot as plt
import zipfile
import xml.etree.ElementTree as ET
import io
import json
import re
import datetime
import hashlib
import os
from reconciliation import conciliar_dos_fuentes

# ==============================================================================
# 1. CONFIGURACIÓN DE INFRAESTRUCTURA PREMIUM CORPORATIVA
# ==============================================================================
st.set_page_config(
    page_title="TaxFlow-Diamond | Suite de Conciliación",
    page_icon=":blue[:material/diamond:]",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Inyección de estilos CSS para visualización ejecutiva e indicadores semafóricos
st.markdown("""
    <style>
    .stApp { background-color: #0D1117; }
    .main-title { font-size: 38px !important; font-weight: 700 !important; color: #FFFFFF; margin-bottom: 5px; }
    .subtitle { font-size: 16px !important; color: #FFFFFF; margin-bottom: 30px; font-weight: 500; opacity: 0.75; }
    .section-header { color: #FFFFFF; font-weight: 600; border-bottom: 2px solid #161B22; padding-bottom: 10px; margin-bottom: 20px; font-size: 22px; }
    .kpi-card { padding: 15px; border-radius: 6px; color: #0D1117; font-weight: 700; text-align: center; margin-bottom: 15px; }
    .kpi-green { background-color: #2ECC71 !important; }
    .kpi-yellow { background-color: #F1C40F !important; }
    .kpi-red { background-color: #E74C3C !important; }
    .help-card { background-color: #161B22; padding: 20px; border-radius: 8px; margin-bottom: 15px; border-left: 4px solid #00D4FF; }
    .help-title { color: #FFFFFF; font-size: 18px; font-weight: 600; margin-bottom: 10px; }
    div.stButton > button:first-child[data-testid="stSidebarActionButton"] { background-color: #00D4FF !important; color: #0D1117 !important; font-weight: 700 !important; border: none !important; }

    /* ---- Estilo Dashboard tipo BlackLine (versión oscura) ---- */
    .bl-wrapper { background-color: #0D1117; padding: 24px; border-radius: 14px; }
    .bl-card { background:#161B22; border-radius:10px; padding:18px 20px; box-shadow:0 1px 3px rgba(0,0,0,0.35), 0 1px 2px rgba(0,0,0,0.25); border:1px solid #2A313C; height:100%; }
    .bl-card-title { font-size:13px; color:#8B96A5; font-weight:600; margin-bottom:6px; display:flex; align-items:center; gap:6px; }
    .bl-card-value { font-size:32px; font-weight:700; color:#E6EDF3; line-height:1.1; }
    .bl-card-sub { font-size:12px; color:#6E7887; margin-top:2px; }
    .bl-subrow { display:flex; justify-content:space-between; font-size:13px; color:#C4CDD8; margin-top:8px; padding-top:8px; border-top:1px solid #2A313C; }
    .bl-badge { padding:1px 8px; border-radius:10px; font-size:11px; font-weight:700; margin-right:6px; }
    .bl-badge-orange { background:#4A2E15; color:#FDBA74; }
    .bl-badge-blue { background:#22284D; color:#FFFFFF; }
    .bl-badge-green { background:#123425; color:#6EE7B7; }
    .bl-badge-red { background:#43181A; color:#FCA5A5; }
    .bl-section { background:#161B22; border-radius:10px; padding:22px 24px; border:1px solid #2A313C; box-shadow:0 1px 3px rgba(0,0,0,0.3); }
    .bl-section-title { font-size:15px; font-weight:700; color:#E6EDF3; }
    .bl-count-pill { background:#2A313C; color:#C4CDD8; border-radius:12px; padding:1px 10px; font-size:12px; font-weight:700; margin-left:8px; }
    .bl-progress-bar { display:flex; height:16px; border-radius:8px; overflow:hidden; width:100%; margin:16px 0 12px 0; }
    .bl-legend { display:flex; flex-wrap:wrap; gap:18px; font-size:12.5px; color:#8B96A5; }
    .bl-dot { display:inline-block; width:8px; height:8px; border-radius:50%; margin-right:5px; }
    .bl-mini-card { background:#161B22; border-radius:10px; padding:16px 18px; border:1px solid #2A313C; border-top:3px solid #444; box-shadow:0 1px 3px rgba(0,0,0,0.25); }
    .bl-mini-title { font-size:13px; color:#8B96A5; font-weight:600; margin-bottom:6px; }
    .bl-mini-value { font-size:24px; font-weight:700; color:#E6EDF3; }

    /* ---- Tarjetas contenedoras para TODAS las gráficas (fondo gris que las delimita) ---- */
    div[class*="st-key-chartcard_"] {
        background-color: #161B22 !important;
        border: 1px solid #2A313C !important;
        border-radius: 12px !important;
        padding: 14px 10px !important;
    }
    </style>
""", unsafe_allow_html=True)

# ==============================================================================
# ICONOGRAFÍA CORPORATIVA: SVG de línea (estilo profesional monocromo) para
# títulos con estilo propio, donde el shortcode :material/x: de Streamlit no
# se renderiza dentro de unsafe_allow_html=True.
# ==============================================================================
_ICONOS_SVG = {
    "diamond": '<path d="M6 3h12l4 6-10 12L2 9Z"/><path d="M2 9h20"/><path d="M9 3l-3 6 6 12 6-12-3-6"/>',
    "dashboard": '<rect x="3" y="12" width="4" height="8" rx="1"/><rect x="10" y="7" width="4" height="13" rx="1"/><rect x="17" y="3" width="4" height="17" rx="1"/>',
    "bank": '<path d="M3 21h18"/><path d="M5 21V10M10 21V10M14 21V10M19 21V10"/><path d="M12 3 2 9h20L12 3Z"/>',
    "document": '<path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8Z"/><path d="M14 2v6h6"/><path d="M8 13h8M8 17h8"/>',
    "invoice": '<path d="M6 2h9l3 3v17H6z"/><path d="M9 8h6M9 12h6M9 16h4"/>',
    "globe": '<circle cx="12" cy="12" r="9"/><path d="M3 12h18"/><path d="M12 3c2.5 2.5 4 5.5 4 9s-1.5 6.5-4 9c-2.5-2.5-4-5.5-4-9s1.5-6.5 4-9Z"/>',
    "badge": '<rect x="4" y="3" width="16" height="18" rx="2"/><circle cx="12" cy="10" r="3"/><path d="M7.5 18c.7-2.2 2.4-3.5 4.5-3.5s3.8 1.3 4.5 3.5"/>',
    "box": '<path d="m3 8 9-5 9 5-9 5-9-5Z"/><path d="M3 8v8l9 5 9-5V8"/><path d="M12 13v8"/>',
    "cash": '<rect x="2" y="6" width="20" height="12" rx="2"/><circle cx="12" cy="12" r="3"/><path d="M6 10v.01M18 14v.01"/>',
    "factory": '<path d="M3 21V10l6 4v-4l6 4V6l6 4v11H3Z"/><path d="M7 21v-4M13 21v-4"/>',
    "trending": '<path d="m3 17 6-6 4 4 8-8"/><path d="M17 7h4v4"/>',
    "scale": '<path d="M12 3v18"/><path d="M5 7h14"/><path d="m5 7-3 7a3.5 3.5 0 0 0 6 0Z"/><path d="m19 7-3 7a3.5 3.5 0 0 0 6 0Z"/>',
    "check": '<circle cx="12" cy="12" r="9"/><path d="m8 12 3 3 5-6"/>',
    "clipboard": '<rect x="6" y="4" width="12" height="16" rx="2"/><path d="M9 2h6v4H9z"/><path d="M9 11h6M9 15h4"/>',
    "book": '<path d="M4 19.5A2.5 2.5 0 0 1 6.5 17H20V4H6.5A2.5 2.5 0 0 0 4 6.5v13Z"/><path d="M4 19.5A2.5 2.5 0 0 1 6.5 17H20"/>',
    "users": '<path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M23 21v-2a4 4 0 0 0-3-3.87"/><path d="M16 3.13a4 4 0 0 1 0 7.75"/>',
    "gear": '<circle cx="12" cy="12" r="3"/><path d="M19.4 15a1.65 1.65 0 0 0 .3 1.8l.1.1a2 2 0 1 1-2.8 2.8l-.1-.1a1.65 1.65 0 0 0-1.8-.3 1.65 1.65 0 0 0-1 1.5V21a2 2 0 0 1-4 0v-.1a1.65 1.65 0 0 0-1-1.5 1.65 1.65 0 0 0-1.8.3l-.1.1a2 2 0 1 1-2.8-2.8l.1-.1a1.65 1.65 0 0 0 .3-1.8 1.65 1.65 0 0 0-1.5-1H3a2 2 0 0 1 0-4h.1a1.65 1.65 0 0 0 1.5-1 1.65 1.65 0 0 0-.3-1.8l-.1-.1a2 2 0 1 1 2.8-2.8l.1.1a1.65 1.65 0 0 0 1.8.3H9a1.65 1.65 0 0 0 1-1.5V3a2 2 0 0 1 4 0v.1a1.65 1.65 0 0 0 1 1.5 1.65 1.65 0 0 0 1.8-.3l.1-.1a2 2 0 1 1 2.8 2.8l-.1.1a1.65 1.65 0 0 0-.3 1.8V9a1.65 1.65 0 0 0 1.5 1H21a2 2 0 0 1 0 4h-.1a1.65 1.65 0 0 0-1.5 1Z"/>',
    "help": '<circle cx="12" cy="12" r="9"/><path d="M9.1 9a3 3 0 0 1 5.8 1c0 2-3 3-3 3"/><path d="M12 17h.01"/>',
    "user": '<circle cx="12" cy="8" r="4"/><path d="M4 21c0-4 4-6 8-6s8 2 8 6"/>',
    "calendar": '<rect x="3" y="4" width="18" height="18" rx="2"/><path d="M16 2v4M8 2v4M3 10h18"/>',
}

_ICONOS_COLORES = {
    "diamond": "#38BDF8",
    "dashboard": "#38BDF8",
    "bank": "#3B82F6",
    "document": "#60A5FA",
    "invoice": "#F59E0B",
    "globe": "#22D3EE",
    "badge": "#A78BFA",
    "box": "#FB923C",
    "cash": "#34D399",
    "factory": "#FB7185",
    "trending": "#34D399",
    "scale": "#A78BFA",
    "check": "#34D399",
    "clipboard": "#60A5FA",
    "book": "#FBBF24",
    "users": "#F472B6",
    "gear": "#94A3B8",
    "help": "#38BDF8",
    "user": "#60A5FA",
    "calendar": "#FB923C",
}

def icono(nombre, size=18, color=None):
    """Devuelve un ícono SVG de línea con color propio (paleta corporativa) para usar dentro de HTML con unsafe_allow_html=True."""
    contenido_svg = _ICONOS_SVG.get(nombre, _ICONOS_SVG["check"])
    color_final = color or _ICONOS_COLORES.get(nombre, "#E6EDF3")
    return (f'<svg viewBox="0 0 24 24" width="{size}" height="{size}" fill="none" stroke="{color_final}" '
            f'stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" '
            f'style="vertical-align:-3px;margin-right:8px;">{contenido_svg}</svg>')

def punto(color, size=9):
    """Punto de estado circular (para semáforos: rojo/amarillo/verde/naranja/azul)."""
    return f'<span style="display:inline-block;width:{size}px;height:{size}px;border-radius:50%;background:{color};margin-right:7px;"></span>'


st.markdown(f'<div class="main-title">{icono("diamond", 32)} TaxFlow-Diamond</div>', unsafe_allow_html=True)
st.markdown('<div class="subtitle">Enterprise Financial & XML Reconciliation Suite</div>', unsafe_allow_html=True)

# ==============================================================================
# 2. SISTEMA DE MEMORIA INTEGRAL DEL WORKFLOW (SESSION STATE)
# ==============================================================================
# ==============================================================================
# 1.4 LOGOTIPO INSTITUCIONAL POR DEFECTO
# ==============================================================================
# Incrustado directamente como base64 (no depende de una carpeta externa ni
# de dónde se coloque app.py al desplegarlo). Si el usuario sube su propio
# logotipo en Configuración, ese reemplaza a este por el resto de la sesión.
_LOGO_DEFECTO_B64 = "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"
try:
    import base64 as _base64_logo
    _LOGO_DEFECTO_BYTES = _base64_logo.b64decode(_LOGO_DEFECTO_B64)
except Exception:
    _LOGO_DEFECTO_BYTES = None

variables_sesion = {
    'df_banco': None, 'df_auxiliar': None, 'bancos_cargados': False, 'bancos_ejecutado': False,
    'df_conciliados': None, 'bancos_pendientes': None, 'auxiliar_pendientes': None,
    'suma_conciliado': 0.0, 'suma_banco_p': 0.0, 'suma_aux_p': 0.0,
    'bancos_col_fecha_banco': None, 'bancos_col_fecha_aux': None, 'bancos_col_monto_banco': None, 'bancos_col_monto_aux': None,
    'bancos_clasificacion_pendientes': None,
    'bancos_departamentos_colores': {"Cuentas por Cobrar": "#10B981", "Tesorería": "#F97316", "Trainees": "#FF7F50", "Sin Asignar": "#6B7280"},
    'bancos_departamento_manual': None,
    'df_xml_gastos': None, 'df_aux_gastos': None, 'xml_cargados': False, 'xml_ejecutado': False, 'xml_conciliados': None, 'xml_pend_xml': None, 'xml_pend_aux': None,
    'df_saldos_globales': None, 'df_facturas_detalle': None, 'saldos_cargados': False, 'saldos_ejecutado': False, 'saldos_conciliados': None, 'saldos_discrepancias': None,
    'df_divisa_ext': None, 'df_divisa_nac': None, 'divisa_cargados': False, 'divisa_ejecutado': False, 'divisa_conciliados': None, 'divisa_pend_ext': None, 'divisa_pend_nac': None, 'tc_auditoria_val': 17.50,
    'df_cfdi_nomina': None, 'df_aux_nomina': None, 'nomina_cargados': False, 'nomina_ejecutado': False, 'nomina_conciliados': None, 'nomina_discrepancias': None, 'nomina_pend_cfdi': None, 'nomina_pend_aux': None,
    'df_inv_fisico': None, 'df_kardex_er': None, 'inventarios_cargados': False, 'inventarios_ejecutado': False, 'inventarios_conciliados': None, 'inventarios_discrepancias': None,
    'df_iva_banco': None, 'df_iva_aux': None, 'iva_cargados': False, 'iva_ejecutado': False, 'iva_conciliados': None, 'iva_discrepancias': None, 'iva_pend_banco': None, 'iva_pend_aux': None,
    'fase_progreso': 1, 'empresa': "", 'periodo': "", 'auditor': "", 'tolerancia': 0.50, 'tolerancia_dias': 3, 'tolerancia_inventario': 1.0, 'divisa': "MXN ($)", 'logo_bytes': _LOGO_DEFECTO_BYTES, 'fecha_limite_cierre': None,

    # --- Módulos corporativos nuevos ---
    'usuario_actual': "", 'rol_actual': "Preparador",
    'bitacora_eventos': [],
    'estado_revision': {},
    'pbc_checklist': None,
    'auditorias_guardadas': {},
    'df_af_kardex': None, 'af_cargados': False, 'af_ejecutado': False, 'af_conciliados': None, 'af_discrepancias': None,
    'sat_checklist': None,
    'rf_datos': {},
}

for llave, valor_defecto in variables_sesion.items():
    if llave not in st.session_state: st.session_state[llave] = valor_defecto

# ==============================================================================
# 1.5 SEGURIDAD: AUTENTICACIÓN DE USUARIOS
# ==============================================================================
# NOTA IMPORTANTE: 'usuarios_sistema' vive DELIBERADAMENTE fuera de
# 'variables_sesion' — es la base de usuarios de la app, no debe borrarse
# cuando alguien cierra sesión o reinicia una auditoría. Aun así, como no hay
# una base de datos real detrás, esta lista de usuarios vive solo en la
# memoria de este proceso de Streamlit: se pierde si el servidor se reinicia.
# Para un uso real en producción, esto debe respaldarse en una base de datos
# externa (esto es un control de flujo de trabajo, no un sistema de
# autenticación de nivel productivo).
def _hash_password(password, salt=None):
    if salt is None:
        salt = os.urandom(16).hex()
    hash_val = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), bytes.fromhex(salt), 100_000).hex()
    return salt, hash_val

def _verificar_password(password, salt, hash_guardado):
    _, hash_calculado = _hash_password(password, salt)
    return hash_calculado == hash_guardado

if 'usuarios_sistema' not in st.session_state:
    _salt_admin, _hash_admin = _hash_password("TaxFlow2026!")
    st.session_state.usuarios_sistema = {
        "admin": {
            "salt": _salt_admin, "hash": _hash_admin, "rol": "Administrador",
            "bloqueado": False, "creado": datetime.datetime.now().strftime("%Y-%m-%d %H:%M"),
            "ultimo_acceso": None, "intentos_fallidos": 0,
        }
    }
if 'sesion_autenticada' not in st.session_state: st.session_state.sesion_autenticada = False
if 'usuario_autenticado' not in st.session_state: st.session_state.usuario_autenticado = None

if not st.session_state.sesion_autenticada:
    st.warning(":orange[:material/key:] Usuario por defecto: **admin** — Contraseña: **TaxFlow2026!** — cámbiala en cuanto entres desde ':violet[:material/group:] Gestión de Usuarios'.")
    with st.form("form_login"):
        st.markdown("### :gray[:material/lock:] Iniciar Sesión")
        usuario_input = st.text_input("Usuario:")
        password_input = st.text_input("Contraseña:", type="password")
        enviado = st.form_submit_button("Entrar", type="primary", use_container_width=True)
    if enviado:
        registro_usuario = st.session_state.usuarios_sistema.get(usuario_input)
        if registro_usuario is None:
            st.error("Usuario o contraseña incorrectos.")
        elif registro_usuario["bloqueado"] or registro_usuario["intentos_fallidos"] >= 5:
            registro_usuario["bloqueado"] = True
            st.error(":red[:material/block:] Este usuario está bloqueado. Contacta a un Administrador.")
        elif _verificar_password(password_input, registro_usuario["salt"], registro_usuario["hash"]):
            st.session_state.sesion_autenticada = True
            st.session_state.usuario_autenticado = usuario_input
            st.session_state.usuario_actual = usuario_input
            st.session_state.rol_actual = registro_usuario["rol"]
            registro_usuario["intentos_fallidos"] = 0
            registro_usuario["ultimo_acceso"] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
            st.session_state.bitacora_eventos.append({
                "Fecha_Hora": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "Usuario": usuario_input, "Rol": registro_usuario["rol"],
                "Módulo": "Seguridad", "Acción": "Inició sesión",
            })
            st.rerun()
        else:
            registro_usuario["intentos_fallidos"] += 1
            if registro_usuario["intentos_fallidos"] >= 5:
                registro_usuario["bloqueado"] = True
                st.error(":red[:material/block:] Demasiados intentos fallidos: este usuario quedó bloqueado automáticamente. Contacta a un Administrador.")
            else:
                st.error(f"Usuario o contraseña incorrectos. Intento {registro_usuario['intentos_fallidos']}/5 antes del bloqueo automático.")
    st.stop()

# ==============================================================================
# 3. NAVEGACIÓN: se construye al final del archivo, agrupada por categorías
#    (una vez que todas las funciones render_x() ya están definidas)
# ==============================================================================

# ==============================================================================
# 4. PANEL LATERAL (IDENTIDAD CORPORATIVA FIJA Y UTILERÍAS)
# ==============================================================================
if st.session_state.logo_bytes is not None: st.sidebar.image(st.session_state.logo_bytes, use_container_width=True)
else: st.sidebar.info(":blue[:material/apartment:] Sin Logotipo Institucional. Configúralo en la pestaña superior de Configuración.")

st.sidebar.markdown("---")
st.sidebar.markdown("### :blue[:material/person:] Sesión Activa")
st.sidebar.success(f"**{st.session_state.usuario_autenticado}** ({st.session_state.rol_actual})")
if st.sidebar.button(":gray[:material/lock:] Cerrar Sesión", type="primary", use_container_width=True, key="sidebar_logout_btn"):
    st.session_state.bitacora_eventos.append({
        "Fecha_Hora": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "Usuario": st.session_state.usuario_autenticado, "Rol": st.session_state.rol_actual,
        "Módulo": "Seguridad", "Acción": "Cerró sesión",
    })
    _eventos_previos = st.session_state.bitacora_eventos
    for llave in variables_sesion.keys(): st.session_state[llave] = variables_sesion[llave]
    st.session_state.bitacora_eventos = _eventos_previos  # conservamos la bitácora aunque se reinicien los datos de trabajo
    st.session_state.sesion_autenticada = False
    st.session_state.usuario_autenticado = None
    st.rerun()
st.sidebar.caption(":orange[:material/warning:] Cerrar sesión también reinicia los datos de esta auditoría (bancos, XML, etc.) — descarga tu respaldo .JSON antes si quieres conservarlos.")

st.sidebar.markdown("---")
with st.sidebar.expander(":blue[:material/apartment:] Multiempresa (auditorías en esta sesión)"):
    st.caption("Guarda distintas auditorías en memoria para alternar entre clientes sin perder tu trabajo. Se pierden al cerrar el navegador o reiniciar el servidor — para conservarlas de forma permanente, descarga el respaldo .JSON de cada una desde Configuración.")
    nombre_nueva_auditoria = st.text_input("Nombre para guardar la auditoría actual:", key="nombre_snapshot")
    if st.button(":blue[:material/save:] Guardar auditoría actual", use_container_width=True, key="guardar_snapshot_btn"):
        if nombre_nueva_auditoria.strip():
            snapshot = _serializar_estado({llave: st.session_state[llave] for llave in variables_sesion.keys()})
            st.session_state.auditorias_guardadas[nombre_nueva_auditoria.strip()] = snapshot
            registrar_evento("Multiempresa", f"Guardó la auditoría '{nombre_nueva_auditoria.strip()}'")
            st.success(f"Auditoría '{nombre_nueva_auditoria.strip()}' guardada.")
        else:
            st.warning("Escribe un nombre antes de guardar.")
    if st.session_state.auditorias_guardadas:
        nombres_guardados = list(st.session_state.auditorias_guardadas.keys())
        auditoria_elegida = st.selectbox("Auditorías guardadas:", nombres_guardados, key="selector_snapshot")
        col_ae1, col_ae2 = st.columns(2)
        with col_ae1:
            if st.button(":blue[:material/folder_open:] Cargar", use_container_width=True, key="cargar_snapshot_btn"):
                for llave, valor in _deserializar_estado(st.session_state.auditorias_guardadas[auditoria_elegida]).items():
                    st.session_state[llave] = valor
                registrar_evento("Multiempresa", f"Cargó la auditoría '{auditoria_elegida}'")
                st.rerun()
        with col_ae2:
            if st.button(":red[:material/delete:] Eliminar", use_container_width=True, key="eliminar_snapshot_btn"):
                del st.session_state.auditorias_guardadas[auditoria_elegida]
                st.rerun()
    else:
        st.caption("Aún no hay auditorías guardadas.")

st.sidebar.markdown("---")
with st.sidebar.expander(":orange[:material/notifications:] Notificaciones", expanded=True):
    _notificaciones = []
    if st.session_state.fecha_limite_cierre:
        try:
            _fecha_lim = datetime.date.fromisoformat(st.session_state.fecha_limite_cierre)
            _dias_rest = (_fecha_lim - datetime.date.today()).days
            if _dias_rest < 0: _notificaciones.append(("error", f"⏰ El cierre venció hace {abs(_dias_rest)} día(s)."))
            elif _dias_rest <= 3: _notificaciones.append(("warning", f"⏰ Quedan {_dias_rest} día(s) para el cierre."))
        except ValueError:
            pass
    _modulos_sin_cargar = sum(1 for llave in ["bancos_cargados", "xml_cargados", "saldos_cargados", "divisa_cargados", "nomina_cargados", "inventarios_cargados", "iva_cargados"] if not st.session_state[llave])
    if _modulos_sin_cargar > 0:
        _notificaciones.append(("info", f":blue[:material/folder_open:] {_modulos_sin_cargar} módulo(s) de conciliación aún sin insumos cargados."))
    if st.session_state.pbc_checklist is not None and not st.session_state.pbc_checklist.empty:
        _pendientes_pbc = int((st.session_state.pbc_checklist["Estado"] == "Pendiente").sum())
        if _pendientes_pbc > 0: _notificaciones.append(("warning", f":blue[:material/checklist:] {_pendientes_pbc} documento(s) del checklist PBC pendientes de recibir."))
    if not _notificaciones:
        st.caption(":green[:material/check_circle:] Sin pendientes por ahora.")
    else:
        for _tipo, _texto in _notificaciones:
            getattr(st, _tipo)(_texto)

st.sidebar.markdown("---")
st.sidebar.markdown("### :blue[:material/download:] Descarga de Plantillas Corporativas")
buffer_p1 = io.BytesIO()
with pd.ExcelWriter(buffer_p1, engine='openpyxl') as w: pd.DataFrame(columns=["Fecha", "Concepto", "Referencia", "Importe", "RFC_Contraparte"]).to_excel(w, index=False)
st.sidebar.download_button(":blue[:material/bar_chart:] Plantilla Estado de Cuenta", data=buffer_p1.getvalue(), file_name="Plantilla_Estado_Cuenta.xlsx", use_container_width=True)

buffer_p2 = io.BytesIO()
with pd.ExcelWriter(buffer_p2, engine='openpyxl') as w: pd.DataFrame(columns=["Fecha_Poliza", "Cuenta_Contable", "Concepto_Movimiento", "Monto_Registro", "RFC_Validar"]).to_excel(w, index=False)
st.sidebar.download_button(":blue[:material/menu_book:] Plantilla Auxiliar Contable", data=buffer_p2.getvalue(), file_name="Plantilla_Auxiliar_Contable.xlsx", use_container_width=True)

st.sidebar.markdown("---")
st.sidebar.markdown("### :blue[:material/search:] Rastreador Rápido de Auditoría")
busqueda_rapida = st.sidebar.text_input("Ingresa monto o texto a rastrear:", placeholder="Ej. 15400.50 o Transferencia")

def leer_archivo_contable(file):
    if file.name.endswith('.csv'): return pd.read_csv(file)
    return pd.read_excel(file)

def validar_rfc(rfc):
    pattern = r'^[A-Z&Ñ]{3,4}[0-9]{2}(0[1-9]|1[0-2])(0[1-9]|[12][0-9]|3[01])[A-Z0-9]{3}$'
    return bool(re.match(pattern, str(rfc).upper().strip()))

def registrar_evento(modulo, accion):
    """Agrega un renglón a la Bitácora de Auditoría con usuario, módulo, acción y hora."""
    st.session_state.bitacora_eventos.append({
        "Fecha_Hora": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "Usuario": st.session_state.usuario_actual if st.session_state.usuario_actual else "Sin identificar",
        "Rol": st.session_state.rol_actual,
        "Módulo": modulo,
        "Acción": accion,
    })

def _serializar_estado(diccionario):
    """Convierte un dict de variables de sesión (incluyendo DataFrames y bytes)
    a una forma 100% serializable en JSON. Se usa tanto para el respaldo
    manual (.json descargable) como para las auditorías guardadas en memoria
    (multiempresa), para no duplicar la lógica de conversión."""
    resultado = {}
    for llave, valor in diccionario.items():
        if isinstance(valor, pd.DataFrame):
            resultado[llave] = {"tipo": "dataframe", "datos": valor.to_json(orient='split')}
        elif llave == 'logo_bytes' and valor is not None:
            resultado[llave] = {"tipo": "bytes", "datos": valor.hex()}
        else:
            resultado[llave] = {"tipo": "nativo", "datos": valor}
    return resultado

def _deserializar_estado(paquete):
    """Inverso de _serializar_estado."""
    resultado = {}
    for llave, info in paquete.items():
        if info["tipo"] == "dataframe":
            resultado[llave] = pd.read_json(io.StringIO(info["datos"]), orient='split')
        elif info["tipo"] == "bytes":
            resultado[llave] = bytes.fromhex(info["datos"])
        else:
            resultado[llave] = info["datos"]
    return resultado

def generar_dictamen_pdf(empresa, periodo, auditor, conciliado, banco_p, aux_p):
    fig, ax = plt.subplots(figsize=(8.5, 11))
    ax.axis('off')
    plt.text(0.1, 0.92, "TAXFLOW-DIAMOND FINANCIAL SUITE", fontsize=16, weight='bold', color='#00A4CC')
    plt.text(0.1, 0.89, "DICTAMEN FORMAL DE AUDITORÍA Y CONCILIACIÓN DE LIBROS", fontsize=12, weight='bold')
    plt.text(0.1, 0.85, "------------------------------------------------------------------------------------------------------------------------", color='gray')
    plt.text(0.1, 0.78, f"Razón Social del Cliente: {empresa if empresa else 'No Especificada'}", fontsize=11)
    plt.text(0.1, 0.75, f"Periodo Fiscal Auditado: {periodo if periodo else 'No Especificado'}", fontsize=11)
    plt.text(0.1, 0.72, f"Auditor Responsable: {auditor if auditor else 'No Especificado'}", fontsize=11)
    plt.text(0.1, 0.60, f"(*) Capital Conciliado y Alineado: $ {conciliado:,.2f}", fontsize=11)
    plt.text(0.1, 0.57, f"(*) Inconsistencias en Estado de Cuenta (Banco): $ {banco_p:,.2f}", fontsize=11)
    plt.text(0.1, 0.54, f"(*) Inconsistencias en Libro Mayor (Auxiliar): $ {aux_p:,.2f}", fontsize=11)
    total_desfase = banco_p + aux_p
    riesgo_status = "CRÍTICO" if total_desfase > (conciliado * 0.05) else "ACEPTABLE"
    plt.text(0.1, 0.45, f"DICTAMEN FINAL DEL AUDITOR: REVISIÓN CON STATUS {riesgo_status}", fontsize=12, weight='bold', color='red' if riesgo_status == "CRÍTICO" else 'green')
    pdf_buffer = io.BytesIO()
    plt.savefig(pdf_buffer, format='pdf', bbox_inches='tight', dpi=300)
    plt.close()
    return pdf_buffer.getvalue()

def calcular_estado_modulos():
    """
    Resume el estado de los 7 módulos de conciliación en dos niveles, igual
    que el concepto Recs/Tasks de BlackLine:
      - TASKS: los 7 módulos como checklist (no preparado / en progreso / completado).
      - RECS: las filas de datos dentro de cada módulo ya ejecutado (conciliadas
        cuentan como "completado", pendientes/discrepancias como "no preparado").
    Módulos que aún no calculan un desglose de pendientes (XML, Multidivisa,
    Nómina, Inventarios, IVA) solo aportan su conteo de filas conciliadas.
    """
    s = st.session_state
    modulos = [
        {"nombre": "Bancos", "cargado": s.bancos_cargados, "ejecutado": s.bancos_ejecutado,
         "insumos": [s.df_banco, s.df_auxiliar],
         "n_ok": len(s.df_conciliados) if s.df_conciliados is not None else 0,
         "n_pend": (len(s.bancos_pendientes) if s.bancos_pendientes is not None else 0) + (len(s.auxiliar_pendientes) if s.auxiliar_pendientes is not None else 0)},
        {"nombre": "XML", "cargado": s.xml_cargados, "ejecutado": s.xml_ejecutado,
         "insumos": [s.df_xml_gastos, s.df_aux_gastos],
         "n_ok": len(s.xml_conciliados) if s.xml_conciliados is not None else 0,
         "n_pend": (len(s.xml_pend_xml) if s.xml_pend_xml is not None else 0) + (len(s.xml_pend_aux) if s.xml_pend_aux is not None else 0)},
        {"nombre": "Clientes/Prov.", "cargado": s.saldos_cargados, "ejecutado": s.saldos_ejecutado,
         "insumos": [s.df_saldos_globales, s.df_facturas_detalle],
         "n_ok": len(s.saldos_conciliados) if s.saldos_conciliados is not None else 0,
         "n_pend": len(s.saldos_discrepancias) if s.saldos_discrepancias is not None else 0},
        {"nombre": "Multidivisa", "cargado": s.divisa_cargados, "ejecutado": s.divisa_ejecutado,
         "insumos": [s.df_divisa_ext, s.df_divisa_nac],
         "n_ok": len(s.divisa_conciliados) if s.divisa_conciliados is not None else 0,
         "n_pend": (len(s.divisa_pend_ext) if s.divisa_pend_ext is not None else 0) + (len(s.divisa_pend_nac) if s.divisa_pend_nac is not None else 0)},
        {"nombre": "Nómina", "cargado": s.nomina_cargados, "ejecutado": s.nomina_ejecutado,
         "insumos": [s.df_cfdi_nomina, s.df_aux_nomina],
         "n_ok": len(s.nomina_conciliados) if s.nomina_conciliados is not None else 0,
         "n_pend": (len(s.nomina_pend_cfdi) if s.nomina_pend_cfdi is not None else 0) + (len(s.nomina_pend_aux) if s.nomina_pend_aux is not None else 0)},
        {"nombre": "Inventarios", "cargado": s.inventarios_cargados, "ejecutado": s.inventarios_ejecutado,
         "insumos": [s.df_inv_fisico, s.df_kardex_er],
         "n_ok": len(s.inventarios_conciliados) if s.inventarios_conciliados is not None else 0,
         "n_pend": len(s.inventarios_discrepancias) if s.inventarios_discrepancias is not None else 0},
        {"nombre": "IVA Flujo", "cargado": s.iva_cargados, "ejecutado": s.iva_ejecutado,
         "insumos": [s.df_iva_banco, s.df_iva_aux],
         "n_ok": len(s.iva_conciliados) if s.iva_conciliados is not None else 0,
         "n_pend": (len(s.iva_pend_banco) if s.iva_pend_banco is not None else 0) + (len(s.iva_pend_aux) if s.iva_pend_aux is not None else 0)},
    ]

    total_tasks = len(modulos)
    tasks_no_prep = sum(1 for m in modulos if not m["cargado"])
    tasks_progreso = sum(1 for m in modulos if m["cargado"] and not m["ejecutado"])
    tasks_completado = sum(1 for m in modulos if m["ejecutado"])

    recs_no_prep, recs_progreso, recs_completado = 0, 0, 0
    for m in modulos:
        if m["ejecutado"]:
            recs_completado += m["n_ok"]
            recs_no_prep += m["n_pend"]
        elif m["cargado"]:
            filas = sum(len(df) for df in m["insumos"] if df is not None)
            recs_progreso += filas
    total_recs = recs_no_prep + recs_progreso + recs_completado

    return {
        "modulos": modulos,
        "tasks": {"total": total_tasks, "no_prep": tasks_no_prep, "progreso": tasks_progreso, "completado": tasks_completado},
        "recs": {"total": total_recs, "no_prep": recs_no_prep, "progreso": recs_progreso, "completado": recs_completado},
    }

def _pct(parte, total):
    return (parte / total * 100) if total else 0.0

def construir_clasificacion_pendientes():
    """
    Combina bancos_pendientes + auxiliar_pendientes en una sola tabla con una
    columna 'Departamento' clasificable. A diferencia de una vista resumida,
    esta tabla conserva TODAS las columnas originales del estado de cuenta /
    auxiliar contable (más '_Fecha_Norm' y '_Monto_Norm' como campos auxiliares
    para agrupar y graficar), para poder mostrar los pendientes "tal cual"
    aparecen en su fuente original cuando se hace clic en una gráfica.

    Si ya existía una clasificación previa (de una corrida anterior), conserva
    la asignación de las partidas que sigan siendo las mismas (comparando
    Origen + Fecha + Monto redondeado); las partidas nuevas entran como
    'Sin Asignar'.
    """
    s = st.session_state
    col_fb, col_ff = s.bancos_col_monto_banco, s.bancos_col_fecha_banco
    col_ab, col_af = s.bancos_col_monto_aux, s.bancos_col_fecha_aux
    partes = []

    if s.bancos_pendientes is not None and not s.bancos_pendientes.empty and col_fb and col_ff:
        parte_banco = s.bancos_pendientes.copy().reset_index(drop=True)
        parte_banco.insert(0, "Origen", "Banco")
        parte_banco["_Monto_Norm"] = pd.to_numeric(parte_banco[col_fb], errors='coerce').round(2)
        parte_banco["_Fecha_Norm"] = pd.to_datetime(parte_banco[col_ff], format='mixed', dayfirst=True, errors='coerce').dt.date
        partes.append(parte_banco)
    if s.auxiliar_pendientes is not None and not s.auxiliar_pendientes.empty and col_ab and col_af:
        parte_aux = s.auxiliar_pendientes.copy().reset_index(drop=True)
        parte_aux.insert(0, "Origen", "Auxiliar")
        parte_aux["_Monto_Norm"] = pd.to_numeric(parte_aux[col_ab], errors='coerce').round(2)
        parte_aux["_Fecha_Norm"] = pd.to_datetime(parte_aux[col_af], format='mixed', dayfirst=True, errors='coerce').dt.date
        partes.append(parte_aux)

    if not partes:
        return pd.DataFrame()

    df_combinado = pd.concat(partes, ignore_index=True, sort=False)
    df_combinado["Departamento"] = "Sin Asignar"

    previo = s.bancos_clasificacion_pendientes
    if previo is not None and not previo.empty and "Departamento" in previo.columns:
        mapa_previo = {
            (r["Origen"], r["_Fecha_Norm"], r["_Monto_Norm"]): r["Departamento"]
            for _, r in previo.iterrows()
        }
        df_combinado["Departamento"] = df_combinado.apply(
            lambda r: mapa_previo.get((r["Origen"], r["_Fecha_Norm"], r["_Monto_Norm"]), "Sin Asignar"), axis=1
        )

    columnas_frente = ["Origen", "Departamento", "_Fecha_Norm", "_Monto_Norm"]
    resto = [c for c in df_combinado.columns if c not in columnas_frente]
    return df_combinado[columnas_frente + resto]

def render_dashboard():
    st.write("")
    estado = calcular_estado_modulos()
    tk, rc = estado["tasks"], estado["recs"]

    # ---------- Días restantes (Close clock) ----------
    dias_restantes, dias_label, dias_color = None, "Sin fecha configurada", "#667085"
    if st.session_state.fecha_limite_cierre:
        try:
            fecha_limite = datetime.date.fromisoformat(st.session_state.fecha_limite_cierre)
            dias_restantes = (fecha_limite - datetime.date.today()).days
            if dias_restantes >= 0:
                dias_label, dias_color = "días restantes", "#101828"
            else:
                dias_restantes, dias_label, dias_color = abs(dias_restantes), "días de atraso", "#B42318"
        except ValueError:
            pass

    st.markdown('<div class="bl-wrapper">', unsafe_allow_html=True)

    # ---------- Fila de 5 tarjetas KPI (Close clock / Total / No preparado / En progreso / Completado) ----------
    k1, k2, k3, k4, k5 = st.columns(5)
    with k1:
        valor_dias = f"{dias_restantes}" if dias_restantes is not None else "—"
        st.markdown(f"""<div class="bl-card">
            <div class="bl-card-title">{icono("calendar")} Cierre de Periodo</div>
            <div class="bl-card-value" style="color:{dias_color};">{valor_dias}</div>
            <div class="bl-card-sub">{dias_label}</div>
        </div>""", unsafe_allow_html=True)
    with k2:
        st.markdown(f"""<div class="bl-card">
            <div class="bl-card-title">{icono("clipboard")} Total</div>
            <div class="bl-card-value">{rc['total']:,}</div>
            <div class="bl-subrow"><span>Recs</span><b>{rc['total']:,}</b></div>
            <div class="bl-subrow"><span>Módulos</span><b>{tk['total']}</b></div>
        </div>""", unsafe_allow_html=True)
    with k3:
        st.markdown(f"""<div class="bl-card">
            <div class="bl-card-title">{punto("#F79009")} No preparado</div>
            <div class="bl-card-value">{_pct(rc['no_prep'], rc['total']):.0f}% <span class="bl-card-sub">{rc['no_prep']:,}</span></div>
            <div class="bl-subrow"><span>Recs</span><span><span class="bl-badge bl-badge-orange">{_pct(rc['no_prep'], rc['total']):.0f}%</span>{rc['no_prep']:,}</span></div>
            <div class="bl-subrow"><span>Módulos</span><span><span class="bl-badge bl-badge-orange">{_pct(tk['no_prep'], tk['total']):.0f}%</span>{tk['no_prep']}</span></div>
        </div>""", unsafe_allow_html=True)
    with k4:
        st.markdown(f"""<div class="bl-card">
            <div class="bl-card-title">{punto("#6172F3")} En progreso</div>
            <div class="bl-card-value">{_pct(rc['progreso'], rc['total']):.0f}% <span class="bl-card-sub">{rc['progreso']:,}</span></div>
            <div class="bl-subrow"><span>Recs</span><span><span class="bl-badge bl-badge-blue">{_pct(rc['progreso'], rc['total']):.0f}%</span>{rc['progreso']:,}</span></div>
            <div class="bl-subrow"><span>Módulos</span><span><span class="bl-badge bl-badge-blue">{_pct(tk['progreso'], tk['total']):.0f}%</span>{tk['progreso']}</span></div>
        </div>""", unsafe_allow_html=True)
    with k5:
        st.markdown(f"""<div class="bl-card">
            <div class="bl-card-title">{icono("check")} Completado</div>
            <div class="bl-card-value">{_pct(rc['completado'], rc['total']):.0f}% <span class="bl-card-sub">{rc['completado']:,}</span></div>
            <div class="bl-subrow"><span>Recs</span><span><span class="bl-badge bl-badge-green">{_pct(rc['completado'], rc['total']):.0f}%</span>{rc['completado']:,}</span></div>
            <div class="bl-subrow"><span>Módulos</span><span><span class="bl-badge bl-badge-green">{_pct(tk['completado'], tk['total']):.0f}%</span>{tk['completado']}</span></div>
        </div>""", unsafe_allow_html=True)

    st.markdown("<div style='height:20px;'></div>", unsafe_allow_html=True)

    # ---------- Sección "Reconciliations": barra segmentada, un segmento por módulo ----------
    colores_estado = {"no_prep": "#F79009", "progreso": "#6172F3", "completado": "#12B76A"}
    segmentos_html = ""
    leyenda_html = ""
    ancho_igual = 100 / len(estado["modulos"])
    for m in estado["modulos"]:
        estado_m = "completado" if m["ejecutado"] else ("progreso" if m["cargado"] else "no_prep")
        segmentos_html += f'<div style="width:{ancho_igual}%; background:{colores_estado[estado_m]};" title="{m["nombre"]}"></div>'
        leyenda_html += f'<span><span class="bl-dot" style="background:{colores_estado[estado_m]};"></span>{m["nombre"]}</span>'

    st.markdown(f"""
    <div class="bl-section">
        <div class="bl-section-title">Módulos de Conciliación <span class="bl-count-pill">{tk['total']}</span></div>
        <div style="color:#667085; font-size:13px; margin-top:10px;">Progreso general</div>
        <div style="font-size:28px; font-weight:700; color:#101828; margin-top:2px;">
            {_pct(tk['completado'], tk['total']):.0f}% <span style="font-size:14px; font-weight:500; color:#98A2B3;">{tk['completado']} de {tk['total']} módulos completados</span>
        </div>
        <div class="bl-progress-bar">{segmentos_html}</div>
        <div class="bl-legend">{leyenda_html}</div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("<div style='height:18px;'></div>", unsafe_allow_html=True)

    # ---------- Fila de 4 mini-tarjetas (Pendientes / Atraso / Diferencia sin identificar / Conciliado) ----------
    diferencia_sin_identificar = st.session_state.suma_banco_p + st.session_state.suma_aux_p
    if st.session_state.saldos_discrepancias is not None and not st.session_state.saldos_discrepancias.empty:
        diferencia_sin_identificar += st.session_state.saldos_discrepancias['Diferencia_Calculada'].abs().sum()

    mc1, mc2, mc3, mc4 = st.columns(4)
    with mc1:
        st.markdown(f"""<div class="bl-mini-card" style="border-top-color:#F79009;">
            <div class="bl-mini-title">Pendientes</div>
            <div class="bl-mini-value">{rc['no_prep']:,}</div>
        </div>""", unsafe_allow_html=True)
    with mc2:
        color_atraso = "#B42318" if (dias_restantes is not None and dias_label == "días de atraso") else "#12B76A"
        texto_atraso = f"{dias_restantes} días" if dias_restantes is not None else "N/D"
        st.markdown(f"""<div class="bl-mini-card" style="border-top-color:{color_atraso};">
            <div class="bl-mini-title">{dias_label.capitalize() if dias_restantes is not None else 'Atraso de cierre'}</div>
            <div class="bl-mini-value" style="color:{color_atraso};">{texto_atraso}</div>
        </div>""", unsafe_allow_html=True)
    with mc3:
        st.markdown(f"""<div class="bl-mini-card" style="border-top-color:#F79009;">
            <div class="bl-mini-title">Diferencia sin Identificar</div>
            <div class="bl-mini-value">$ {diferencia_sin_identificar:,.2f}</div>
        </div>""", unsafe_allow_html=True)
    with mc4:
        st.markdown(f"""<div class="bl-mini-card" style="border-top-color:#12B76A;">
            <div class="bl-mini-title">Conciliado</div>
            <div class="bl-mini-value">{_pct(rc['completado'], rc['total']):.0f}%</div>
        </div>""", unsafe_allow_html=True)

    st.markdown("</div>", unsafe_allow_html=True)

    # ---------- Gráficas ejecutivas (Plotly) ----------
    st.write("")
    gcol1, gcol2 = st.columns([2, 1])
    with gcol1:
        df_graf_modulos = pd.DataFrame([
            {"Módulo": m["nombre"],
             "Estado": "Completado" if m["ejecutado"] else ("En progreso" if m["cargado"] else "No preparado"),
             "Filas": (m["n_ok"] + m["n_pend"]) if m["ejecutado"] else (sum(len(d) for d in m["insumos"] if d is not None) if m["cargado"] else 1)}
            for m in estado["modulos"]
        ])
        fig_modulos = px.bar(
            df_graf_modulos, x="Filas", y="Módulo", color="Estado", orientation="h",
            color_discrete_map={"No preparado": "#F79009", "En progreso": "#6172F3", "Completado": "#12B76A"},
            title="Estado por Módulo (filas de datos)",
        )
        fig_modulos.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", font_color="#E6EDF3", legend_title_text="", height=380)
        with st.container(key="chartcard_modulos", border=True):
            st.plotly_chart(fig_modulos, use_container_width=True)
    with gcol2:
        df_dona = pd.DataFrame({
            "Estado": ["No preparado", "En progreso", "Completado"],
            "Módulos": [tk["no_prep"], tk["progreso"], tk["completado"]],
        })
        fig_dona = px.pie(
            df_dona, names="Estado", values="Módulos", hole=0.55,
            color="Estado", color_discrete_map={"No preparado": "#F79009", "En progreso": "#6172F3", "Completado": "#12B76A"},
            title="Módulos por Estado",
        )
        fig_dona.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", font_color="#E6EDF3", height=380)
        with st.container(key="chartcard_dona", border=True):
            st.plotly_chart(fig_dona, use_container_width=True)

    # ---------- Debajo: semáforo de riesgo original + dictamen PDF ----------
    st.write("")
    fases = ["1. Configuración", "2. Carga Insumos", "3. Mapeo Columnas", "4. Reportes y Dictamen"]
    st.progress(st.session_state.fase_progreso / 4, text=f"Progreso del Flujo: **{fases[st.session_state.fase_progreso - 1]}**")
    if st.session_state.bancos_ejecutado:
        st.markdown(f'<div class="section-header">{icono("dashboard")} Indicadores de Riesgo Corporativo</div>', unsafe_allow_html=True)
        total_pendientes = st.session_state.suma_banco_p + st.session_state.suma_aux_p
        porcentaje_riesgo = (total_pendientes / st.session_state.suma_conciliado * 100) if st.session_state.suma_conciliado > 0 else 0
        if porcentaje_riesgo <= 2.0: clase_semaforo, mensaje_semaforo = "kpi-green", f"{punto('#0D1117')}RIESGO BAJO: Libros Alineados."
        elif porcentaje_riesgo <= 5.0: clase_semaforo, mensaje_semaforo = "kpi-yellow", f"{punto('#0D1117')}RIESGO MODERADO: Monitorear partidas."
        else: clase_semaforo, mensaje_semaforo = "kpi-red", f"{punto('#0D1117')}ALERTA - RIESGO ALTO: Desfase crítico."
        st.markdown(f"<div class='kpi-card {clase_semaforo}'>{mensaje_semaforo} ({porcentaje_riesgo:.2f}% desfase)</div>", unsafe_allow_html=True)
        
        m1, m2, m3 = st.columns(3)
        m1.metric("Capital Conciliado", f"$ {st.session_state.suma_conciliado:,.2f}")
        m2.metric("Pendientes Banco", f"$ {st.session_state.suma_banco_p:,.2f}", delta_color="inverse")
        m3.metric("Pendientes Auxiliar", f"$ {st.session_state.suma_aux_p:,.2f}", delta_color="inverse")
        
        pdf_dictamen = generar_dictamen_pdf(st.session_state.empresa, st.session_state.periodo, st.session_state.auditor, st.session_state.suma_conciliado, st.session_state.suma_banco_p, st.session_state.suma_aux_p)
        st.download_button(label=":blue[:material/download:] Descargar Dictamen Certificado (PDF)", data=pdf_dictamen, file_name="Dictamen_Auditoria.pdf", mime="application/pdf", use_container_width=True)
    else: st.info(":blue[:material/diamond:] Suite Inicializada. Usa los módulos superiores para comenzar la auditoría.")

# ==============================================================================
# CONFIGURACIÓN COMPLETA RESTAURADA CON BOTONES DE RESPALDO JSON
# ==============================================================================
def render_configuracion():
    st.write("")
    st.markdown(f'<div class="section-header">{icono("gear")} Panel de Parámetros Globales y Membretes</div>', unsafe_allow_html=True)
    col_m1, col_m2, col_m3 = st.columns(3)
    with col_m1: st.session_state.empresa = st.text_input("Razón Social del Cliente:", value=st.session_state.empresa)
    with col_m2: st.session_state.periodo = st.text_input("Periodo Fiscal:", value=st.session_state.periodo)
    with col_m3: st.session_state.auditor = st.text_input("Auditor Encargado:", value=st.session_state.auditor)
    
    st.markdown("---")
    col_conf1, col_conf2, col_conf3, col_conf4, col_conf5 = st.columns(5)
    with col_conf1: st.session_state.tolerancia = st.slider("Tolerancia Monto ($):", 0.00, 5.00, value=float(st.session_state.tolerancia), step=0.10)
    with col_conf2: st.session_state.tolerancia_dias = st.slider("Tolerancia Fecha (días):", 0, 15, value=int(st.session_state.tolerancia_dias), step=1)
    with col_conf3:
        lista_divisas = ["MXN ($)", "USD ($)", "EUR (€)"]
        st.session_state.divisa = st.selectbox("Divisa Base:", lista_divisas, index=lista_divisas.index(st.session_state.divisa) if st.session_state.divisa in lista_divisas else 0)
    with col_conf4:
        valor_fecha_limite = st.session_state.fecha_limite_cierre
        if isinstance(valor_fecha_limite, str) and valor_fecha_limite:
            try: valor_fecha_limite = datetime.date.fromisoformat(valor_fecha_limite)
            except ValueError: valor_fecha_limite = None
        nueva_fecha = st.date_input("Fecha Límite de Cierre:", value=valor_fecha_limite, format="DD/MM/YYYY")
        st.session_state.fecha_limite_cierre = nueva_fecha.isoformat() if nueva_fecha else None
    with col_conf5:
        st.session_state.tolerancia_inventario = st.slider("Tolerancia Inventario (unidades):", 0.0, 20.0, value=float(st.session_state.tolerancia_inventario), step=0.5)
    
    st.markdown("---")
    logo_file = st.file_uploader("Sube el logotipo (PNG, JPG)", type=["png", "jpg", "jpeg", "webp"], key="logo_config")
    if logo_file is not None:
        nuevos_bytes = logo_file.read()
        if st.session_state.logo_bytes != nuevos_bytes: st.session_state.logo_bytes = nuevos_bytes; st.session_state.fase_progreso = 2; st.rerun()
    if _LOGO_DEFECTO_BYTES is not None and st.session_state.logo_bytes != _LOGO_DEFECTO_BYTES:
        if st.button(":blue[:material/restart_alt:] Restablecer al logo por defecto de TaxFlow-Diamond", key="restablecer_logo"):
            st.session_state.logo_bytes = _LOGO_DEFECTO_BYTES
            st.rerun()

    # RESPALDO JSON COMPLETO — sin excepción de ningún módulo
    st.markdown("---")
    st.subheader(":blue[:material/save:] Copias de Seguridad de la Auditoría (.JSON)")
    st.caption("El respaldo incluye TODOS los módulos sin excepción: los 8 de conciliación (Bancos, XML, Saldos, Multidivisa, Nómina, Inventarios, IVA, Activo Fijo), Razones Financieras, Checklist SAT, Checklist PBC, Revisión y Aprobación, Bitácora de Auditoría, Configuración, auditorías guardadas (Multiempresa) y la base de Usuarios del sistema (incluye contraseñas cifradas).")
    col_j1, col_j2 = st.columns(2)
    with col_j1:
        llaves_respaldo_completo = list(variables_sesion.keys()) + ["usuarios_sistema"]
        respaldo_dinamico = _serializar_estado({llave: st.session_state[llave] for llave in llaves_respaldo_completo})
        st.download_button(label=":blue[:material/download:] Descargar Respaldo JSON Completo", data=json.dumps(respaldo_dinamico), file_name="Backup_TaxFlow.json", mime="application/json", use_container_width=True, on_click=lambda: registrar_evento("Configuración", "Descargó respaldo JSON completo (todos los módulos)"))

    with col_j2:
        archivo_json_cargado = st.file_uploader("Sube tu archivo de respaldo (.JSON)", type=["json"], key="json_config_uploader")
        restaurar_usuarios = st.checkbox("Restaurar también la base de Usuarios (usuarios, roles, contraseñas)", value=False, key="restaurar_usuarios_chk")
        if not restaurar_usuarios:
            st.caption(":orange[:material/warning:] Por seguridad, restaurar usuarios está desmarcado por defecto — así no se sobreescribe accidentalmente tu lista de usuarios actual (incluyendo tu propia contraseña) al cargar un respaldo de otra auditoría.")
        if archivo_json_cargado is not None:
            try:
                datos_restaurados = json.load(archivo_json_cargado)
                for llave, valor in _deserializar_estado(datos_restaurados).items():
                    if llave == "usuarios_sistema" and not restaurar_usuarios:
                        continue
                    st.session_state[llave] = valor
                registrar_evento("Configuración", f"Restauró la sesión desde un respaldo JSON (usuarios {'incluidos' if restaurar_usuarios else 'excluidos'})")
                st.success(":green[:material/check:] Ecosistema restaurado desde el JSON con éxito.")
                st.rerun()
            except Exception as e: st.error(f"Error JSON: {e}")
def render_bancos():
    st.write("")
    st.markdown(f'<div class="section-header">{icono("bank")} Módulo Bancario: Estado de Cuenta vs Auxiliar Contable Interno</div>', unsafe_allow_html=True)
    if not st.session_state.bancos_cargados:
        c_b1, c_b2 = st.columns(2)
        with c_b1: b_file = st.file_uploader("Sube Estado de Cuenta Bancario", type=["csv", "xlsx"], key="b_u")
        with c_b2: a_file = st.file_uploader("Sube Auxiliar Contable", type=["csv", "xlsx"], key="a_u")
        if b_file and a_file: st.session_state.df_banco = leer_archivo_contable(b_file); st.session_state.df_auxiliar = leer_archivo_contable(a_file); st.session_state.bancos_cargados = True; st.session_state.fase_progreso = 3; st.rerun()
    else:
        st.success(":green[:material/flag:] Insumos bancarios indexados.")
        if st.button(":blue[:material/refresh:] Cargar nuevos archivos de banco", key="reset_b"): st.session_state.bancos_cargados, st.session_state.bancos_ejecutado = False, False; st.session_state.fase_progreso = 1; st.rerun()
    if st.session_state.bancos_cargados:
        df_b, df_a = st.session_state.df_banco, st.session_state.df_auxiliar
        c1, c2, c3, c4 = st.columns(4)
        with c1: cb_m = st.selectbox("Monto BANCO:", df_b.columns, key="cb_m")
        with c2: cb_f = st.selectbox("Fecha BANCO:", df_b.columns, key="cb_f")
        with c3: ca_m = st.selectbox("Monto AUXILIAR:", df_a.columns, key="ca_m")
        with c4: ca_f = st.selectbox("Fecha AUXILIAR:", df_a.columns, key="ca_f")
        
        st.markdown("---")
        st.subheader(":violet[:material/shield:] Panel de Pre-Validación de Insumos")
        col_v1, col_v2 = st.columns(2)
        with col_v1:
            col_rfc_b = st.selectbox("Columna de RFC en archivo BANCO (Opcional):", ["Ninguna"] + list(df_b.columns))
            if col_rfc_b != "Ninguna" and not df_b[~df_b[col_rfc_b].apply(validar_rfc)].empty: st.warning(":orange[:material/warning:] RFCs inválidos en Banco.")
        with col_v2:
            col_rfc_a = st.selectbox("Columna de RFC en archivo AUXILIAR (Opcional):", ["Ninguna"] + list(df_a.columns))
            if col_rfc_a != "Ninguna" and not df_a[~df_a[col_rfc_a].apply(validar_rfc)].empty: st.warning(":orange[:material/warning:] RFCs inválidos en Auxiliar.")

        if st.button(":green[:material/play_arrow:] Ejecutar Algoritmo de Conciliación Diamond", type="primary", use_container_width=True):
            try:
                resultado = conciliar_dos_fuentes(
                    df_banco=df_b, df_auxiliar=df_a,
                    col_monto_banco=cb_m, col_fecha_banco=cb_f,
                    col_monto_aux=ca_m, col_fecha_aux=ca_f,
                    tolerancia_monto=float(st.session_state.tolerancia),
                    tolerancia_dias=int(st.session_state.tolerancia_dias),
                )
                st.session_state.df_conciliados = resultado["conciliados"]
                st.session_state.bancos_pendientes = resultado["pendientes_banco"]
                st.session_state.auxiliar_pendientes = resultado["pendientes_auxiliar"]
                st.session_state.bancos_col_fecha_banco = cb_f
                st.session_state.bancos_col_fecha_aux = ca_f
                st.session_state.bancos_col_monto_banco = cb_m
                st.session_state.bancos_col_monto_aux = ca_m
                st.session_state.suma_conciliado = resultado["resumen"]["suma_conciliado"]
                st.session_state.suma_banco_p = resultado["resumen"]["suma_banco_pendiente"]
                st.session_state.suma_aux_p = resultado["resumen"]["suma_aux_pendiente"]
                st.session_state.bancos_ejecutado = True
                st.session_state.fase_progreso = 4
                registrar_evento("Bancos vs Auxiliar", f"Ejecutó la conciliación ({resultado['resumen']['num_exactos']} exactos, {resultado['resumen']['num_aproximados']} aproximados, {resultado['resumen']['num_pendientes_banco']+resultado['resumen']['num_pendientes_auxiliar']} pendientes)")
                st.rerun()
            except Exception as e:
                st.error(f":orange[:material/warning:] No se pudo ejecutar la conciliación. Revisa que las columnas de fecha y monto sean correctas. Detalle: {e}")
        if st.session_state.bancos_ejecutado:
            if 'Tipo_Match' in st.session_state.df_conciliados.columns and not st.session_state.df_conciliados.empty:
                n_exactos = int((st.session_state.df_conciliados['Tipo_Match'] == 'Exacto (fecha + monto)').sum())
                n_aprox = int((st.session_state.df_conciliados['Tipo_Match'] == 'Aproximado (dentro de tolerancia)').sum())
                st.caption(f":blue[:material/search:] Trazabilidad: {n_exactos} partidas por match exacto (misma fecha y monto) · {n_aprox} por match aproximado (dentro de tolerancia). Cada partida se usa una sola vez, nunca se repite en ambos lados.")
            buffer = io.BytesIO()
            with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
                st.session_state.df_conciliados.to_excel(writer, sheet_name='Partidas_Conciliadas', index=False)
                st.session_state.bancos_pendientes.to_excel(writer, sheet_name='Pendientes_Solo_Banco', index=False)
                st.session_state.auxiliar_pendientes.to_excel(writer, sheet_name='Pendientes_Solo_Auxiliar', index=False)
            st.download_button(label=":blue[:material/download:] Descargar Libro de Conciliación Completo (.XLSX)", data=buffer.getvalue(), file_name="Reporte_Bancos.xlsx", use_container_width=True)
            tab1, tab2, tab3 = st.tabs([":green[:material/check_circle:] Conciliados", ":orange[:material/warning:] Solo Banco", ":blue[:material/menu_book:] Solo Auxiliar"])
            with tab1: st.dataframe(st.session_state.df_conciliados, use_container_width=True)
            with tab2: st.dataframe(st.session_state.bancos_pendientes, use_container_width=True)
            with tab3: st.dataframe(st.session_state.auxiliar_pendientes, use_container_width=True)

        # ---------- Clasificación de pendientes por Departamento ----------
        if st.session_state.bancos_ejecutado and ((st.session_state.bancos_pendientes is not None and not st.session_state.bancos_pendientes.empty) or (st.session_state.auxiliar_pendientes is not None and not st.session_state.auxiliar_pendientes.empty)):
            st.markdown("---")
            st.markdown(f'<div class="section-header">{icono("users")} Clasificación de Pendientes por Departamento</div>', unsafe_allow_html=True)
            st.caption("Asigna cada partida pendiente (Banco + Auxiliar) a un departamento responsable de registrarla. Haz clic en cualquier gráfica para ver la lista de pendientes de ese departamento, tal cual aparece en su fuente original (estado de cuenta o auxiliar).")

            colores_dep = st.session_state.bancos_departamentos_colores
            with st.expander(":violet[:material/palette:] Configurar departamentos y colores"):
                nuevos_colores = {}
                cols_color = st.columns(len(colores_dep))
                for col, (depto, color) in zip(cols_color, colores_dep.items()):
                    with col:
                        nuevos_colores[depto] = st.color_picker(depto, value=color, key=f"color_{depto}")
                nuevo_depto = st.text_input("Agregar nuevo departamento:", key="nuevo_depto_input")
                if st.button(":green[:material/add:] Agregar departamento", key="agregar_depto_btn") and nuevo_depto.strip():
                    nuevos_colores[nuevo_depto.strip()] = "#10B981"
                st.session_state.bancos_departamentos_colores = nuevos_colores
                colores_dep = nuevos_colores

            if st.session_state.bancos_clasificacion_pendientes is None or st.button(":blue[:material/refresh:] Recalcular tabla de pendientes", key="recalcular_clasificacion"):
                st.session_state.bancos_clasificacion_pendientes = construir_clasificacion_pendientes()

            df_clasificado = st.session_state.bancos_clasificacion_pendientes
            if df_clasificado is not None and not df_clasificado.empty:
                st.markdown("###### Editor de clasificación (incluye todas las columnas originales)")
                df_editado = st.data_editor(
                    df_clasificado,
                    use_container_width=True,
                    key="editor_clasificacion_bancos",
                    column_config={
                        "Departamento": st.column_config.SelectboxColumn("Departamento", options=list(colores_dep.keys())),
                        "_Monto_Norm": st.column_config.NumberColumn("Monto", format="$ %.2f"),
                        "_Fecha_Norm": st.column_config.DateColumn("Fecha", format="DD/MM/YYYY"),
                    },
                )
                st.session_state.bancos_clasificacion_pendientes = df_editado

                # Vista de solo lectura con color de fondo por departamento
                def _color_fila(fila):
                    color = colores_dep.get(fila["Departamento"], "#6B7280")
                    return [f"background-color:{color}22; color:#E6EDF3"] * len(fila)
                st.markdown("###### Vista con color por departamento")
                st.dataframe(df_editado.style.apply(_color_fila, axis=1), use_container_width=True)

                # ---------- Tarjetas por departamento (clicables) ----------
                resumen_dep = df_editado.groupby("Departamento").agg(Partidas=("_Monto_Norm", "count"), Monto_Total=("_Monto_Norm", "sum")).reset_index()
                cols_tarjetas = st.columns(len(resumen_dep)) if len(resumen_dep) > 0 else []
                for col, (_, fila) in zip(cols_tarjetas, resumen_dep.iterrows()):
                    depto_tarjeta = fila["Departamento"]
                    color = colores_dep.get(depto_tarjeta, "#6B7280")
                    seleccionada = st.session_state.bancos_departamento_manual == depto_tarjeta
                    with col:
                        sombra = f"box-shadow:0 0 0 2px {color};" if seleccionada else ""
                        st.markdown(f"""<div class="bl-mini-card" style="border-top-color:{color}; {sombra}">
                            <div class="bl-mini-title">{depto_tarjeta}</div>
                            <div class="bl-mini-value">{int(fila['Partidas'])} partidas</div>
                            <div class="bl-card-sub">$ {fila['Monto_Total']:,.2f}</div>
                        </div>""", unsafe_allow_html=True)
                        etiqueta_btn = ":material/filter_list_off: Quitar filtro" if seleccionada else ":material/filter_list: Ver pendientes"
                        if st.button(etiqueta_btn, key=f"filtro_tarjeta_{depto_tarjeta}", use_container_width=True):
                            st.session_state.bancos_departamento_manual = None if seleccionada else depto_tarjeta
                            st.rerun()

                st.markdown("<div style='height:16px;'></div>", unsafe_allow_html=True)
                st.caption(":orange[:material/touch_app:] Haz clic en una tarjeta (botón 'Ver pendientes') o en una barra/dona/segmento para ver el detalle de ese departamento.")

                # ---------- 4 gráficas clicables (custom_data lleva el Departamento) ----------
                eventos = []
                g1, g2 = st.columns(2)
                with g1:
                    fig_monto = px.bar(
                        resumen_dep, x="Departamento", y="Monto_Total", color="Departamento",
                        color_discrete_map=colores_dep, title="Monto Pendiente por Departamento",
                        custom_data=["Departamento"],
                    )
                    fig_monto.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", font_color="#E6EDF3", showlegend=False, height=380)
                    with st.container(key="chartcard_monto_depto", border=True):
                        eventos.append(st.plotly_chart(fig_monto, use_container_width=True, on_select="rerun", key="chart_monto_depto"))
                with g2:
                    fig_partidas = px.pie(
                        resumen_dep, names="Departamento", values="Partidas", hole=0.55,
                        color="Departamento", color_discrete_map=colores_dep, title="Partidas Pendientes por Departamento",
                        custom_data=["Departamento"],
                    )
                    fig_partidas.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", font_color="#E6EDF3", height=380)
                    with st.container(key="chartcard_partidas_depto", border=True):
                        eventos.append(st.plotly_chart(fig_partidas, use_container_width=True, on_select="rerun", key="chart_partidas_depto"))

                g3, g4 = st.columns(2)
                with g3:
                    resumen_origen_dep = df_editado.groupby(["Departamento", "Origen"]).size().reset_index(name="Cantidad")
                    fig_origen = px.bar(
                        resumen_origen_dep, x="Departamento", y="Cantidad", color="Origen", barmode="group",
                        title="Pendientes Banco vs Auxiliar por Departamento",
                        custom_data=["Departamento"],
                    )
                    fig_origen.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", font_color="#E6EDF3", height=380)
                    with st.container(key="chartcard_origen_depto", border=True):
                        eventos.append(st.plotly_chart(fig_origen, use_container_width=True, on_select="rerun", key="chart_origen_depto"))
                with g4:
                    df_antiguedad = df_editado.dropna(subset=["_Fecha_Norm"]).copy()
                    if not df_antiguedad.empty:
                        df_antiguedad["Dias"] = df_antiguedad["_Fecha_Norm"].apply(lambda f: (datetime.date.today() - f).days)
                        bins = [-1, 30, 60, 90, 10_000]
                        etiquetas = ["0-30 días", "31-60 días", "61-90 días", "90+ días"]
                        df_antiguedad["Antigüedad"] = pd.cut(df_antiguedad["Dias"], bins=bins, labels=etiquetas)
                        resumen_antiguedad = df_antiguedad.groupby(["Antigüedad", "Departamento"], observed=True).size().reset_index(name="Cantidad")
                        fig_antiguedad = px.bar(
                            resumen_antiguedad, x="Antigüedad", y="Cantidad", color="Departamento",
                            color_discrete_map=colores_dep, title="Antigüedad de Pendientes por Departamento",
                            custom_data=["Departamento"],
                        )
                        fig_antiguedad.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", font_color="#E6EDF3", height=380)
                        with st.container(key="chartcard_antiguedad_depto", border=True):
                            eventos.append(st.plotly_chart(fig_antiguedad, use_container_width=True, on_select="rerun", key="chart_antiguedad_depto"))
                    else:
                        st.info(":blue[:material/info:] No hay fechas válidas para calcular antigüedad.")

                # ---------- Drill-down: combinar clic en tarjeta + clic en cualquiera de las 4 gráficas ----------
                departamento_click = None
                for evento in eventos:
                    puntos = evento.selection.get("points", []) if evento and getattr(evento, "selection", None) else []
                    if puntos:
                        customdata = puntos[0].get("customdata")
                        if customdata:
                            departamento_click = customdata[0]
                            break

                # El clic en una gráfica también fija el filtro manual (así ambos
                # caminos quedan sincronizados y el botón de la tarjeta refleja
                # el estado correcto en el siguiente rerun).
                if departamento_click:
                    st.session_state.bancos_departamento_manual = departamento_click

                departamento_final = departamento_click or st.session_state.bancos_departamento_manual

                if departamento_final:
                    st.markdown("---")
                    color_sel = colores_dep.get(departamento_final, "#6B7280")
                    st.markdown(
                        f'<div class="section-header">{icono("clipboard")} Pendientes por Registrar — '
                        f'<span style="color:{color_sel};">{departamento_final}</span></div>',
                        unsafe_allow_html=True,
                    )
                    filtro = df_editado[df_editado["Departamento"] == departamento_final]
                    filas_banco = filtro[filtro["Origen"] == "Banco"]
                    filas_aux = filtro[filtro["Origen"] == "Auxiliar"]

                    dcol1, dcol2 = st.columns(2)
                    with dcol1:
                        st.markdown("###### :blue[:material/account_balance:] Tal cual aparece en el Estado de Cuenta")
                        if not filas_banco.empty and st.session_state.df_banco is not None:
                            columnas_banco = [c for c in st.session_state.df_banco.columns if c in filas_banco.columns]
                            st.dataframe(filas_banco[columnas_banco], use_container_width=True)
                        else:
                            st.caption("Sin pendientes de banco en este departamento.")
                    with dcol2:
                        st.markdown("###### :blue[:material/menu_book:] Tal cual aparece en el Auxiliar Contable")
                        if not filas_aux.empty and st.session_state.df_auxiliar is not None:
                            columnas_aux = [c for c in st.session_state.df_auxiliar.columns if c in filas_aux.columns]
                            st.dataframe(filas_aux[columnas_aux], use_container_width=True)
                        else:
                            st.caption("Sin pendientes de auxiliar en este departamento.")

def render_xml():
    st.write("")
    st.markdown(f'<div class="section-header">{icono("document")} Auditoría Fiscal: Comprobantes XML vs Auxiliar de Contabilidad</div>', unsafe_allow_html=True)
    if not st.session_state.xml_cargados:
        cx_1, cx_2 = st.columns(2)
        with cx_1: x_file = st.file_uploader("Sube Reporte de Facturas", type=["csv", "xlsx"], key="x_u")
        with cx_2: cg_file = st.file_uploader("Sube Auxiliar de Gastos", type=["csv", "xlsx"], key="cg_u")
        if x_file and cg_file: st.session_state.df_xml_gastos = leer_archivo_contable(x_file); st.session_state.df_aux_gastos = leer_archivo_contable(cg_file); st.session_state.xml_cargados = True; st.rerun()
    else:
        st.success(":green[:material/flag:] Insumos de facturación indexados.")
        if st.button(":blue[:material/refresh:] Cargar nuevos archivos de XML", key="reset_xml"): st.session_state.xml_cargados, st.session_state.xml_ejecutado = False, False; st.rerun()
    if st.session_state.xml_cargados:
        df_xml, df_cg = st.session_state.df_xml_gastos, st.session_state.df_aux_gastos
        cx1, cx2, cx3, cx4 = st.columns(4)
        with cx1: xml_m = st.selectbox("Monto XML:", df_xml.columns, key="xml_m")
        with cx2: xml_f = st.selectbox("Fecha XML:", df_xml.columns, key="xml_f")
        with cx3: cont_m = st.selectbox("Monto Auxiliar Gasto:", df_cg.columns, key="cont_m")
        with cx4: cont_f = st.selectbox("Fecha Auxiliar Gasto:", df_cg.columns, key="cont_f")
        if st.button(":green[:material/play_arrow:] Cruce XML vs Contabilidad", type="primary", use_container_width=True):
            try:
                resultado = conciliar_dos_fuentes(
                    df_banco=df_xml, df_auxiliar=df_cg,
                    col_monto_banco=xml_m, col_fecha_banco=xml_f,
                    col_monto_aux=cont_m, col_fecha_aux=cont_f,
                    tolerancia_monto=float(st.session_state.tolerancia),
                    tolerancia_dias=int(st.session_state.tolerancia_dias),
                )
                st.session_state.xml_conciliados = resultado["conciliados"]
                st.session_state.xml_pend_xml = resultado["pendientes_banco"]
                st.session_state.xml_pend_aux = resultado["pendientes_auxiliar"]
                st.session_state.xml_ejecutado = True
                registrar_evento("XML vs Contabilidad", f"Ejecutó el cruce ({len(resultado['conciliados'])} conciliadas, {len(resultado['pendientes_banco'])+len(resultado['pendientes_auxiliar'])} pendientes)")
                st.rerun()
            except Exception as e:
                st.error(f":orange[:material/warning:] No se pudo cruzar XML vs Contabilidad. Revisa las columnas de fecha/monto. Detalle: {e}")
        if st.session_state.xml_ejecutado:
            if 'Tipo_Match' in st.session_state.xml_conciliados.columns and not st.session_state.xml_conciliados.empty:
                n_exactos = int((st.session_state.xml_conciliados['Tipo_Match'] == 'Exacto (fecha + monto)').sum())
                n_aprox = int((st.session_state.xml_conciliados['Tipo_Match'] == 'Aproximado (dentro de tolerancia)').sum())
                st.caption(f":blue[:material/search:] Trazabilidad: {n_exactos} facturas por match exacto · {n_aprox} por match aproximado. Cada factura se usa una sola vez.")
            buffer_xml = io.BytesIO()
            with pd.ExcelWriter(buffer_xml, engine='openpyxl') as writer:
                st.session_state.xml_conciliados.to_excel(writer, sheet_name='Conciliados', index=False)
                st.session_state.xml_pend_xml.to_excel(writer, sheet_name='Pendientes_Solo_XML', index=False)
                st.session_state.xml_pend_aux.to_excel(writer, sheet_name='Pendientes_Solo_Auxiliar', index=False)
            st.download_button(label=":blue[:material/download:] Descargar Cruce XML vs Contabilidad (.XLSX)", data=buffer_xml.getvalue(), file_name="Reporte_XML.xlsx", use_container_width=True)
            tx1, tx2, tx3 = st.tabs([":green[:material/check_circle:] Conciliados", ":orange[:material/warning:] Solo XML (posible omisión contable)", ":blue[:material/menu_book:] Solo Auxiliar (posible CFDI faltante)"])
            with tx1: st.dataframe(st.session_state.xml_conciliados, use_container_width=True)
            with tx2: st.dataframe(st.session_state.xml_pend_xml, use_container_width=True)
            with tx3: st.dataframe(st.session_state.xml_pend_aux, use_container_width=True)

def render_saldos():
    st.write("")
    st.markdown(f'<div class="section-header">{icono("invoice")} Herramienta de Auditoría de Cartera: Clientes y Proveedores</div>', unsafe_allow_html=True)
    if not st.session_state.saldos_cargados:
        cs_1, cs_2 = st.columns(2)
        with cs_1: sg_file = st.file_uploader("Sube Reporte de Saldos Globales (ERP)", type=["csv", "xlsx"], key="sg_u_new")
        with cs_2: fd_file = st.file_uploader("Sube Desglose de Facturas / Antigüedad", type=["csv", "xlsx"], key="fd_u_new")
        if sg_file and fd_file: st.session_state.df_saldos_globales = leer_archivo_contable(sg_file); st.session_state.df_facturas_detalle = leer_archivo_contable(fd_file); st.session_state.saldos_cargados = True; st.rerun()
    if st.session_state.saldos_cargados:
        df_sg, df_fd = st.session_state.df_saldos_globales, st.session_state.df_facturas_detalle
        col_s1, col_s2, col_s3 = st.columns(3); id_cte = st.selectbox("Columna Identificador (Código/RFC):", df_sg.columns, key="id_cte_new"); sg_m = st.selectbox("Monto Saldo Global Contable:", df_sg.columns, key="sg_m_new"); fd_m = st.selectbox("Monto Factura en Desglose:", df_fd.columns, key="fd_m_new")
        if st.button(":green[:material/play_arrow:] Ejecutar Cruce de Antigüedad de Saldos", type="primary", use_container_width=True):
            df_sg_num = df_sg.copy()
            df_sg_num[sg_m] = pd.to_numeric(df_sg_num[sg_m], errors='coerce').fillna(0)
            # Agrupamos también el lado de saldos globales por cliente: si el ERP
            # trae al mismo cliente en más de una fila, un merge directo lo
            # duplicaría contra el detalle de facturas (mismo problema de fondo
            # que el many-to-many de Nómina/IVA, aquí por ID repetido en vez de
            # monto repetido).
            df_sg_grouped = df_sg_num.groupby(id_cte, as_index=False).agg({sg_m: 'sum', **{c: 'first' for c in df_sg_num.columns if c not in [id_cte, sg_m]}})
            df_fd_grouped = df_fd.groupby(id_cte)[fd_m].sum().reset_index()
            df_fd_grouped.columns = [id_cte, 'Suma_Detalle_Facturas']
            df_cruce = pd.merge(df_sg_grouped, df_fd_grouped, on=id_cte, how='outer')
            df_cruce['Saldo_Global_Num'] = pd.to_numeric(df_cruce[sg_m], errors='coerce').fillna(0)
            df_cruce['Suma_Detalle_Num'] = pd.to_numeric(df_cruce['Suma_Detalle_Facturas'], errors='coerce').fillna(0)
            df_cruce['Diferencia_Calculada'] = (df_cruce['Saldo_Global_Num'] - df_cruce['Suma_Detalle_Num']).round(2)
            st.session_state.saldos_conciliados = df_cruce[df_cruce['Diferencia_Calculada'].abs() <= st.session_state.tolerancia]
            st.session_state.saldos_discrepancias = df_cruce[df_cruce['Diferencia_Calculada'].abs() > st.session_state.tolerancia]
            st.session_state.saldos_ejecutado = True
            registrar_evento("Clientes y Proveedores", f"Ejecutó el cruce de antigüedad ({len(st.session_state.saldos_conciliados)} correctos, {len(st.session_state.saldos_discrepancias)} discrepancias)")
            st.rerun()
        if st.session_state.saldos_ejecutado:
            t_s1, t_s2 = st.tabs([":green[:material/check_circle:] Saldos Correctos", ":orange[:material/warning:] Discrepancias Encontradas"])
            with t_s1: st.dataframe(st.session_state.saldos_conciliados, use_container_width=True)
            with t_s2: st.dataframe(st.session_state.saldos_discrepancias, use_container_width=True)
def render_multidivisa():
    st.write("")
    st.markdown(f'<div class="section-header">{icono("globe")} Herramienta Cambiaria: Conciliación de Cuentas en Dólares (USD)</div>', unsafe_allow_html=True)
    st.session_state.tc_auditoria_val = st.number_input("Tipo de Cambio (TC) de Cierre Mensual:", min_value=1.0000, value=float(st.session_state.tc_auditoria_val), step=0.0100, key="tc_num_input")
    if not st.session_state.divisa_cargados:
        cv_1, cv_2 = st.columns(2)
        with cv_1: de_file = st.file_uploader("Sube Estado de Cuenta Extranjero (USD)", type=["csv", "xlsx"], key="de_u_new")
        with cv_2: dn_file = st.file_uploader("Sube Registro en Moneda Nacional (Pólizas)", type=["csv", "xlsx"], key="dn_u_new")
        if de_file and dn_file: st.session_state.df_divisa_ext = leer_archivo_contable(de_file); st.session_state.df_divisa_nac = leer_archivo_contable(dn_file); st.session_state.divisa_cargados = True; st.rerun()
    else:
        st.success(":green[:material/flag:] Papeles de divisas extranjeras indexados.")
        if st.button(":blue[:material/refresh:] Reestablecer Módulo Multidivisa", key="reset_v_new"): st.session_state.divisa_cargados, st.session_state.divisa_ejecutado = False, False; st.rerun()
    if st.session_state.divisa_cargados:
        df_ext, df_nac = st.session_state.df_divisa_ext, st.session_state.df_divisa_nac
        col_v1, col_v2, col_v3, col_v4 = st.columns(4)
        with col_v1: de_m = st.selectbox("Monto en Dólares (USD):", df_ext.columns, key="de_m_new")
        with col_v2: de_f = st.selectbox("Fecha (USD):", df_ext.columns, key="de_f_new")
        with col_v3: dn_m = st.selectbox("Monto en Moneda Nacional (MXN):", df_nac.columns, key="dn_m_new")
        with col_v4: dn_f = st.selectbox("Fecha (MXN):", df_nac.columns, key="dn_f_new")
        st.caption("ℹ️ El monto en USD se convierte primero a MXN con el tipo de cambio de arriba, y ESE valor convertido es el que se concilia contra tu registro en pesos (antes se comparaban los números crudos de ambas monedas, lo cual no tiene sentido matemático).")
        if st.button(":green[:material/play_arrow:] Calcular Fluctuación Cambiaria Analítica", type="primary", use_container_width=True):
            try:
                df_ext_c = df_ext.copy()
                df_ext_c['Monto_Convertido_MXN'] = pd.to_numeric(df_ext_c[de_m], errors='coerce').fillna(0).abs() * float(st.session_state.tc_auditoria_val)
                # Tolerancia de fluctuación cambiaria: el tipo de cambio "de cierre"
                # casi nunca es idéntico al tipo de cambio real de cada operación,
                # así que usamos una tolerancia más amplia (relativa al TC) además
                # de la tolerancia de monto normal configurada.
                tolerancia_cambiaria = max(float(st.session_state.tolerancia), float(st.session_state.tc_auditoria_val) * 0.02)
                resultado = conciliar_dos_fuentes(
                    df_banco=df_ext_c, df_auxiliar=df_nac,
                    col_monto_banco='Monto_Convertido_MXN', col_fecha_banco=de_f,
                    col_monto_aux=dn_m, col_fecha_aux=dn_f,
                    tolerancia_monto=tolerancia_cambiaria,
                    tolerancia_dias=int(st.session_state.tolerancia_dias),
                )
                conciliados = resultado["conciliados"]
                if not conciliados.empty:
                    conciliados['Valor_Contable_Esperado'] = conciliados['Monto_Limpio_Banco'].round(2)
                    conciliados['Monto_Local_Real'] = conciliados['Monto_Limpio_Auxiliar'].round(2)
                    conciliados['Diferencia_Fluctuacion'] = (conciliados['Valor_Contable_Esperado'] - conciliados['Monto_Local_Real']).round(2)
                st.session_state.divisa_conciliados = conciliados
                st.session_state.divisa_pend_ext = resultado["pendientes_banco"]
                st.session_state.divisa_pend_nac = resultado["pendientes_auxiliar"]
                st.session_state.divisa_ejecutado = True
                registrar_evento("Multidivisa USD", f"Calculó fluctuación cambiaria ({len(conciliados)} conciliadas, TC={st.session_state.tc_auditoria_val})")
                st.rerun()
            except Exception as e:
                st.error(f":orange[:material/warning:] No se pudo calcular la fluctuación cambiaria. Revisa las columnas de fecha/monto. Detalle: {e}")
        if st.session_state.divisa_ejecutado:
            tolerancia_cambiaria_mostrar = max(float(st.session_state.tolerancia), float(st.session_state.tc_auditoria_val) * 0.02)
            if 'Tipo_Match' in st.session_state.divisa_conciliados.columns and not st.session_state.divisa_conciliados.empty:
                n_exactos = int((st.session_state.divisa_conciliados['Tipo_Match'] == 'Exacto (fecha + monto)').sum())
                n_aprox = int((st.session_state.divisa_conciliados['Tipo_Match'] == 'Aproximado (dentro de tolerancia)').sum())
                st.caption(f":blue[:material/search:] Trazabilidad: {n_exactos} operaciones por match exacto · {n_aprox} por match aproximado (tolerancia cambiaria ± {tolerancia_cambiaria_mostrar:.2f} MXN).")
            buffer_div = io.BytesIO()
            with pd.ExcelWriter(buffer_div, engine='openpyxl') as writer:
                st.session_state.divisa_conciliados.to_excel(writer, sheet_name='Conciliados', index=False)
                st.session_state.divisa_pend_ext.to_excel(writer, sheet_name='Pendientes_Solo_USD', index=False)
                st.session_state.divisa_pend_nac.to_excel(writer, sheet_name='Pendientes_Solo_MXN', index=False)
            st.download_button(label=":blue[:material/download:] Descargar Conciliación Cambiaria (.XLSX)", data=buffer_div.getvalue(), file_name="Reporte_Multidivisa.xlsx", use_container_width=True)
            td1, td2, td3 = st.tabs([":green[:material/check_circle:] Conciliados", ":orange[:material/warning:] Solo USD", ":blue[:material/menu_book:] Solo MXN"])
            with td1: st.dataframe(st.session_state.divisa_conciliados, use_container_width=True)
            with td2: st.dataframe(st.session_state.divisa_pend_ext, use_container_width=True)
            with td3: st.dataframe(st.session_state.divisa_pend_nac, use_container_width=True)

def render_nomina():
    st.write("")
    st.markdown(f'<div class="section-header">{icono("badge")} Auditoría de Nómina: CFDI Timbrados vs Auxiliar</div>', unsafe_allow_html=True)
    if not st.session_state.nomina_cargados:
        cn_1, cn_2 = st.columns(2)
        with cn_1: n_xml = st.file_uploader("Sube XML Nómina", type=["csv", "xlsx"], key="nx")
        with cn_2: n_aux = st.file_uploader("Sube Auxiliar Sueldos", type=["csv", "xlsx"], key="na")
        if n_xml and n_aux: st.session_state.df_cfdi_nomina = leer_archivo_contable(n_xml); st.session_state.df_aux_nomina = leer_archivo_contable(n_aux); st.session_state.nomina_cargados = True; st.rerun()
    else:
        st.success(":green[:material/flag:] Insumos de nómina indexados.")
        if st.button(":blue[:material/refresh:] Cargar nuevos archivos de nómina", key="reset_n"): st.session_state.nomina_cargados, st.session_state.nomina_ejecutado = False, False; st.rerun()
    if st.session_state.nomina_cargados:
        df_nx, df_na = st.session_state.df_cfdi_nomina, st.session_state.df_aux_nomina
        cn1, cn2, cn3, cn4 = st.columns(4)
        with cn1: nx_m = st.selectbox("Monto CFDI:", df_nx.columns, key="nx_m")
        with cn2: nx_f = st.selectbox("Fecha CFDI:", df_nx.columns, key="nx_f")
        with cn3: na_m = st.selectbox("Monto Libros:", df_na.columns, key="na_m")
        with cn4: na_f = st.selectbox("Fecha Libros:", df_na.columns, key="na_f")
        if st.button(":green[:material/play_arrow:] Conciliar Nóminas", type="primary", use_container_width=True):
            try:
                resultado = conciliar_dos_fuentes(
                    df_banco=df_nx, df_auxiliar=df_na,
                    col_monto_banco=nx_m, col_fecha_banco=nx_f,
                    col_monto_aux=na_m, col_fecha_aux=na_f,
                    tolerancia_monto=float(st.session_state.tolerancia),
                    tolerancia_dias=int(st.session_state.tolerancia_dias),
                )
                st.session_state.nomina_conciliados = resultado["conciliados"]
                st.session_state.nomina_pend_cfdi = resultado["pendientes_banco"]
                st.session_state.nomina_pend_aux = resultado["pendientes_auxiliar"]
                st.session_state.nomina_ejecutado = True
                registrar_evento("Nómina CFDI", f"Conciló nómina ({len(resultado['conciliados'])} recibos conciliados)")
                st.rerun()
            except Exception as e:
                st.error(f":orange[:material/warning:] No se pudo conciliar la nómina. Revisa las columnas de fecha/monto. Detalle: {e}")
        if st.session_state.nomina_ejecutado:
            if 'Tipo_Match' in st.session_state.nomina_conciliados.columns and not st.session_state.nomina_conciliados.empty:
                n_exactos = int((st.session_state.nomina_conciliados['Tipo_Match'] == 'Exacto (fecha + monto)').sum())
                n_aprox = int((st.session_state.nomina_conciliados['Tipo_Match'] == 'Aproximado (dentro de tolerancia)').sum())
                st.caption(f":blue[:material/search:] Trazabilidad: {n_exactos} recibos por match exacto · {n_aprox} por match aproximado. Cada recibo se usa una sola vez.")
            buffer_n = io.BytesIO()
            with pd.ExcelWriter(buffer_n, engine='openpyxl') as writer:
                st.session_state.nomina_conciliados.to_excel(writer, sheet_name='Conciliados', index=False)
                st.session_state.nomina_pend_cfdi.to_excel(writer, sheet_name='Pendientes_Solo_CFDI', index=False)
                st.session_state.nomina_pend_aux.to_excel(writer, sheet_name='Pendientes_Solo_Auxiliar', index=False)
            st.download_button(label=":blue[:material/download:] Descargar Conciliación de Nómina (.XLSX)", data=buffer_n.getvalue(), file_name="Reporte_Nomina.xlsx", use_container_width=True)
            tn1, tn2, tn3 = st.tabs([":green[:material/check_circle:] Conciliados", ":orange[:material/warning:] Solo CFDI", ":blue[:material/menu_book:] Solo Auxiliar"])
            with tn1: st.dataframe(st.session_state.nomina_conciliados, use_container_width=True)
            with tn2: st.dataframe(st.session_state.nomina_pend_cfdi, use_container_width=True)
            with tn3: st.dataframe(st.session_state.nomina_pend_aux, use_container_width=True)

def render_inventarios():
    st.write("")
    st.markdown(f'<div class="section-header">{icono("box")} Inventarios Físicos vs Almacén ERP</div>', unsafe_allow_html=True)
    if not st.session_state.inventarios_cargados:
        ci_1, ci_2 = st.columns(2)
        with ci_1: inf = st.file_uploader("Conteo Físico Real", type=["csv", "xlsx"], key="inf")
        with ci_2: ke = st.file_uploader("Kárdex Teórico Contable", type=["csv", "xlsx"], key="ke")
        if inf and ke: st.session_state.df_inv_fisico = leer_archivo_contable(inf); st.session_state.df_kardex_er = leer_archivo_contable(ke); st.session_state.inventarios_cargados = True; st.rerun()
    else:
        st.success(":green[:material/flag:] Insumos de inventario indexados.")
        if st.button(":blue[:material/refresh:] Cargar nuevos archivos de inventario", key="reset_inv"): st.session_state.inventarios_cargados, st.session_state.inventarios_ejecutado = False, False; st.rerun()
    if st.session_state.inventarios_cargados:
        df_inf, df_ke = st.session_state.df_inv_fisico, st.session_state.df_kardex_er
        cli1, cli2, cli3 = st.columns(3)
        with cli1: id_prod = st.selectbox("SKU/Código:", df_inf.columns, key="id_p")
        with cli2: if_q = st.selectbox("Cant Física:", df_inf.columns, key="if_q")
        with cli3: ke_q = st.selectbox("Cant ERP:", df_ke.columns, key="ke_q")
        if st.button(":green[:material/play_arrow:] Auditar Almacenes", type="primary", use_container_width=True):
            try:
                df_inf_c = df_inf.copy()
                df_ke_c = df_ke.copy()
                df_inf_c['Q_Fisica'] = pd.to_numeric(df_inf_c[if_q], errors='coerce').fillna(0)
                df_ke_c['Q_ERP'] = pd.to_numeric(df_ke_c[ke_q], errors='coerce').fillna(0)
                if id_prod not in df_ke_c.columns:
                    raise KeyError(f"La columna SKU '{id_prod}' no existe en el Kárdex ERP; selecciona la columna equivalente.")
                # Agrupamos por SKU en ambos lados: si un mismo producto aparece en
                # más de una fila (ej. distintos lotes o ubicaciones de almacén),
                # un merge directo lo duplicaría igual que el bug de Saldos.
                df_inf_g = df_inf_c.groupby(id_prod, as_index=False)['Q_Fisica'].sum()
                df_ke_g = df_ke_c.groupby(id_prod, as_index=False)['Q_ERP'].sum()
                df_cruce = pd.merge(df_inf_g, df_ke_g, on=id_prod, how='outer').fillna(0)
                df_cruce['Diferencia_Unidades'] = (df_cruce['Q_Fisica'] - df_cruce['Q_ERP']).round(2)
                st.session_state.inventarios_conciliados = df_cruce[df_cruce['Diferencia_Unidades'].abs() <= st.session_state.tolerancia_inventario]
                st.session_state.inventarios_discrepancias = df_cruce[df_cruce['Diferencia_Unidades'].abs() > st.session_state.tolerancia_inventario]
                st.session_state.inventarios_ejecutado = True
                registrar_evento("Inventarios", f"Auditó almacenes ({len(st.session_state.inventarios_conciliados)} SKUs correctos, {len(st.session_state.inventarios_discrepancias)} discrepancias)")
                st.rerun()
            except Exception as e:
                st.error(f":orange[:material/warning:] No se pudo auditar el almacén. Detalle: {e}")
        if st.session_state.inventarios_ejecutado:
            st.caption(f":blue[:material/search:] Tolerancia aplicada: ± {st.session_state.tolerancia_inventario:g} unidades por SKU (ajustable en Configuración).")
            buffer_inv = io.BytesIO()
            with pd.ExcelWriter(buffer_inv, engine='openpyxl') as writer:
                st.session_state.inventarios_conciliados.to_excel(writer, sheet_name='SKUs_Correctos', index=False)
                st.session_state.inventarios_discrepancias.to_excel(writer, sheet_name='Discrepancias', index=False)
            st.download_button(label=":blue[:material/download:] Descargar Auditoría de Inventarios (.XLSX)", data=buffer_inv.getvalue(), file_name="Reporte_Inventarios.xlsx", use_container_width=True)
            ti1, ti2 = st.tabs([":green[:material/check_circle:] SKUs Correctos", ":orange[:material/warning:] Discrepancias Encontradas"])
            with ti1: st.dataframe(st.session_state.inventarios_conciliados, use_container_width=True)
            with ti2: st.dataframe(st.session_state.inventarios_discrepancias, use_container_width=True)

def render_iva():
    st.write("")
    st.markdown(f'<div class="section-header">{icono("cash")} IVA Efectivamente Cobrado / Pagado (Flujo de Efectivo)</div>', unsafe_allow_html=True)
    if not st.session_state.iva_cargados:
        civ_1, civ_2 = st.columns(2)
        with civ_1: iv_b = st.file_uploader("Flujo Bancos con IVA", type=["csv", "xlsx"], key="iv_b")
        with civ_2: iv_a = st.file_uploader("Determinación Mensual IVA", type=["csv", "xlsx"], key="iv_a")
        if iv_b and iv_a: st.session_state.df_iva_banco = leer_archivo_contable(iv_b); st.session_state.df_iva_aux = leer_archivo_contable(iv_a); st.session_state.iva_cargados = True; st.rerun()
    else:
        st.success(":green[:material/flag:] Insumos de IVA indexados.")
        if st.button(":blue[:material/refresh:] Cargar nuevos archivos de IVA", key="reset_iva"): st.session_state.iva_cargados, st.session_state.iva_ejecutado = False, False; st.rerun()
    if st.session_state.iva_cargados:
        df_ivb, df_iva = st.session_state.df_iva_banco, st.session_state.df_iva_aux
        civ1, civ2, civ3, civ4 = st.columns(4)
        with civ1: ib_m = st.selectbox("Importe Banco:", df_ivb.columns, key="ib_m")
        with civ2: ib_f = st.selectbox("Fecha Banco:", df_ivb.columns, key="ib_f")
        with civ3: ia_m = st.selectbox("Importe Papel IVA:", df_iva.columns, key="ia_m")
        with civ4: ia_f = st.selectbox("Fecha Papel IVA:", df_iva.columns, key="ia_f")
        if st.button(":green[:material/play_arrow:] Amarre IVA Flujo", type="primary", use_container_width=True):
            try:
                resultado = conciliar_dos_fuentes(
                    df_banco=df_ivb, df_auxiliar=df_iva,
                    col_monto_banco=ib_m, col_fecha_banco=ib_f,
                    col_monto_aux=ia_m, col_fecha_aux=ia_f,
                    tolerancia_monto=float(st.session_state.tolerancia),
                    tolerancia_dias=int(st.session_state.tolerancia_dias),
                )
                st.session_state.iva_conciliados = resultado["conciliados"]
                st.session_state.iva_pend_banco = resultado["pendientes_banco"]
                st.session_state.iva_pend_aux = resultado["pendientes_auxiliar"]
                st.session_state.iva_ejecutado = True
                registrar_evento("IVA Flujo", f"Amarró IVA ({len(resultado['conciliados'])} partidas conciliadas)")
                st.rerun()
            except Exception as e:
                st.error(f":orange[:material/warning:] No se pudo amarrar el IVA. Revisa las columnas de fecha/monto. Detalle: {e}")
        if st.session_state.iva_ejecutado:
            if 'Tipo_Match' in st.session_state.iva_conciliados.columns and not st.session_state.iva_conciliados.empty:
                n_exactos = int((st.session_state.iva_conciliados['Tipo_Match'] == 'Exacto (fecha + monto)').sum())
                n_aprox = int((st.session_state.iva_conciliados['Tipo_Match'] == 'Aproximado (dentro de tolerancia)').sum())
                st.caption(f":blue[:material/search:] Trazabilidad: {n_exactos} partidas por match exacto · {n_aprox} por match aproximado. Cada partida se usa una sola vez.")
            buffer_iva = io.BytesIO()
            with pd.ExcelWriter(buffer_iva, engine='openpyxl') as writer:
                st.session_state.iva_conciliados.to_excel(writer, sheet_name='Conciliados', index=False)
                st.session_state.iva_pend_banco.to_excel(writer, sheet_name='Pendientes_Solo_Banco', index=False)
                st.session_state.iva_pend_aux.to_excel(writer, sheet_name='Pendientes_Solo_Papel_IVA', index=False)
            st.download_button(label=":blue[:material/download:] Descargar Amarre de IVA (.XLSX)", data=buffer_iva.getvalue(), file_name="Reporte_IVA.xlsx", use_container_width=True)
            tiv1, tiv2, tiv3 = st.tabs([":green[:material/check_circle:] Conciliados", ":orange[:material/warning:] Solo Banco", ":blue[:material/menu_book:] Solo Papel IVA"])
            with tiv1: st.dataframe(st.session_state.iva_conciliados, use_container_width=True)
            with tiv2: st.dataframe(st.session_state.iva_pend_banco, use_container_width=True)
            with tiv3: st.dataframe(st.session_state.iva_pend_aux, use_container_width=True)

def render_activo_fijo():
    st.write("")
    st.markdown(f'<div class="section-header">{icono("factory")} Activo Fijo: Depreciación Esperada vs Registrada</div>', unsafe_allow_html=True)
    st.caption("A diferencia de los demás módulos, aquí se sube UN solo archivo (el kárdex de activos fijos ya trae el valor original y la depreciación acumulada contable en la misma fila).")
    if not st.session_state.af_cargados:
        af_file = st.file_uploader("Sube el Kárdex de Activos Fijos", type=["csv", "xlsx"], key="af_u")
        if af_file: st.session_state.df_af_kardex = leer_archivo_contable(af_file); st.session_state.af_cargados = True; st.rerun()
    else:
        st.success(":green[:material/flag:] Kárdex de activos fijos indexado.")
        if st.button(":blue[:material/refresh:] Cargar nuevo kárdex de activos", key="reset_af"): st.session_state.af_cargados, st.session_state.af_ejecutado = False, False; st.rerun()
    if st.session_state.af_cargados:
        df_af = st.session_state.df_af_kardex
        caf1, caf2, caf3, caf4 = st.columns(4)
        with caf1: af_id = st.selectbox("ID / Código de Activo:", df_af.columns, key="af_id")
        with caf2: af_valor = st.selectbox("Valor Original:", df_af.columns, key="af_valor")
        with caf3: af_fecha_adq = st.selectbox("Fecha de Adquisición:", df_af.columns, key="af_fecha_adq")
        with caf4: af_vida = st.selectbox("Vida Útil (meses):", df_af.columns, key="af_vida")
        af_dep_contable = st.selectbox("Depreciación Acumulada Contable (registrada en libros):", df_af.columns, key="af_dep_contable")
        fecha_corte_str = st.session_state.fecha_limite_cierre
        fecha_corte = datetime.date.fromisoformat(fecha_corte_str) if fecha_corte_str else datetime.date.today()
        st.caption(f":blue[:material/calendar_month:] Fecha de corte usada para el cálculo: {fecha_corte.strftime('%d/%m/%Y')} (toma la Fecha Límite de Cierre configurada; si no hay una, usa hoy).")
        if st.button(":green[:material/play_arrow:] Calcular Depreciación Esperada", type="primary", use_container_width=True):
            try:
                df_c = df_af.copy()
                df_c['Valor_Original_Num'] = pd.to_numeric(df_c[af_valor], errors='coerce').fillna(0)
                df_c['Vida_Util_Meses_Num'] = pd.to_numeric(df_c[af_vida], errors='coerce').replace(0, np.nan)
                df_c['Dep_Contable_Num'] = pd.to_numeric(df_c[af_dep_contable], errors='coerce').fillna(0)
                df_c['Fecha_Adquisicion_Limpia'] = pd.to_datetime(df_c[af_fecha_adq], format='mixed', dayfirst=True, errors='coerce')
                df_c = df_c.dropna(subset=['Fecha_Adquisicion_Limpia', 'Vida_Util_Meses_Num'])
                # Meses transcurridos entre adquisición y la fecha de corte (aprox. 30.44 días/mes)
                df_c['Meses_Transcurridos'] = ((pd.Timestamp(fecha_corte) - df_c['Fecha_Adquisicion_Limpia']).dt.days / 30.44).clip(lower=0)
                df_c['Depreciacion_Mensual'] = df_c['Valor_Original_Num'] / df_c['Vida_Util_Meses_Num']
                df_c['Depreciacion_Esperada'] = (df_c['Depreciacion_Mensual'] * df_c['Meses_Transcurridos']).clip(upper=df_c['Valor_Original_Num']).round(2)
                df_c['Diferencia_Depreciacion'] = (df_c['Dep_Contable_Num'] - df_c['Depreciacion_Esperada']).round(2)
                # Agrupamos por ID de activo antes de separar correctos/discrepancias,
                # por si el kárdex trae el mismo activo repetido en más de una fila.
                df_c = df_c.groupby(af_id, as_index=False).agg({
                    'Valor_Original_Num': 'sum', 'Dep_Contable_Num': 'sum',
                    'Depreciacion_Esperada': 'sum', 'Diferencia_Depreciacion': 'sum',
                    'Meses_Transcurridos': 'first',
                })
                st.session_state.af_conciliados = df_c[df_c['Diferencia_Depreciacion'].abs() <= st.session_state.tolerancia]
                st.session_state.af_discrepancias = df_c[df_c['Diferencia_Depreciacion'].abs() > st.session_state.tolerancia]
                st.session_state.af_ejecutado = True
                registrar_evento("Activo Fijo", f"Calculó depreciación esperada ({len(st.session_state.af_conciliados)} correctos, {len(st.session_state.af_discrepancias)} discrepancias)")
                st.rerun()
            except Exception as e:
                st.error(f":orange[:material/warning:] No se pudo calcular la depreciación. Revisa que las columnas de valor, fecha y vida útil sean correctas. Detalle: {e}")
        if st.session_state.af_ejecutado:
            buffer_af = io.BytesIO()
            with pd.ExcelWriter(buffer_af, engine='openpyxl') as writer:
                st.session_state.af_conciliados.to_excel(writer, sheet_name='Activos_Correctos', index=False)
                st.session_state.af_discrepancias.to_excel(writer, sheet_name='Discrepancias', index=False)
            st.download_button(label=":blue[:material/download:] Descargar Auditoría de Activo Fijo (.XLSX)", data=buffer_af.getvalue(), file_name="Reporte_Activo_Fijo.xlsx", use_container_width=True)
            taf1, taf2 = st.tabs([":green[:material/check_circle:] Activos Correctos", ":orange[:material/warning:] Discrepancias Encontradas"])
            with taf1: st.dataframe(st.session_state.af_conciliados, use_container_width=True)
            with taf2: st.dataframe(st.session_state.af_discrepancias, use_container_width=True)

def render_razones():
    st.write("")
    st.markdown(f'<div class="section-header">{icono("trending")} Análisis de Razones Financieras</div>', unsafe_allow_html=True)
    st.caption("Captura las cifras del periodo (de tu Balance General y Estado de Resultados) para calcular las razones financieras estándar. Se guardan automáticamente en esta sesión.")
    rf = st.session_state.rf_datos
    cr1, cr2 = st.columns(2)
    with cr1:
        st.markdown("**Balance General**")
        rf['activo_circulante'] = st.number_input("Activo Circulante:", min_value=0.0, value=float(rf.get('activo_circulante', 0.0)), step=1000.0, key="rf_ac")
        rf['inventarios_bg'] = st.number_input("Inventarios:", min_value=0.0, value=float(rf.get('inventarios_bg', 0.0)), step=1000.0, key="rf_inv")
        rf['activo_total'] = st.number_input("Activo Total:", min_value=0.0, value=float(rf.get('activo_total', 0.0)), step=1000.0, key="rf_at")
        rf['pasivo_circulante'] = st.number_input("Pasivo Circulante:", min_value=0.0, value=float(rf.get('pasivo_circulante', 0.0)), step=1000.0, key="rf_pc")
        rf['pasivo_total'] = st.number_input("Pasivo Total:", min_value=0.0, value=float(rf.get('pasivo_total', 0.0)), step=1000.0, key="rf_pt")
        rf['capital_contable'] = st.number_input("Capital Contable:", min_value=0.0, value=float(rf.get('capital_contable', 0.0)), step=1000.0, key="rf_cc")
    with cr2:
        st.markdown("**Estado de Resultados**")
        rf['ventas_netas'] = st.number_input("Ventas Netas:", min_value=0.0, value=float(rf.get('ventas_netas', 0.0)), step=1000.0, key="rf_vn")
        rf['costo_ventas'] = st.number_input("Costo de Ventas:", min_value=0.0, value=float(rf.get('costo_ventas', 0.0)), step=1000.0, key="rf_cv")
        rf['utilidad_operativa'] = st.number_input("Utilidad Operativa:", value=float(rf.get('utilidad_operativa', 0.0)), step=1000.0, key="rf_uo")
        rf['utilidad_neta'] = st.number_input("Utilidad Neta:", value=float(rf.get('utilidad_neta', 0.0)), step=1000.0, key="rf_un")
    st.session_state.rf_datos = rf

    def _div_seguro(a, b):
        return (a / b) if b else None

    razones = {
        "Razón Circulante": _div_seguro(rf['activo_circulante'], rf['pasivo_circulante']),
        "Prueba del Ácido": _div_seguro(rf['activo_circulante'] - rf['inventarios_bg'], rf['pasivo_circulante']),
        "Endeudamiento (Pasivo/Activo)": _div_seguro(rf['pasivo_total'], rf['activo_total']),
        "Apalancamiento (Pasivo/Capital)": _div_seguro(rf['pasivo_total'], rf['capital_contable']),
        "Margen Bruto": _div_seguro(rf['ventas_netas'] - rf['costo_ventas'], rf['ventas_netas']),
        "Margen Operativo": _div_seguro(rf['utilidad_operativa'], rf['ventas_netas']),
        "Margen Neto": _div_seguro(rf['utilidad_neta'], rf['ventas_netas']),
        "ROA (Utilidad/Activo)": _div_seguro(rf['utilidad_neta'], rf['activo_total']),
        "ROE (Utilidad/Capital)": _div_seguro(rf['utilidad_neta'], rf['capital_contable']),
    }

    if any(v is not None for v in razones.values()):
        st.markdown("---")
        st.markdown('<div class="section-header">Resultado</div>', unsafe_allow_html=True)
        cols_metric = st.columns(3)
        for i, (nombre, valor) in enumerate(razones.items()):
            with cols_metric[i % 3]:
                texto = f"{valor:.2%}" if "Margen" in nombre or "ROA" in nombre or "ROE" in nombre or "Endeudamiento" in nombre else (f"{valor:.2f}" if valor is not None else "N/D")
                st.metric(nombre, texto if valor is not None else "N/D")

        df_razones_graf = pd.DataFrame({"Razón": list(razones.keys()), "Valor": [v if v is not None else 0 for v in razones.values()]})
        fig_razones = px.bar(df_razones_graf, x="Valor", y="Razón", orientation="h", title="Razones Financieras del Periodo", color="Valor", color_continuous_scale="Tealgrn")
        fig_razones.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", font_color="#E6EDF3", showlegend=False, coloraxis_showscale=False, height=380)
        with st.container(key="chartcard_razones", border=True):
            st.plotly_chart(fig_razones, use_container_width=True)
    else:
        st.info(":orange[:material/lightbulb:] Captura al menos algunas cifras para ver las razones calculadas.")

def render_sat():
    st.write("")
    st.markdown(f'<div class="section-header">{icono("scale")} Checklist de Cumplimiento SAT</div>', unsafe_allow_html=True)
    st.caption("Esto es un rastreador de estatus de obligaciones (qué se presentó, cuándo, con qué acuse), NO un calculador de impuestos — los montos e ISR/IVA a pagar se calculan en tu sistema contable o con tu asesor fiscal; aquí solo llevas el control de cumplimiento.")
    if st.session_state.sat_checklist is None:
        st.session_state.sat_checklist = pd.DataFrame([
            {"Obligación": "ISR Provisional", "Periodo": "", "Fecha_Límite": None, "Estado": "Pendiente", "Folio/Acuse": "", "Notas": ""},
            {"Obligación": "IVA Mensual", "Periodo": "", "Fecha_Límite": None, "Estado": "Pendiente", "Folio/Acuse": "", "Notas": ""},
            {"Obligación": "DIOT", "Periodo": "", "Fecha_Límite": None, "Estado": "Pendiente", "Folio/Acuse": "", "Notas": ""},
            {"Obligación": "Nómina/CFDI Timbrado", "Periodo": "", "Fecha_Límite": None, "Estado": "Pendiente", "Folio/Acuse": "", "Notas": ""},
            {"Obligación": "Opinión de Cumplimiento (32-D)", "Periodo": "", "Fecha_Límite": None, "Estado": "Pendiente", "Folio/Acuse": "", "Notas": ""},
            {"Obligación": "Contabilidad Electrónica", "Periodo": "", "Fecha_Límite": None, "Estado": "Pendiente", "Folio/Acuse": "", "Notas": ""},
        ])
    df_sat_editado = st.data_editor(
        st.session_state.sat_checklist,
        num_rows="dynamic",
        use_container_width=True,
        column_config={
            "Estado": st.column_config.SelectboxColumn("Estado", options=["Pendiente", "Presentada", "Vencida", "No Aplica"]),
            "Fecha_Límite": st.column_config.DateColumn("Fecha Límite", format="DD/MM/YYYY"),
        },
        key="sat_editor",
    )
    if st.button(":blue[:material/save:] Guardar Checklist SAT", use_container_width=True, key="guardar_sat"):
        st.session_state.sat_checklist = df_sat_editado
        registrar_evento("Cumplimiento SAT", "Actualizó el checklist de obligaciones fiscales")
        st.success("Checklist guardado.")
    vencidas = df_sat_editado[(df_sat_editado["Estado"] == "Pendiente") & (pd.to_datetime(df_sat_editado["Fecha_Límite"], errors='coerce') < pd.Timestamp(datetime.date.today()))]
    if not vencidas.empty:
        st.error(f":orange[:material/warning:] {len(vencidas)} obligación(es) con fecha límite vencida y aún marcadas como 'Pendiente'.")

def render_aprobacion():
    st.write("")
    st.markdown(f'<div class="section-header">{icono("check")} Flujo de Revisión y Aprobación</div>', unsafe_allow_html=True)
    st.caption("Deja constancia de quién preparó, revisó y aprobó cada módulo. El rol de tu usuario autenticado determina qué acciones tienen sentido para ti (ver panel lateral).")
    estado_modulos_actual = calcular_estado_modulos()
    for modulo_info in estado_modulos_actual["modulos"]:
        nombre_mod = modulo_info["nombre"]
        estado_actual = st.session_state.estado_revision.get(nombre_mod, {"estado": "Preparado", "revisor": "", "fecha": "", "comentario": ""})
        with st.expander(f"{':green[:material/check_circle:]' if modulo_info['ejecutado'] else (':blue[:material/autorenew:]' if modulo_info['cargado'] else ':orange[:material/pending:]')} {nombre_mod}", expanded=False):
            ca1, ca2, ca3 = st.columns([1, 1, 2])
            with ca1:
                opciones_estado = ["Preparado", "Revisado", "Aprobado"]
                nuevo_estado = st.selectbox("Estado:", opciones_estado, index=opciones_estado.index(estado_actual["estado"]) if estado_actual["estado"] in opciones_estado else 0, key=f"estado_{nombre_mod}")
            with ca2:
                nuevo_revisor = st.text_input("Responsable:", value=estado_actual["revisor"], key=f"revisor_{nombre_mod}")
            with ca3:
                nuevo_comentario = st.text_input("Comentario:", value=estado_actual["comentario"], key=f"comentario_{nombre_mod}")
            if nuevo_estado == "Aprobado" and st.session_state.rol_actual == "Preparador":
                st.warning(":orange[:material/lightbulb:] Tu rol actual es 'Preparador'. Normalmente solo un Revisor o Socio/Aprobador marca un módulo como Aprobado — puedes cambiar tu rol en el panel lateral si corresponde.")
            if st.button(":blue[:material/save:] Guardar estado", key=f"guardar_estado_{nombre_mod}"):
                st.session_state.estado_revision[nombre_mod] = {
                    "estado": nuevo_estado, "revisor": nuevo_revisor, "comentario": nuevo_comentario,
                    "fecha": datetime.datetime.now().strftime("%Y-%m-%d %H:%M"),
                }
                registrar_evento(nombre_mod, f"Cambió el estado de revisión a '{nuevo_estado}' (responsable: {nuevo_revisor or 'sin especificar'})")
                st.rerun()
            if estado_actual["fecha"]:
                st.caption(f"Última actualización: {estado_actual['fecha']} — {estado_actual['estado']} por {estado_actual['revisor'] or 'sin especificar'}")

    st.markdown("---")
    resumen_aprobacion = pd.DataFrame([
        {"Módulo": m, "Estado": v.get("estado", "Preparado"), "Responsable": v.get("revisor", ""), "Última Actualización": v.get("fecha", "")}
        for m, v in st.session_state.estado_revision.items()
    ])
    if not resumen_aprobacion.empty:
        st.dataframe(resumen_aprobacion, use_container_width=True)

def render_pbc():
    st.write("")
    st.markdown(f'<div class="section-header">{icono("clipboard")} Checklist de Documentos Solicitados al Cliente (PBC)</div>', unsafe_allow_html=True)
    st.caption("Lleva control de qué se pidió, a quién, para cuándo, y si ya llegó. Agrega o quita renglones directamente en la tabla.")
    if st.session_state.pbc_checklist is None:
        st.session_state.pbc_checklist = pd.DataFrame([
            {"Documento": "Estados de cuenta bancarios", "Responsable": "", "Fecha_Límite": None, "Estado": "Solicitado", "Notas": ""},
            {"Documento": "Auxiliar contable completo", "Responsable": "", "Fecha_Límite": None, "Estado": "Solicitado", "Notas": ""},
            {"Documento": "XML de facturación (CFDI)", "Responsable": "", "Fecha_Límite": None, "Estado": "Solicitado", "Notas": ""},
            {"Documento": "Nómina timbrada del periodo", "Responsable": "", "Fecha_Límite": None, "Estado": "Solicitado", "Notas": ""},
        ])
    df_pbc_editado = st.data_editor(
        st.session_state.pbc_checklist,
        num_rows="dynamic",
        use_container_width=True,
        column_config={
            "Estado": st.column_config.SelectboxColumn("Estado", options=["Solicitado", "Recibido", "Pendiente", "No Aplica"]),
            "Fecha_Límite": st.column_config.DateColumn("Fecha Límite", format="DD/MM/YYYY"),
        },
        key="pbc_editor",
    )
    if st.button(":blue[:material/save:] Guardar Checklist PBC", use_container_width=True, key="guardar_pbc"):
        st.session_state.pbc_checklist = df_pbc_editado
        registrar_evento("Checklist PBC", "Actualizó el checklist de documentos solicitados")
        st.success("Checklist guardado.")
        st.rerun()
    total_docs = len(df_pbc_editado)
    recibidos = int((df_pbc_editado["Estado"] == "Recibido").sum())
    if total_docs > 0:
        st.progress(recibidos / total_docs, text=f"{recibidos} de {total_docs} documentos recibidos")

def render_bitacora():
    st.write("")
    st.markdown(f'<div class="section-header">{icono("book")} Bitácora de Auditoría</div>', unsafe_allow_html=True)
    st.caption("Registro cronológico de las acciones realizadas en esta sesión (usuario, rol, módulo y acción). Se guarda dentro del respaldo JSON, pero se pierde si cierras el navegador sin descargarlo.")
    if st.session_state.bitacora_eventos:
        df_bitacora = pd.DataFrame(st.session_state.bitacora_eventos).iloc[::-1].reset_index(drop=True)
        st.dataframe(df_bitacora, use_container_width=True)
        buffer_bit = io.BytesIO()
        with pd.ExcelWriter(buffer_bit, engine='openpyxl') as writer:
            df_bitacora.to_excel(writer, sheet_name='Bitacora', index=False)
        st.download_button(label=":blue[:material/download:] Descargar Bitácora (.XLSX)", data=buffer_bit.getvalue(), file_name="Bitacora_Auditoria.xlsx", use_container_width=True)
        if st.button(":red[:material/delete:] Vaciar Bitácora", key="vaciar_bitacora"):
            st.session_state.bitacora_eventos = []
            st.rerun()
    else:
        st.info(":orange[:material/lightbulb:] Aún no hay eventos registrados. Cada vez que ejecutes una conciliación o cambies un estado de aprobación, aparecerá aquí.")

def render_gestion_usuarios():
    st.write("")
    st.markdown(f'<div class="section-header">{icono("users")} Gestión de Usuarios</div>', unsafe_allow_html=True)

    # --- Disponible para CUALQUIER usuario autenticado, sin importar su rol ---
    st.markdown("#### :orange[:material/key:] Cambiar mi Contraseña")
    with st.form("form_cambiar_password", clear_on_submit=True):
        cp1, cp2, cp3 = st.columns(3)
        with cp1: pass_actual = st.text_input("Contraseña actual:", type="password", key="cp_actual")
        with cp2: pass_nueva = st.text_input("Nueva contraseña:", type="password", key="cp_nueva")
        with cp3: pass_nueva_confirmar = st.text_input("Confirmar nueva contraseña:", type="password", key="cp_confirmar")
        cambiar_pass = st.form_submit_button("Actualizar Contraseña", type="primary", use_container_width=True)
    if cambiar_pass:
        usuario_actual_info = st.session_state.usuarios_sistema.get(st.session_state.usuario_autenticado)
        if usuario_actual_info is None:
            st.error("No se encontró tu usuario en el sistema. Vuelve a iniciar sesión.")
        elif not _verificar_password(pass_actual, usuario_actual_info["salt"], usuario_actual_info["hash"]):
            st.error("La contraseña actual no es correcta.")
        elif len(pass_nueva) < 6:
            st.error("La nueva contraseña debe tener al menos 6 caracteres.")
        elif pass_nueva != pass_nueva_confirmar:
            st.error("La confirmación no coincide con la nueva contraseña.")
        elif pass_nueva == pass_actual:
            st.warning("La nueva contraseña debe ser distinta a la actual.")
        else:
            nuevo_salt, nuevo_hash = _hash_password(pass_nueva)
            usuario_actual_info["salt"] = nuevo_salt
            usuario_actual_info["hash"] = nuevo_hash
            registrar_evento("Gestión de Usuarios", "Cambió su propia contraseña")
            st.success(":green[:material/check_circle:] Contraseña actualizada correctamente. La usarás la próxima vez que inicies sesión.")

    st.markdown("---")

    if st.session_state.rol_actual != "Administrador":
        st.info(":orange[:material/lightbulb:] El resto de este módulo (agregar, bloquear o eliminar usuarios) está restringido a usuarios con rol **Administrador**. Si necesitas uno de esos cambios, pídeselo a tu Administrador.")
        return
    st.caption("Los usuarios viven en la memoria de este servidor mientras esté corriendo — no hay base de datos externa detrás. Si el servidor se reinicia, la lista vuelve a su estado inicial (solo el usuario admin).")

    st.markdown("#### :green[:material/add:] Agregar Usuario")
    with st.form("form_nuevo_usuario", clear_on_submit=True):
        cu1, cu2, cu3 = st.columns(3)
        with cu1: nuevo_usuario_nombre = st.text_input("Usuario (sin espacios):")
        with cu2: nuevo_usuario_pass = st.text_input("Contraseña:", type="password")
        with cu3: nuevo_usuario_rol = st.selectbox("Rol:", ["Preparador", "Revisor", "Socio/Aprobador", "Administrador"])
        crear = st.form_submit_button("Crear Usuario", type="primary", use_container_width=True)
    if crear:
        nombre_limpio = nuevo_usuario_nombre.strip()
        if not nombre_limpio or " " in nombre_limpio:
            st.error("El nombre de usuario no puede estar vacío ni contener espacios.")
        elif nombre_limpio in st.session_state.usuarios_sistema:
            st.error(f"El usuario '{nombre_limpio}' ya existe.")
        elif len(nuevo_usuario_pass) < 6:
            st.error("La contraseña debe tener al menos 6 caracteres.")
        else:
            salt, hash_val = _hash_password(nuevo_usuario_pass)
            st.session_state.usuarios_sistema[nombre_limpio] = {
                "salt": salt, "hash": hash_val, "rol": nuevo_usuario_rol, "bloqueado": False,
                "creado": datetime.datetime.now().strftime("%Y-%m-%d %H:%M"), "ultimo_acceso": None, "intentos_fallidos": 0,
            }
            registrar_evento("Gestión de Usuarios", f"Creó al usuario '{nombre_limpio}' con rol {nuevo_usuario_rol}")
            st.success(f"Usuario '{nombre_limpio}' creado.")
            st.rerun()

    st.markdown("---")
    st.markdown("#### :blue[:material/checklist:] Usuarios Registrados")
    admins_activos = [u for u, info in st.session_state.usuarios_sistema.items() if info["rol"] == "Administrador" and not info["bloqueado"]]
    for nombre_u, info_u in st.session_state.usuarios_sistema.items():
        with st.container():
            cu1, cu2, cu3, cu4, cu5 = st.columns([2, 1.5, 1.5, 1, 1])
            with cu1:
                etiqueta = f"**{nombre_u}**" + (" (tú)" if nombre_u == st.session_state.usuario_autenticado else "")
                st.markdown(etiqueta)
                st.caption(f"Creado: {info_u['creado']} · Último acceso: {info_u['ultimo_acceso'] or 'nunca'}")
            with cu2:
                st.markdown(info_u["rol"])
            with cu3:
                if info_u["bloqueado"]:
                    st.markdown(":red[:material/cancel:] Bloqueado")
                else:
                    st.markdown(":green[:material/check_circle:] Activo")
            with cu4:
                es_unico_admin = nombre_u in admins_activos and len(admins_activos) <= 1 and not info_u["bloqueado"]
                if st.button(":gray[:material/lock_open:]" if info_u["bloqueado"] else ":gray[:material/lock:]", key=f"toggle_bloqueo_{nombre_u}", help="Bloquear/Desbloquear", disabled=es_unico_admin):
                    st.session_state.usuarios_sistema[nombre_u]["bloqueado"] = not info_u["bloqueado"]
                    if not st.session_state.usuarios_sistema[nombre_u]["bloqueado"]:
                        st.session_state.usuarios_sistema[nombre_u]["intentos_fallidos"] = 0
                    registrar_evento("Gestión de Usuarios", f"{'Bloqueó' if st.session_state.usuarios_sistema[nombre_u]['bloqueado'] else 'Desbloqueó'} al usuario '{nombre_u}'")
                    st.rerun()
                if es_unico_admin:
                    st.caption("Único admin")
            with cu5:
                if st.button(":red[:material/delete:]", key=f"eliminar_usuario_{nombre_u}", help="Eliminar", disabled=(nombre_u == st.session_state.usuario_autenticado or es_unico_admin)):
                    del st.session_state.usuarios_sistema[nombre_u]
                    registrar_evento("Gestión de Usuarios", f"Eliminó al usuario '{nombre_u}'")
                    st.rerun()
            st.markdown("---")

def render_ayuda():
    st.write("")
    st.markdown(f'<div class="section-header">{icono("help")} Manual Operativo Diamond y Documentación de Herramientas</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="help-card"><div class="help-title">{icono("dashboard")} 1. Dashboard General</div>Diagnóstico financiero global con indicadores semafóricos de riesgo y entregable PDF.</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="help-card"><div class="help-title">{icono("bank")} 2. Módulo Bancario (Bancos vs Auxiliar)</div>Cruce bidimensional por fecha e importe para cuadrar estados de cuenta con Auxiliar.</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="help-card"><div class="help-title">{icono("document")} 3. XML vs Contabilidad</div>Mapeo inteligente para amarrar facturas electrónicas e identificar CFDI omitidos.</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="help-card"><div class="help-title">{icono("invoice")} 4. Clientes y Proveedores</div>Balanza de saldos globales contra reportes de antigüedad analíticos.</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="help-card"><div class="help-title">{icono("globe")} 5. Multidivisa USD</div>Algoritmo cambiario para calcular de forma exacta la ganancia o pérdida cambiaria.</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="help-card"><div class="help-title">{icono("badge")} 6. Nómina CFDI</div>Cruzamiento masivo para verificar recibos de nómina timbrados ante el SAT vs pólizas.</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="help-card"><div class="help-title">{icono("box")} 7. Inventarios</div>Levantamiento físico real de auditoría contra los saldos del Kárdex contable.</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="help-card"><div class="help-title">{icono("cash")} 8. IVA Flujo</div>Validar que el IVA determinado coincida con el flujo real reflejado en bancos.</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="help-card"><div class="help-title">{icono("gear")} 9. Configuración y Copias JSON</div>Gestión de membretes, tolerancias, fecha límite de cierre y carga/descarga de respaldos de sesión.</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="help-card"><div class="help-title">{icono("factory")} 10. Activo Fijo</div>Calcula la depreciación esperada en línea recta a partir del kárdex de activos y la compara contra la depreciación acumulada registrada en libros.</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="help-card"><div class="help-title">{icono("trending")} 11. Razones Financieras</div>Captura cifras del Balance General y Estado de Resultados para obtener liquidez, apalancamiento, márgenes, ROA y ROE con su gráfica.</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="help-card"><div class="help-title">{icono("scale")} 12. Cumplimiento SAT</div>Checklist de obligaciones fiscales (ISR, IVA, DIOT, Nómina, 32-D, Contabilidad Electrónica) con fechas límite y estatus — no calcula impuestos, solo da seguimiento a lo que ya se presentó.</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="help-card"><div class="help-title">{icono("check")} 13. Revisión y Aprobación</div>Marca cada módulo como Preparado, Revisado o Aprobado, con responsable, comentario y fecha — deja constancia de quién validó cada parte del trabajo.</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="help-card"><div class="help-title">{icono("clipboard")} 14. Checklist PBC</div>Lista editable de documentos solicitados al cliente, con responsable, fecha límite y estatus de recepción.</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="help-card"><div class="help-title">{icono("book")} 15. Bitácora de Auditoría</div>Registro cronológico de acciones (usuario, rol, módulo, acción y hora) de todo lo ejecutado en la sesión, exportable a Excel.</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="help-card"><div class="help-title">{icono("user")} Panel Lateral: Sesión, Multiempresa y Notificaciones</div>Muestra tu usuario y rol autenticados, permite cerrar sesión, guardar/alternar entre varias auditorías en la misma sesión, y revisa alertas de fechas límite, insumos faltantes o documentos PBC pendientes.</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="help-card"><div class="help-title">{icono("users")} 16. Gestión de Usuarios (solo Administrador)</div>Agrega, bloquea/desbloquea y elimina usuarios del sistema. Requiere haber iniciado sesión con un usuario con rol Administrador.</div>', unsafe_allow_html=True)

# ==============================================================================
# 5. NAVEGACIÓN FINAL: PESTAÑAS AGRUPADAS POR CATEGORÍA
# ==============================================================================
# Se construye hasta aquí (y no arriba) porque necesita que todas las
# funciones render_x() ya estén definidas. Agrupar por categoría, en vez de
# una sola barra plana de 17 pestañas, evita que la navegación se desborde
# visualmente y ayuda a que la app se sienta organizada por área de trabajo.
CATEGORIAS = {
    ":blue[:material/bar_chart:] Panel General": [(":blue[:material/bar_chart:] Dashboard", render_dashboard)],
    ":blue[:material/refresh:] Conciliaciones": [
        (":blue[:material/account_balance:] Bancos vs Auxiliar", render_bancos),
        (":gray[:material/description:] XML vs Contabilidad", render_xml),
        (":orange[:material/receipt_long:] Clientes y Proveedores", render_saldos),
        (":blue[:material/public:] Multidivisa USD", render_multidivisa),
        (":violet[:material/badge:] Nómina CFDI", render_nomina),
        (":orange[:material/inventory_2:] Inventarios", render_inventarios),
        (":green[:material/payments:] IVA Flujo", render_iva),
        (":orange[:material/factory:] Activo Fijo", render_activo_fijo),
    ],
    ":green[:material/trending_up:] Análisis y Cumplimiento": [
        (":green[:material/trending_up:] Razones Financieras", render_razones),
        (":violet[:material/balance:] Cumplimiento SAT", render_sat),
    ],
    ":violet[:material/shield:] Gobierno y Auditoría": [
        (":green[:material/check_circle:] Revisión y Aprobación", render_aprobacion),
        (":blue[:material/checklist:] Checklist PBC", render_pbc),
        (":orange[:material/history:] Bitácora", render_bitacora),
    ],
    ":gray[:material/settings:] Sistema": [
        (":gray[:material/settings:] Configuración", render_configuracion),
        (":violet[:material/group:] Gestión de Usuarios", render_gestion_usuarios),
        (":blue[:material/help:] Ayuda", render_ayuda),
    ],
}

st.markdown("---")
categoria_activa = st.radio(
    "Categoría:", list(CATEGORIAS.keys()), horizontal=True, label_visibility="collapsed", key="selector_categoria",
)
pestanas_categoria = CATEGORIAS[categoria_activa]
objetos_tabs = st.tabs([nombre for nombre, _ in pestanas_categoria])
for tab_obj, (_, funcion_render) in zip(objetos_tabs, pestanas_categoria):
    with tab_obj:
        funcion_render()
