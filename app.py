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
    page_icon="💎",
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
    </style>
""", unsafe_allow_html=True)

st.markdown('<div class="main-title">💎 TaxFlow-Diamond</div>', unsafe_allow_html=True)
st.markdown('<div class="subtitle">Enterprise Financial & XML Reconciliation Suite</div>', unsafe_allow_html=True)

# ==============================================================================
# 2. SISTEMA DE MEMORIA INTEGRAL DEL WORKFLOW (SESSION STATE)
# ==============================================================================
variables_sesion = {
    'df_banco': None, 'df_auxiliar': None, 'bancos_cargados': False, 'bancos_ejecutado': False,
    'df_conciliados': None, 'bancos_pendientes': None, 'auxiliar_pendientes': None,
    'suma_conciliado': 0.0, 'suma_banco_p': 0.0, 'suma_aux_p': 0.0,
    'df_xml_gastos': None, 'df_aux_gastos': None, 'xml_cargados': False, 'xml_ejecutado': False, 'xml_conciliados': None, 'xml_pend_xml': None, 'xml_pend_aux': None,
    'df_saldos_globales': None, 'df_facturas_detalle': None, 'saldos_cargados': False, 'saldos_ejecutado': False, 'saldos_conciliados': None, 'saldos_discrepancias': None,
    'df_divisa_ext': None, 'df_divisa_nac': None, 'divisa_cargados': False, 'divisa_ejecutado': False, 'divisa_conciliados': None, 'divisa_pend_ext': None, 'divisa_pend_nac': None, 'tc_auditoria_val': 17.50,
    'df_cfdi_nomina': None, 'df_aux_nomina': None, 'nomina_cargados': False, 'nomina_ejecutado': False, 'nomina_conciliados': None, 'nomina_discrepancias': None, 'nomina_pend_cfdi': None, 'nomina_pend_aux': None,
    'df_inv_fisico': None, 'df_kardex_er': None, 'inventarios_cargados': False, 'inventarios_ejecutado': False, 'inventarios_conciliados': None, 'inventarios_discrepancias': None,
    'df_iva_banco': None, 'df_iva_aux': None, 'iva_cargados': False, 'iva_ejecutado': False, 'iva_conciliados': None, 'iva_discrepancias': None, 'iva_pend_banco': None, 'iva_pend_aux': None,
    'fase_progreso': 1, 'empresa': "", 'periodo': "", 'auditor': "", 'tolerancia': 0.50, 'tolerancia_dias': 3, 'tolerancia_inventario': 1.0, 'divisa': "MXN ($)", 'logo_bytes': None, 'fecha_limite_cierre': None,

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
    st.warning("🔑 Usuario por defecto: **admin** — Contraseña: **TaxFlow2026!** — cámbiala en cuanto entres desde '👥 Gestión de Usuarios'.")
    with st.form("form_login"):
        st.markdown("### 🔒 Iniciar Sesión")
        usuario_input = st.text_input("Usuario:")
        password_input = st.text_input("Contraseña:", type="password")
        enviado = st.form_submit_button("Entrar", type="primary", use_container_width=True)
    if enviado:
        registro_usuario = st.session_state.usuarios_sistema.get(usuario_input)
        if registro_usuario is None:
            st.error("Usuario o contraseña incorrectos.")
        elif registro_usuario["bloqueado"] or registro_usuario["intentos_fallidos"] >= 5:
            registro_usuario["bloqueado"] = True
            st.error("🚫 Este usuario está bloqueado. Contacta a un Administrador.")
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
                st.error("🚫 Demasiados intentos fallidos: este usuario quedó bloqueado automáticamente. Contacta a un Administrador.")
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
else: st.sidebar.info("🏢 Sin Logotipo Institucional. Configúralo en la pestaña superior de Configuración.")

st.sidebar.markdown("---")
st.sidebar.markdown("### 👤 Sesión Activa")
st.sidebar.success(f"**{st.session_state.usuario_autenticado}** ({st.session_state.rol_actual})")
if st.sidebar.button("🔒 Cerrar Sesión", type="primary", use_container_width=True, key="sidebar_logout_btn"):
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
st.sidebar.caption("⚠️ Cerrar sesión también reinicia los datos de esta auditoría (bancos, XML, etc.) — descarga tu respaldo .JSON antes si quieres conservarlos.")

st.sidebar.markdown("---")
with st.sidebar.expander("🏢 Multiempresa (auditorías en esta sesión)"):
    st.caption("Guarda distintas auditorías en memoria para alternar entre clientes sin perder tu trabajo. Se pierden al cerrar el navegador o reiniciar el servidor — para conservarlas de forma permanente, descarga el respaldo .JSON de cada una desde Configuración.")
    nombre_nueva_auditoria = st.text_input("Nombre para guardar la auditoría actual:", key="nombre_snapshot")
    if st.button("💾 Guardar auditoría actual", use_container_width=True, key="guardar_snapshot_btn"):
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
            if st.button("📂 Cargar", use_container_width=True, key="cargar_snapshot_btn"):
                for llave, valor in _deserializar_estado(st.session_state.auditorias_guardadas[auditoria_elegida]).items():
                    st.session_state[llave] = valor
                registrar_evento("Multiempresa", f"Cargó la auditoría '{auditoria_elegida}'")
                st.rerun()
        with col_ae2:
            if st.button("🗑️ Eliminar", use_container_width=True, key="eliminar_snapshot_btn"):
                del st.session_state.auditorias_guardadas[auditoria_elegida]
                st.rerun()
    else:
        st.caption("Aún no hay auditorías guardadas.")

st.sidebar.markdown("---")
with st.sidebar.expander("🔔 Notificaciones", expanded=True):
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
        _notificaciones.append(("info", f"📂 {_modulos_sin_cargar} módulo(s) de conciliación aún sin insumos cargados."))
    if st.session_state.pbc_checklist is not None and not st.session_state.pbc_checklist.empty:
        _pendientes_pbc = int((st.session_state.pbc_checklist["Estado"] == "Pendiente").sum())
        if _pendientes_pbc > 0: _notificaciones.append(("warning", f"📋 {_pendientes_pbc} documento(s) del checklist PBC pendientes de recibir."))
    if not _notificaciones:
        st.caption("✅ Sin pendientes por ahora.")
    else:
        for _tipo, _texto in _notificaciones:
            getattr(st, _tipo)(_texto)

st.sidebar.markdown("---")
st.sidebar.markdown("### 📥 Descarga de Plantillas Corporativas")
buffer_p1 = io.BytesIO()
with pd.ExcelWriter(buffer_p1, engine='openpyxl') as w: pd.DataFrame(columns=["Fecha", "Concepto", "Referencia", "Importe", "RFC_Contraparte"]).to_excel(w, index=False)
st.sidebar.download_button("📊 Plantilla Estado de Cuenta", data=buffer_p1.getvalue(), file_name="Plantilla_Estado_Cuenta.xlsx", use_container_width=True)

buffer_p2 = io.BytesIO()
with pd.ExcelWriter(buffer_p2, engine='openpyxl') as w: pd.DataFrame(columns=["Fecha_Poliza", "Cuenta_Contable", "Concepto_Movimiento", "Monto_Registro", "RFC_Validar"]).to_excel(w, index=False)
st.sidebar.download_button("📖 Plantilla Auxiliar Contable", data=buffer_p2.getvalue(), file_name="Plantilla_Auxiliar_Contable.xlsx", use_container_width=True)

st.sidebar.markdown("---")
st.sidebar.markdown("### 🔍 Rastreador Rápido de Auditoría")
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
            <div class="bl-card-title">🗓️ Cierre de Periodo</div>
            <div class="bl-card-value" style="color:{dias_color};">{valor_dias}</div>
            <div class="bl-card-sub">{dias_label}</div>
        </div>""", unsafe_allow_html=True)
    with k2:
        st.markdown(f"""<div class="bl-card">
            <div class="bl-card-title">📋 Total</div>
            <div class="bl-card-value">{rc['total']:,}</div>
            <div class="bl-subrow"><span>Recs</span><b>{rc['total']:,}</b></div>
            <div class="bl-subrow"><span>Módulos</span><b>{tk['total']}</b></div>
        </div>""", unsafe_allow_html=True)
    with k3:
        st.markdown(f"""<div class="bl-card">
            <div class="bl-card-title">🟠 No preparado</div>
            <div class="bl-card-value">{_pct(rc['no_prep'], rc['total']):.0f}% <span class="bl-card-sub">{rc['no_prep']:,}</span></div>
            <div class="bl-subrow"><span>Recs</span><span><span class="bl-badge bl-badge-orange">{_pct(rc['no_prep'], rc['total']):.0f}%</span>{rc['no_prep']:,}</span></div>
            <div class="bl-subrow"><span>Módulos</span><span><span class="bl-badge bl-badge-orange">{_pct(tk['no_prep'], tk['total']):.0f}%</span>{tk['no_prep']}</span></div>
        </div>""", unsafe_allow_html=True)
    with k4:
        st.markdown(f"""<div class="bl-card">
            <div class="bl-card-title">🔵 En progreso</div>
            <div class="bl-card-value">{_pct(rc['progreso'], rc['total']):.0f}% <span class="bl-card-sub">{rc['progreso']:,}</span></div>
            <div class="bl-subrow"><span>Recs</span><span><span class="bl-badge bl-badge-blue">{_pct(rc['progreso'], rc['total']):.0f}%</span>{rc['progreso']:,}</span></div>
            <div class="bl-subrow"><span>Módulos</span><span><span class="bl-badge bl-badge-blue">{_pct(tk['progreso'], tk['total']):.0f}%</span>{tk['progreso']}</span></div>
        </div>""", unsafe_allow_html=True)
    with k5:
        st.markdown(f"""<div class="bl-card">
            <div class="bl-card-title">✅ Completado</div>
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
        fig_modulos.update_layout(paper_bgcolor="#0D1117", plot_bgcolor="#0D1117", font_color="#E6EDF3", legend_title_text="")
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
        fig_dona.update_layout(paper_bgcolor="#0D1117", plot_bgcolor="#0D1117", font_color="#E6EDF3")
        st.plotly_chart(fig_dona, use_container_width=True)

    # ---------- Debajo: semáforo de riesgo original + dictamen PDF ----------
    st.write("")
    fases = ["1. Configuración", "2. Carga Insumos", "3. Mapeo Columnas", "4. Reportes y Dictamen"]
    st.progress(st.session_state.fase_progreso / 4, text=f"Progreso del Flujo: **{fases[st.session_state.fase_progreso - 1]}**")
    if st.session_state.bancos_ejecutado:
        st.markdown('<div class="section-header">📊 Indicadores de Riesgo Corporativo</div>', unsafe_allow_html=True)
        total_pendientes = st.session_state.suma_banco_p + st.session_state.suma_aux_p
        porcentaje_riesgo = (total_pendientes / st.session_state.suma_conciliado * 100) if st.session_state.suma_conciliado > 0 else 0
        if porcentaje_riesgo <= 2.0: clase_semaforo, mensaje_semaforo = "kpi-green", "🟢 RIESGO BAJO: Libros Alineados."
        elif porcentaje_riesgo <= 5.0: clase_semaforo, mensaje_semaforo = "kpi-yellow", "🟡 RIESGO MODERADO: Monitorear partidas."
        else: clase_semaforo, mensaje_semaforo = "kpi-red", "🔴 ALERTA - RIESGO ALTO: Desfase crítico."
        st.markdown(f"<div class='kpi-card {clase_semaforo}'>{mensaje_semaforo} ({porcentaje_riesgo:.2f}% desfase)</div>", unsafe_allow_html=True)
        
        m1, m2, m3 = st.columns(3)
        m1.metric("Capital Conciliado", f"$ {st.session_state.suma_conciliado:,.2f}")
        m2.metric("Pendientes Banco", f"$ {st.session_state.suma_banco_p:,.2f}", delta_color="inverse")
        m3.metric("Pendientes Auxiliar", f"$ {st.session_state.suma_aux_p:,.2f}", delta_color="inverse")
        
        pdf_dictamen = generar_dictamen_pdf(st.session_state.empresa, st.session_state.periodo, st.session_state.auditor, st.session_state.suma_conciliado, st.session_state.suma_banco_p, st.session_state.suma_aux_p)
        st.download_button(label="📥 Descargar Dictamen Certificado (PDF)", data=pdf_dictamen, file_name="Dictamen_Auditoria.pdf", mime="application/pdf", use_container_width=True)
    else: st.info("💎 Suite Inicializada. Usa los módulos superiores para comenzar la auditoría.")

# ==============================================================================
# CONFIGURACIÓN COMPLETA RESTAURADA CON BOTONES DE RESPALDO JSON
# ==============================================================================
def render_configuracion():
    st.write("")
    st.markdown('<div class="section-header">⚙️ Panel de Parámetros Globales y Membretes</div>', unsafe_allow_html=True)
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

    # RESPALDO JSON COMPLETO — sin excepción de ningún módulo
    st.markdown("---")
    st.subheader("💾 Copias de Seguridad de la Auditoría (.JSON)")
    st.caption("El respaldo incluye TODOS los módulos sin excepción: los 8 de conciliación (Bancos, XML, Saldos, Multidivisa, Nómina, Inventarios, IVA, Activo Fijo), Razones Financieras, Checklist SAT, Checklist PBC, Revisión y Aprobación, Bitácora de Auditoría, Configuración, auditorías guardadas (Multiempresa) y la base de Usuarios del sistema (incluye contraseñas cifradas).")
    col_j1, col_j2 = st.columns(2)
    with col_j1:
        llaves_respaldo_completo = list(variables_sesion.keys()) + ["usuarios_sistema"]
        respaldo_dinamico = _serializar_estado({llave: st.session_state[llave] for llave in llaves_respaldo_completo})
        st.download_button(label="📥 Descargar Respaldo JSON Completo", data=json.dumps(respaldo_dinamico), file_name="Backup_TaxFlow.json", mime="application/json", use_container_width=True, on_click=lambda: registrar_evento("Configuración", "Descargó respaldo JSON completo (todos los módulos)"))

    with col_j2:
        archivo_json_cargado = st.file_uploader("Sube tu archivo de respaldo (.JSON)", type=["json"], key="json_config_uploader")
        restaurar_usuarios = st.checkbox("Restaurar también la base de Usuarios (usuarios, roles, contraseñas)", value=False, key="restaurar_usuarios_chk")
        if not restaurar_usuarios:
            st.caption("⚠️ Por seguridad, restaurar usuarios está desmarcado por defecto — así no se sobreescribe accidentalmente tu lista de usuarios actual (incluyendo tu propia contraseña) al cargar un respaldo de otra auditoría.")
        if archivo_json_cargado is not None:
            try:
                datos_restaurados = json.load(archivo_json_cargado)
                for llave, valor in _deserializar_estado(datos_restaurados).items():
                    if llave == "usuarios_sistema" and not restaurar_usuarios:
                        continue
                    st.session_state[llave] = valor
                registrar_evento("Configuración", f"Restauró la sesión desde un respaldo JSON (usuarios {'incluidos' if restaurar_usuarios else 'excluidos'})")
                st.success("✓ Ecosistema restaurado desde el JSON con éxito.")
                st.rerun()
            except Exception as e: st.error(f"Error JSON: {e}")
def render_bancos():
    st.write("")
    st.markdown('<div class="section-header">🏦 Módulo Bancario: Estado de Cuenta vs Auxiliar Contable Interno</div>', unsafe_allow_html=True)
    if not st.session_state.bancos_cargados:
        c_b1, c_b2 = st.columns(2)
        with c_b1: b_file = st.file_uploader("Sube Estado de Cuenta Bancario", type=["csv", "xlsx"], key="b_u")
        with c_b2: a_file = st.file_uploader("Sube Auxiliar Contable", type=["csv", "xlsx"], key="a_u")
        if b_file and a_file: st.session_state.df_banco = leer_archivo_contable(b_file); st.session_state.df_auxiliar = leer_archivo_contable(a_file); st.session_state.bancos_cargados = True; st.session_state.fase_progreso = 3; st.rerun()
    else:
        st.success("🏁 Insumos bancarios indexados.")
        if st.button("🔄 Cargar nuevos archivos de banco", key="reset_b"): st.session_state.bancos_cargados, st.session_state.bancos_ejecutado = False, False; st.session_state.fase_progreso = 1; st.rerun()
    if st.session_state.bancos_cargados:
        df_b, df_a = st.session_state.df_banco, st.session_state.df_auxiliar
        c1, c2, c3, c4 = st.columns(4)
        with c1: cb_m = st.selectbox("Monto BANCO:", df_b.columns, key="cb_m")
        with c2: cb_f = st.selectbox("Fecha BANCO:", df_b.columns, key="cb_f")
        with c3: ca_m = st.selectbox("Monto AUXILIAR:", df_a.columns, key="ca_m")
        with c4: ca_f = st.selectbox("Fecha AUXILIAR:", df_a.columns, key="ca_f")
        
        st.markdown("---")
        st.subheader("🛡️ Panel de Pre-Validación de Insumos")
        col_v1, col_v2 = st.columns(2)
        with col_v1:
            col_rfc_b = st.selectbox("Columna de RFC en archivo BANCO (Opcional):", ["Ninguna"] + list(df_b.columns))
            if col_rfc_b != "Ninguna" and not df_b[~df_b[col_rfc_b].apply(validar_rfc)].empty: st.warning("⚠️ RFCs inválidos en Banco.")
        with col_v2:
            col_rfc_a = st.selectbox("Columna de RFC en archivo AUXILIAR (Opcional):", ["Ninguna"] + list(df_a.columns))
            if col_rfc_a != "Ninguna" and not df_a[~df_a[col_rfc_a].apply(validar_rfc)].empty: st.warning("⚠️ RFCs inválidos en Auxiliar.")

        if st.button("🚀 Ejecutar Algoritmo de Conciliación Diamond", type="primary", use_container_width=True):
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
                st.session_state.suma_conciliado = resultado["resumen"]["suma_conciliado"]
                st.session_state.suma_banco_p = resultado["resumen"]["suma_banco_pendiente"]
                st.session_state.suma_aux_p = resultado["resumen"]["suma_aux_pendiente"]
                st.session_state.bancos_ejecutado = True
                st.session_state.fase_progreso = 4
                registrar_evento("Bancos vs Auxiliar", f"Ejecutó la conciliación ({resultado['resumen']['num_exactos']} exactos, {resultado['resumen']['num_aproximados']} aproximados, {resultado['resumen']['num_pendientes_banco']+resultado['resumen']['num_pendientes_auxiliar']} pendientes)")
                st.rerun()
            except Exception as e:
                st.error(f"⚠️ No se pudo ejecutar la conciliación. Revisa que las columnas de fecha y monto sean correctas. Detalle: {e}")
        if st.session_state.bancos_ejecutado:
            if 'Tipo_Match' in st.session_state.df_conciliados.columns and not st.session_state.df_conciliados.empty:
                n_exactos = int((st.session_state.df_conciliados['Tipo_Match'] == 'Exacto (fecha + monto)').sum())
                n_aprox = int((st.session_state.df_conciliados['Tipo_Match'] == 'Aproximado (dentro de tolerancia)').sum())
                st.caption(f"🔎 Trazabilidad: {n_exactos} partidas por match exacto (misma fecha y monto) · {n_aprox} por match aproximado (dentro de tolerancia). Cada partida se usa una sola vez, nunca se repite en ambos lados.")
            buffer = io.BytesIO()
            with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
                st.session_state.df_conciliados.to_excel(writer, sheet_name='Partidas_Conciliadas', index=False)
                st.session_state.bancos_pendientes.to_excel(writer, sheet_name='Pendientes_Solo_Banco', index=False)
                st.session_state.auxiliar_pendientes.to_excel(writer, sheet_name='Pendientes_Solo_Auxiliar', index=False)
            st.download_button(label="📥 Descargar Libro de Conciliación Completo (.XLSX)", data=buffer.getvalue(), file_name="Reporte_Bancos.xlsx", use_container_width=True)
            tab1, tab2, tab3 = st.tabs(["✅ Conciliados", "⚠️ Solo Banco", "📖 Solo Auxiliar"])
            with tab1: st.dataframe(st.session_state.df_conciliados, use_container_width=True)
            with tab2: st.dataframe(st.session_state.bancos_pendientes, use_container_width=True)
            with tab3: st.dataframe(st.session_state.auxiliar_pendientes, use_container_width=True)

def render_xml():
    st.write("")
    st.markdown('<div class="section-header">📄 Auditoría Fiscal: Comprobantes XML vs Auxiliar de Contabilidad</div>', unsafe_allow_html=True)
    if not st.session_state.xml_cargados:
        cx_1, cx_2 = st.columns(2)
        with cx_1: x_file = st.file_uploader("Sube Reporte de Facturas", type=["csv", "xlsx"], key="x_u")
        with cx_2: cg_file = st.file_uploader("Sube Auxiliar de Gastos", type=["csv", "xlsx"], key="cg_u")
        if x_file and cg_file: st.session_state.df_xml_gastos = leer_archivo_contable(x_file); st.session_state.df_aux_gastos = leer_archivo_contable(cg_file); st.session_state.xml_cargados = True; st.rerun()
    else:
        st.success("🏁 Insumos de facturación indexados.")
        if st.button("🔄 Cargar nuevos archivos de XML", key="reset_xml"): st.session_state.xml_cargados, st.session_state.xml_ejecutado = False, False; st.rerun()
    if st.session_state.xml_cargados:
        df_xml, df_cg = st.session_state.df_xml_gastos, st.session_state.df_aux_gastos
        cx1, cx2, cx3, cx4 = st.columns(4)
        with cx1: xml_m = st.selectbox("Monto XML:", df_xml.columns, key="xml_m")
        with cx2: xml_f = st.selectbox("Fecha XML:", df_xml.columns, key="xml_f")
        with cx3: cont_m = st.selectbox("Monto Auxiliar Gasto:", df_cg.columns, key="cont_m")
        with cx4: cont_f = st.selectbox("Fecha Auxiliar Gasto:", df_cg.columns, key="cont_f")
        if st.button("🚀 Cruce XML vs Contabilidad", type="primary", use_container_width=True):
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
                st.error(f"⚠️ No se pudo cruzar XML vs Contabilidad. Revisa las columnas de fecha/monto. Detalle: {e}")
        if st.session_state.xml_ejecutado:
            if 'Tipo_Match' in st.session_state.xml_conciliados.columns and not st.session_state.xml_conciliados.empty:
                n_exactos = int((st.session_state.xml_conciliados['Tipo_Match'] == 'Exacto (fecha + monto)').sum())
                n_aprox = int((st.session_state.xml_conciliados['Tipo_Match'] == 'Aproximado (dentro de tolerancia)').sum())
                st.caption(f"🔎 Trazabilidad: {n_exactos} facturas por match exacto · {n_aprox} por match aproximado. Cada factura se usa una sola vez.")
            buffer_xml = io.BytesIO()
            with pd.ExcelWriter(buffer_xml, engine='openpyxl') as writer:
                st.session_state.xml_conciliados.to_excel(writer, sheet_name='Conciliados', index=False)
                st.session_state.xml_pend_xml.to_excel(writer, sheet_name='Pendientes_Solo_XML', index=False)
                st.session_state.xml_pend_aux.to_excel(writer, sheet_name='Pendientes_Solo_Auxiliar', index=False)
            st.download_button(label="📥 Descargar Cruce XML vs Contabilidad (.XLSX)", data=buffer_xml.getvalue(), file_name="Reporte_XML.xlsx", use_container_width=True)
            tx1, tx2, tx3 = st.tabs(["✅ Conciliados", "⚠️ Solo XML (posible omisión contable)", "📖 Solo Auxiliar (posible CFDI faltante)"])
            with tx1: st.dataframe(st.session_state.xml_conciliados, use_container_width=True)
            with tx2: st.dataframe(st.session_state.xml_pend_xml, use_container_width=True)
            with tx3: st.dataframe(st.session_state.xml_pend_aux, use_container_width=True)

def render_saldos():
    st.write("")
    st.markdown('<div class="section-header">🧾 Herramienta de Auditoría de Cartera: Clientes y Proveedores</div>', unsafe_allow_html=True)
    if not st.session_state.saldos_cargados:
        cs_1, cs_2 = st.columns(2)
        with cs_1: sg_file = st.file_uploader("Sube Reporte de Saldos Globales (ERP)", type=["csv", "xlsx"], key="sg_u_new")
        with cs_2: fd_file = st.file_uploader("Sube Desglose de Facturas / Antigüedad", type=["csv", "xlsx"], key="fd_u_new")
        if sg_file and fd_file: st.session_state.df_saldos_globales = leer_archivo_contable(sg_file); st.session_state.df_facturas_detalle = leer_archivo_contable(fd_file); st.session_state.saldos_cargados = True; st.rerun()
    if st.session_state.saldos_cargados:
        df_sg, df_fd = st.session_state.df_saldos_globales, st.session_state.df_facturas_detalle
        col_s1, col_s2, col_s3 = st.columns(3); id_cte = st.selectbox("Columna Identificador (Código/RFC):", df_sg.columns, key="id_cte_new"); sg_m = st.selectbox("Monto Saldo Global Contable:", df_sg.columns, key="sg_m_new"); fd_m = st.selectbox("Monto Factura en Desglose:", df_fd.columns, key="fd_m_new")
        if st.button("🚀 Ejecutar Cruce de Antigüedad de Saldos", type="primary", use_container_width=True):
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
            t_s1, t_s2 = st.tabs(["✅ Saldos Correctos", "⚠️ Discrepancias Encontradas"])
            with t_s1: st.dataframe(st.session_state.saldos_conciliados, use_container_width=True)
            with t_s2: st.dataframe(st.session_state.saldos_discrepancias, use_container_width=True)
def render_multidivisa():
    st.write("")
    st.markdown('<div class="section-header">🌐 Herramienta Cambiaria: Conciliación de Cuentas en Dólares (USD)</div>', unsafe_allow_html=True)
    st.session_state.tc_auditoria_val = st.number_input("Tipo de Cambio (TC) de Cierre Mensual:", min_value=1.0000, value=float(st.session_state.tc_auditoria_val), step=0.0100, key="tc_num_input")
    if not st.session_state.divisa_cargados:
        cv_1, cv_2 = st.columns(2)
        with cv_1: de_file = st.file_uploader("Sube Estado de Cuenta Extranjero (USD)", type=["csv", "xlsx"], key="de_u_new")
        with cv_2: dn_file = st.file_uploader("Sube Registro en Moneda Nacional (Pólizas)", type=["csv", "xlsx"], key="dn_u_new")
        if de_file and dn_file: st.session_state.df_divisa_ext = leer_archivo_contable(de_file); st.session_state.df_divisa_nac = leer_archivo_contable(dn_file); st.session_state.divisa_cargados = True; st.rerun()
    else:
        st.success("🏁 Papeles de divisas extranjeras indexados.")
        if st.button("🔄 Reestablecer Módulo Multidivisa", key="reset_v_new"): st.session_state.divisa_cargados, st.session_state.divisa_ejecutado = False, False; st.rerun()
    if st.session_state.divisa_cargados:
        df_ext, df_nac = st.session_state.df_divisa_ext, st.session_state.df_divisa_nac
        col_v1, col_v2, col_v3, col_v4 = st.columns(4)
        with col_v1: de_m = st.selectbox("Monto en Dólares (USD):", df_ext.columns, key="de_m_new")
        with col_v2: de_f = st.selectbox("Fecha (USD):", df_ext.columns, key="de_f_new")
        with col_v3: dn_m = st.selectbox("Monto en Moneda Nacional (MXN):", df_nac.columns, key="dn_m_new")
        with col_v4: dn_f = st.selectbox("Fecha (MXN):", df_nac.columns, key="dn_f_new")
        st.caption("ℹ️ El monto en USD se convierte primero a MXN con el tipo de cambio de arriba, y ESE valor convertido es el que se concilia contra tu registro en pesos (antes se comparaban los números crudos de ambas monedas, lo cual no tiene sentido matemático).")
        if st.button("🚀 Calcular Fluctuación Cambiaria Analítica", type="primary", use_container_width=True):
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
                st.error(f"⚠️ No se pudo calcular la fluctuación cambiaria. Revisa las columnas de fecha/monto. Detalle: {e}")
        if st.session_state.divisa_ejecutado:
            tolerancia_cambiaria_mostrar = max(float(st.session_state.tolerancia), float(st.session_state.tc_auditoria_val) * 0.02)
            if 'Tipo_Match' in st.session_state.divisa_conciliados.columns and not st.session_state.divisa_conciliados.empty:
                n_exactos = int((st.session_state.divisa_conciliados['Tipo_Match'] == 'Exacto (fecha + monto)').sum())
                n_aprox = int((st.session_state.divisa_conciliados['Tipo_Match'] == 'Aproximado (dentro de tolerancia)').sum())
                st.caption(f"🔎 Trazabilidad: {n_exactos} operaciones por match exacto · {n_aprox} por match aproximado (tolerancia cambiaria ± {tolerancia_cambiaria_mostrar:.2f} MXN).")
            buffer_div = io.BytesIO()
            with pd.ExcelWriter(buffer_div, engine='openpyxl') as writer:
                st.session_state.divisa_conciliados.to_excel(writer, sheet_name='Conciliados', index=False)
                st.session_state.divisa_pend_ext.to_excel(writer, sheet_name='Pendientes_Solo_USD', index=False)
                st.session_state.divisa_pend_nac.to_excel(writer, sheet_name='Pendientes_Solo_MXN', index=False)
            st.download_button(label="📥 Descargar Conciliación Cambiaria (.XLSX)", data=buffer_div.getvalue(), file_name="Reporte_Multidivisa.xlsx", use_container_width=True)
            td1, td2, td3 = st.tabs(["✅ Conciliados", "⚠️ Solo USD", "📖 Solo MXN"])
            with td1: st.dataframe(st.session_state.divisa_conciliados, use_container_width=True)
            with td2: st.dataframe(st.session_state.divisa_pend_ext, use_container_width=True)
            with td3: st.dataframe(st.session_state.divisa_pend_nac, use_container_width=True)

def render_nomina():
    st.write("")
    st.markdown('<div class="section-header">👔 Auditoría de Nómina: CFDI Timbrados vs Auxiliar</div>', unsafe_allow_html=True)
    if not st.session_state.nomina_cargados:
        cn_1, cn_2 = st.columns(2)
        with cn_1: n_xml = st.file_uploader("Sube XML Nómina", type=["csv", "xlsx"], key="nx")
        with cn_2: n_aux = st.file_uploader("Sube Auxiliar Sueldos", type=["csv", "xlsx"], key="na")
        if n_xml and n_aux: st.session_state.df_cfdi_nomina = leer_archivo_contable(n_xml); st.session_state.df_aux_nomina = leer_archivo_contable(n_aux); st.session_state.nomina_cargados = True; st.rerun()
    else:
        st.success("🏁 Insumos de nómina indexados.")
        if st.button("🔄 Cargar nuevos archivos de nómina", key="reset_n"): st.session_state.nomina_cargados, st.session_state.nomina_ejecutado = False, False; st.rerun()
    if st.session_state.nomina_cargados:
        df_nx, df_na = st.session_state.df_cfdi_nomina, st.session_state.df_aux_nomina
        cn1, cn2, cn3, cn4 = st.columns(4)
        with cn1: nx_m = st.selectbox("Monto CFDI:", df_nx.columns, key="nx_m")
        with cn2: nx_f = st.selectbox("Fecha CFDI:", df_nx.columns, key="nx_f")
        with cn3: na_m = st.selectbox("Monto Libros:", df_na.columns, key="na_m")
        with cn4: na_f = st.selectbox("Fecha Libros:", df_na.columns, key="na_f")
        if st.button("🚀 Conciliar Nóminas", type="primary", use_container_width=True):
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
                st.error(f"⚠️ No se pudo conciliar la nómina. Revisa las columnas de fecha/monto. Detalle: {e}")
        if st.session_state.nomina_ejecutado:
            if 'Tipo_Match' in st.session_state.nomina_conciliados.columns and not st.session_state.nomina_conciliados.empty:
                n_exactos = int((st.session_state.nomina_conciliados['Tipo_Match'] == 'Exacto (fecha + monto)').sum())
                n_aprox = int((st.session_state.nomina_conciliados['Tipo_Match'] == 'Aproximado (dentro de tolerancia)').sum())
                st.caption(f"🔎 Trazabilidad: {n_exactos} recibos por match exacto · {n_aprox} por match aproximado. Cada recibo se usa una sola vez.")
            buffer_n = io.BytesIO()
            with pd.ExcelWriter(buffer_n, engine='openpyxl') as writer:
                st.session_state.nomina_conciliados.to_excel(writer, sheet_name='Conciliados', index=False)
                st.session_state.nomina_pend_cfdi.to_excel(writer, sheet_name='Pendientes_Solo_CFDI', index=False)
                st.session_state.nomina_pend_aux.to_excel(writer, sheet_name='Pendientes_Solo_Auxiliar', index=False)
            st.download_button(label="📥 Descargar Conciliación de Nómina (.XLSX)", data=buffer_n.getvalue(), file_name="Reporte_Nomina.xlsx", use_container_width=True)
            tn1, tn2, tn3 = st.tabs(["✅ Conciliados", "⚠️ Solo CFDI", "📖 Solo Auxiliar"])
            with tn1: st.dataframe(st.session_state.nomina_conciliados, use_container_width=True)
            with tn2: st.dataframe(st.session_state.nomina_pend_cfdi, use_container_width=True)
            with tn3: st.dataframe(st.session_state.nomina_pend_aux, use_container_width=True)

def render_inventarios():
    st.write("")
    st.markdown('<div class="section-header">📦 Inventarios Físicos vs Almacén ERP</div>', unsafe_allow_html=True)
    if not st.session_state.inventarios_cargados:
        ci_1, ci_2 = st.columns(2)
        with ci_1: inf = st.file_uploader("Conteo Físico Real", type=["csv", "xlsx"], key="inf")
        with ci_2: ke = st.file_uploader("Kárdex Teórico Contable", type=["csv", "xlsx"], key="ke")
        if inf and ke: st.session_state.df_inv_fisico = leer_archivo_contable(inf); st.session_state.df_kardex_er = leer_archivo_contable(ke); st.session_state.inventarios_cargados = True; st.rerun()
    else:
        st.success("🏁 Insumos de inventario indexados.")
        if st.button("🔄 Cargar nuevos archivos de inventario", key="reset_inv"): st.session_state.inventarios_cargados, st.session_state.inventarios_ejecutado = False, False; st.rerun()
    if st.session_state.inventarios_cargados:
        df_inf, df_ke = st.session_state.df_inv_fisico, st.session_state.df_kardex_er
        cli1, cli2, cli3 = st.columns(3)
        with cli1: id_prod = st.selectbox("SKU/Código:", df_inf.columns, key="id_p")
        with cli2: if_q = st.selectbox("Cant Física:", df_inf.columns, key="if_q")
        with cli3: ke_q = st.selectbox("Cant ERP:", df_ke.columns, key="ke_q")
        if st.button("🚀 Auditar Almacenes", type="primary", use_container_width=True):
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
                st.error(f"⚠️ No se pudo auditar el almacén. Detalle: {e}")
        if st.session_state.inventarios_ejecutado:
            st.caption(f"🔎 Tolerancia aplicada: ± {st.session_state.tolerancia_inventario:g} unidades por SKU (ajustable en Configuración).")
            buffer_inv = io.BytesIO()
            with pd.ExcelWriter(buffer_inv, engine='openpyxl') as writer:
                st.session_state.inventarios_conciliados.to_excel(writer, sheet_name='SKUs_Correctos', index=False)
                st.session_state.inventarios_discrepancias.to_excel(writer, sheet_name='Discrepancias', index=False)
            st.download_button(label="📥 Descargar Auditoría de Inventarios (.XLSX)", data=buffer_inv.getvalue(), file_name="Reporte_Inventarios.xlsx", use_container_width=True)
            ti1, ti2 = st.tabs(["✅ SKUs Correctos", "⚠️ Discrepancias Encontradas"])
            with ti1: st.dataframe(st.session_state.inventarios_conciliados, use_container_width=True)
            with ti2: st.dataframe(st.session_state.inventarios_discrepancias, use_container_width=True)

def render_iva():
    st.write("")
    st.markdown('<div class="section-header">💸 IVA Efectivamente Cobrado / Pagado (Flujo de Efectivo)</div>', unsafe_allow_html=True)
    if not st.session_state.iva_cargados:
        civ_1, civ_2 = st.columns(2)
        with civ_1: iv_b = st.file_uploader("Flujo Bancos con IVA", type=["csv", "xlsx"], key="iv_b")
        with civ_2: iv_a = st.file_uploader("Determinación Mensual IVA", type=["csv", "xlsx"], key="iv_a")
        if iv_b and iv_a: st.session_state.df_iva_banco = leer_archivo_contable(iv_b); st.session_state.df_iva_aux = leer_archivo_contable(iv_a); st.session_state.iva_cargados = True; st.rerun()
    else:
        st.success("🏁 Insumos de IVA indexados.")
        if st.button("🔄 Cargar nuevos archivos de IVA", key="reset_iva"): st.session_state.iva_cargados, st.session_state.iva_ejecutado = False, False; st.rerun()
    if st.session_state.iva_cargados:
        df_ivb, df_iva = st.session_state.df_iva_banco, st.session_state.df_iva_aux
        civ1, civ2, civ3, civ4 = st.columns(4)
        with civ1: ib_m = st.selectbox("Importe Banco:", df_ivb.columns, key="ib_m")
        with civ2: ib_f = st.selectbox("Fecha Banco:", df_ivb.columns, key="ib_f")
        with civ3: ia_m = st.selectbox("Importe Papel IVA:", df_iva.columns, key="ia_m")
        with civ4: ia_f = st.selectbox("Fecha Papel IVA:", df_iva.columns, key="ia_f")
        if st.button("🚀 Amarre IVA Flujo", type="primary", use_container_width=True):
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
                st.error(f"⚠️ No se pudo amarrar el IVA. Revisa las columnas de fecha/monto. Detalle: {e}")
        if st.session_state.iva_ejecutado:
            if 'Tipo_Match' in st.session_state.iva_conciliados.columns and not st.session_state.iva_conciliados.empty:
                n_exactos = int((st.session_state.iva_conciliados['Tipo_Match'] == 'Exacto (fecha + monto)').sum())
                n_aprox = int((st.session_state.iva_conciliados['Tipo_Match'] == 'Aproximado (dentro de tolerancia)').sum())
                st.caption(f"🔎 Trazabilidad: {n_exactos} partidas por match exacto · {n_aprox} por match aproximado. Cada partida se usa una sola vez.")
            buffer_iva = io.BytesIO()
            with pd.ExcelWriter(buffer_iva, engine='openpyxl') as writer:
                st.session_state.iva_conciliados.to_excel(writer, sheet_name='Conciliados', index=False)
                st.session_state.iva_pend_banco.to_excel(writer, sheet_name='Pendientes_Solo_Banco', index=False)
                st.session_state.iva_pend_aux.to_excel(writer, sheet_name='Pendientes_Solo_Papel_IVA', index=False)
            st.download_button(label="📥 Descargar Amarre de IVA (.XLSX)", data=buffer_iva.getvalue(), file_name="Reporte_IVA.xlsx", use_container_width=True)
            tiv1, tiv2, tiv3 = st.tabs(["✅ Conciliados", "⚠️ Solo Banco", "📖 Solo Papel IVA"])
            with tiv1: st.dataframe(st.session_state.iva_conciliados, use_container_width=True)
            with tiv2: st.dataframe(st.session_state.iva_pend_banco, use_container_width=True)
            with tiv3: st.dataframe(st.session_state.iva_pend_aux, use_container_width=True)

def render_activo_fijo():
    st.write("")
    st.markdown('<div class="section-header">🏭 Activo Fijo: Depreciación Esperada vs Registrada</div>', unsafe_allow_html=True)
    st.caption("A diferencia de los demás módulos, aquí se sube UN solo archivo (el kárdex de activos fijos ya trae el valor original y la depreciación acumulada contable en la misma fila).")
    if not st.session_state.af_cargados:
        af_file = st.file_uploader("Sube el Kárdex de Activos Fijos", type=["csv", "xlsx"], key="af_u")
        if af_file: st.session_state.df_af_kardex = leer_archivo_contable(af_file); st.session_state.af_cargados = True; st.rerun()
    else:
        st.success("🏁 Kárdex de activos fijos indexado.")
        if st.button("🔄 Cargar nuevo kárdex de activos", key="reset_af"): st.session_state.af_cargados, st.session_state.af_ejecutado = False, False; st.rerun()
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
        st.caption(f"📅 Fecha de corte usada para el cálculo: {fecha_corte.strftime('%d/%m/%Y')} (toma la Fecha Límite de Cierre configurada; si no hay una, usa hoy).")
        if st.button("🚀 Calcular Depreciación Esperada", type="primary", use_container_width=True):
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
                st.error(f"⚠️ No se pudo calcular la depreciación. Revisa que las columnas de valor, fecha y vida útil sean correctas. Detalle: {e}")
        if st.session_state.af_ejecutado:
            buffer_af = io.BytesIO()
            with pd.ExcelWriter(buffer_af, engine='openpyxl') as writer:
                st.session_state.af_conciliados.to_excel(writer, sheet_name='Activos_Correctos', index=False)
                st.session_state.af_discrepancias.to_excel(writer, sheet_name='Discrepancias', index=False)
            st.download_button(label="📥 Descargar Auditoría de Activo Fijo (.XLSX)", data=buffer_af.getvalue(), file_name="Reporte_Activo_Fijo.xlsx", use_container_width=True)
            taf1, taf2 = st.tabs(["✅ Activos Correctos", "⚠️ Discrepancias Encontradas"])
            with taf1: st.dataframe(st.session_state.af_conciliados, use_container_width=True)
            with taf2: st.dataframe(st.session_state.af_discrepancias, use_container_width=True)

def render_razones():
    st.write("")
    st.markdown('<div class="section-header">📈 Análisis de Razones Financieras</div>', unsafe_allow_html=True)
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
        fig_razones.update_layout(paper_bgcolor="#0D1117", plot_bgcolor="#0D1117", font_color="#E6EDF3", showlegend=False, coloraxis_showscale=False)
        st.plotly_chart(fig_razones, use_container_width=True)
    else:
        st.info("💡 Captura al menos algunas cifras para ver las razones calculadas.")

def render_sat():
    st.write("")
    st.markdown('<div class="section-header">🏛️ Checklist de Cumplimiento SAT</div>', unsafe_allow_html=True)
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
    if st.button("💾 Guardar Checklist SAT", use_container_width=True, key="guardar_sat"):
        st.session_state.sat_checklist = df_sat_editado
        registrar_evento("Cumplimiento SAT", "Actualizó el checklist de obligaciones fiscales")
        st.success("Checklist guardado.")
    vencidas = df_sat_editado[(df_sat_editado["Estado"] == "Pendiente") & (pd.to_datetime(df_sat_editado["Fecha_Límite"], errors='coerce') < pd.Timestamp(datetime.date.today()))]
    if not vencidas.empty:
        st.error(f"⚠️ {len(vencidas)} obligación(es) con fecha límite vencida y aún marcadas como 'Pendiente'.")

def render_aprobacion():
    st.write("")
    st.markdown('<div class="section-header">✅ Flujo de Revisión y Aprobación</div>', unsafe_allow_html=True)
    st.caption("Deja constancia de quién preparó, revisó y aprobó cada módulo. El rol de tu usuario autenticado determina qué acciones tienen sentido para ti (ver panel lateral).")
    estado_modulos_actual = calcular_estado_modulos()
    for modulo_info in estado_modulos_actual["modulos"]:
        nombre_mod = modulo_info["nombre"]
        estado_actual = st.session_state.estado_revision.get(nombre_mod, {"estado": "Preparado", "revisor": "", "fecha": "", "comentario": ""})
        with st.expander(f"{'✅' if modulo_info['ejecutado'] else ('🔵' if modulo_info['cargado'] else '🟠')} {nombre_mod}", expanded=False):
            ca1, ca2, ca3 = st.columns([1, 1, 2])
            with ca1:
                opciones_estado = ["Preparado", "Revisado", "Aprobado"]
                nuevo_estado = st.selectbox("Estado:", opciones_estado, index=opciones_estado.index(estado_actual["estado"]) if estado_actual["estado"] in opciones_estado else 0, key=f"estado_{nombre_mod}")
            with ca2:
                nuevo_revisor = st.text_input("Responsable:", value=estado_actual["revisor"], key=f"revisor_{nombre_mod}")
            with ca3:
                nuevo_comentario = st.text_input("Comentario:", value=estado_actual["comentario"], key=f"comentario_{nombre_mod}")
            if nuevo_estado == "Aprobado" and st.session_state.rol_actual == "Preparador":
                st.warning("💡 Tu rol actual es 'Preparador'. Normalmente solo un Revisor o Socio/Aprobador marca un módulo como Aprobado — puedes cambiar tu rol en el panel lateral si corresponde.")
            if st.button("💾 Guardar estado", key=f"guardar_estado_{nombre_mod}"):
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
    st.markdown('<div class="section-header">📋 Checklist de Documentos Solicitados al Cliente (PBC)</div>', unsafe_allow_html=True)
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
    if st.button("💾 Guardar Checklist PBC", use_container_width=True, key="guardar_pbc"):
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
    st.markdown('<div class="section-header">📜 Bitácora de Auditoría</div>', unsafe_allow_html=True)
    st.caption("Registro cronológico de las acciones realizadas en esta sesión (usuario, rol, módulo y acción). Se guarda dentro del respaldo JSON, pero se pierde si cierras el navegador sin descargarlo.")
    if st.session_state.bitacora_eventos:
        df_bitacora = pd.DataFrame(st.session_state.bitacora_eventos).iloc[::-1].reset_index(drop=True)
        st.dataframe(df_bitacora, use_container_width=True)
        buffer_bit = io.BytesIO()
        with pd.ExcelWriter(buffer_bit, engine='openpyxl') as writer:
            df_bitacora.to_excel(writer, sheet_name='Bitacora', index=False)
        st.download_button(label="📥 Descargar Bitácora (.XLSX)", data=buffer_bit.getvalue(), file_name="Bitacora_Auditoria.xlsx", use_container_width=True)
        if st.button("🗑️ Vaciar Bitácora", key="vaciar_bitacora"):
            st.session_state.bitacora_eventos = []
            st.rerun()
    else:
        st.info("💡 Aún no hay eventos registrados. Cada vez que ejecutes una conciliación o cambies un estado de aprobación, aparecerá aquí.")

def render_gestion_usuarios():
    st.write("")
    st.markdown('<div class="section-header">👥 Gestión de Usuarios</div>', unsafe_allow_html=True)
    if st.session_state.rol_actual != "Administrador":
        st.warning("🚫 Acceso restringido. Solo un usuario con rol **Administrador** puede entrar a este módulo.")
        return
    st.caption("Los usuarios viven en la memoria de este servidor mientras esté corriendo — no hay base de datos externa detrás. Si el servidor se reinicia, la lista vuelve a su estado inicial (solo el usuario admin).")

    st.markdown("#### ➕ Agregar Usuario")
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
    st.markdown("#### 📋 Usuarios Registrados")
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
                    st.markdown("🔴 Bloqueado")
                else:
                    st.markdown("🟢 Activo")
            with cu4:
                es_unico_admin = nombre_u in admins_activos and len(admins_activos) <= 1 and not info_u["bloqueado"]
                if st.button("🔓" if info_u["bloqueado"] else "🔒", key=f"toggle_bloqueo_{nombre_u}", help="Bloquear/Desbloquear", disabled=es_unico_admin):
                    st.session_state.usuarios_sistema[nombre_u]["bloqueado"] = not info_u["bloqueado"]
                    if not st.session_state.usuarios_sistema[nombre_u]["bloqueado"]:
                        st.session_state.usuarios_sistema[nombre_u]["intentos_fallidos"] = 0
                    registrar_evento("Gestión de Usuarios", f"{'Bloqueó' if st.session_state.usuarios_sistema[nombre_u]['bloqueado'] else 'Desbloqueó'} al usuario '{nombre_u}'")
                    st.rerun()
                if es_unico_admin:
                    st.caption("Único admin")
            with cu5:
                if st.button("🗑️", key=f"eliminar_usuario_{nombre_u}", help="Eliminar", disabled=(nombre_u == st.session_state.usuario_autenticado or es_unico_admin)):
                    del st.session_state.usuarios_sistema[nombre_u]
                    registrar_evento("Gestión de Usuarios", f"Eliminó al usuario '{nombre_u}'")
                    st.rerun()
            st.markdown("---")

def render_ayuda():
    st.write("")
    st.markdown('<div class="section-header">❓ Manual Operativo Diamond y Documentación de Herramientas</div>', unsafe_allow_html=True)
    st.markdown('<div class="help-card"><div class="help-title">📊 1. Dashboard General</div>Diagnóstico financiero global con indicadores semafóricos de riesgo y entregable PDF.</div>', unsafe_allow_html=True)
    st.markdown('<div class="help-card"><div class="help-title">🏦 2. Módulo Bancario (Bancos vs Auxiliar)</div>Cruce bidimensional por fecha e importe para cuadrar estados de cuenta con Auxiliar.</div>', unsafe_allow_html=True)
    st.markdown('<div class="help-card"><div class="help-title">📄 3. XML vs Contabilidad</div>Mapeo inteligente para amarrar facturas electrónicas e identificar CFDI omitidos.</div>', unsafe_allow_html=True)
    st.markdown('<div class="help-card"><div class="help-title">🧾 4. Clientes y Proveedores</div>Balanza de saldos globales contra reportes de antigüedad analíticos.</div>', unsafe_allow_html=True)
    st.markdown('<div class="help-card"><div class="help-title">🌐 5. Multidivisa USD</div>Algoritmo cambiario para calcular de forma exacta la ganancia o pérdida cambiaria.</div>', unsafe_allow_html=True)
    st.markdown('<div class="help-card"><div class="help-title">👔 6. Nómina CFDI</div>Cruzamiento masivo para verificar recibos de nómina timbrados ante el SAT vs pólizas.</div>', unsafe_allow_html=True)
    st.markdown('<div class="help-card"><div class="help-title">📦 7. Inventarios</div>Levantamiento físico real de auditoría contra los saldos del Kárdex contable.</div>', unsafe_allow_html=True)
    st.markdown('<div class="help-card"><div class="help-title">💸 8. IVA Flujo</div>Validar que el IVA determinado coincida con el flujo real reflejado en bancos.</div>', unsafe_allow_html=True)
    st.markdown('<div class="help-card"><div class="help-title">⚙️ 9. Configuración y Copias JSON</div>Gestión de membretes, tolerancias, fecha límite de cierre y carga/descarga de respaldos de sesión.</div>', unsafe_allow_html=True)
    st.markdown('<div class="help-card"><div class="help-title">🏭 10. Activo Fijo</div>Calcula la depreciación esperada en línea recta a partir del kárdex de activos y la compara contra la depreciación acumulada registrada en libros.</div>', unsafe_allow_html=True)
    st.markdown('<div class="help-card"><div class="help-title">📈 11. Razones Financieras</div>Captura cifras del Balance General y Estado de Resultados para obtener liquidez, apalancamiento, márgenes, ROA y ROE con su gráfica.</div>', unsafe_allow_html=True)
    st.markdown('<div class="help-card"><div class="help-title">🏛️ 12. Cumplimiento SAT</div>Checklist de obligaciones fiscales (ISR, IVA, DIOT, Nómina, 32-D, Contabilidad Electrónica) con fechas límite y estatus — no calcula impuestos, solo da seguimiento a lo que ya se presentó.</div>', unsafe_allow_html=True)
    st.markdown('<div class="help-card"><div class="help-title">✅ 13. Revisión y Aprobación</div>Marca cada módulo como Preparado, Revisado o Aprobado, con responsable, comentario y fecha — deja constancia de quién validó cada parte del trabajo.</div>', unsafe_allow_html=True)
    st.markdown('<div class="help-card"><div class="help-title">📋 14. Checklist PBC</div>Lista editable de documentos solicitados al cliente, con responsable, fecha límite y estatus de recepción.</div>', unsafe_allow_html=True)
    st.markdown('<div class="help-card"><div class="help-title">📜 15. Bitácora de Auditoría</div>Registro cronológico de acciones (usuario, rol, módulo, acción y hora) de todo lo ejecutado en la sesión, exportable a Excel.</div>', unsafe_allow_html=True)
    st.markdown('<div class="help-card"><div class="help-title">👤 Panel Lateral: Sesión, Multiempresa y Notificaciones</div>Muestra tu usuario y rol autenticados, permite cerrar sesión, guardar/alternar entre varias auditorías en la misma sesión, y revisa alertas de fechas límite, insumos faltantes o documentos PBC pendientes.</div>', unsafe_allow_html=True)
    st.markdown('<div class="help-card"><div class="help-title">👥 16. Gestión de Usuarios (solo Administrador)</div>Agrega, bloquea/desbloquea y elimina usuarios del sistema. Requiere haber iniciado sesión con un usuario con rol Administrador.</div>', unsafe_allow_html=True)

# ==============================================================================
# 5. NAVEGACIÓN FINAL: PESTAÑAS AGRUPADAS POR CATEGORÍA
# ==============================================================================
# Se construye hasta aquí (y no arriba) porque necesita que todas las
# funciones render_x() ya estén definidas. Agrupar por categoría, en vez de
# una sola barra plana de 17 pestañas, evita que la navegación se desborde
# visualmente y ayuda a que la app se sienta organizada por área de trabajo.
CATEGORIAS = {
    "📊 Panel General": [("📊 Dashboard", render_dashboard)],
    "🔄 Conciliaciones": [
        ("🏦 Bancos vs Auxiliar", render_bancos),
        ("📄 XML vs Contabilidad", render_xml),
        ("🧾 Clientes y Proveedores", render_saldos),
        ("🌐 Multidivisa USD", render_multidivisa),
        ("👔 Nómina CFDI", render_nomina),
        ("📦 Inventarios", render_inventarios),
        ("💸 IVA Flujo", render_iva),
        ("🏭 Activo Fijo", render_activo_fijo),
    ],
    "📈 Análisis y Cumplimiento": [
        ("📈 Razones Financieras", render_razones),
        ("🏛️ Cumplimiento SAT", render_sat),
    ],
    "🛡️ Gobierno y Auditoría": [
        ("✅ Revisión y Aprobación", render_aprobacion),
        ("📋 Checklist PBC", render_pbc),
        ("📜 Bitácora", render_bitacora),
    ],
    "⚙️ Sistema": [
        ("⚙️ Configuración", render_configuracion),
        ("👥 Gestión de Usuarios", render_gestion_usuarios),
        ("❓ Ayuda", render_ayuda),
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
