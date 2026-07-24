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
    .main-title { font-size: 38px !important; font-weight: 700 !important; color: #00D4FF; margin-bottom: 5px; }
    .subtitle { font-size: 16px !important; color: #639FAB; margin-bottom: 30px; font-weight: 500; }
    .section-header { color: #00D4FF; font-weight: 600; border-bottom: 2px solid #161B22; padding-bottom: 10px; margin-bottom: 20px; font-size: 22px; }
    .kpi-card { padding: 15px; border-radius: 6px; color: #0D1117; font-weight: 700; text-align: center; margin-bottom: 15px; }
    .kpi-green { background-color: #2ECC71 !important; }
    .kpi-yellow { background-color: #F1C40F !important; }
    .kpi-red { background-color: #E74C3C !important; }
    .help-card { background-color: #161B22; padding: 20px; border-radius: 8px; margin-bottom: 15px; border-left: 4px solid #00D4FF; }
    .help-title { color: #00D4FF; font-size: 18px; font-weight: 600; margin-bottom: 10px; }
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
    .bl-badge-blue { background:#22284D; color:#A5B4FC; }
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
    'fase_progreso': 1, 'empresa': "", 'periodo': "", 'auditor': "", 'tolerancia': 0.50, 'tolerancia_dias': 3, 'tolerancia_inventario': 1.0, 'divisa': "MXN ($)", 'logo_bytes': None, 'fecha_limite_cierre': None
}

for llave, valor_defecto in variables_sesion.items():
    if llave not in st.session_state: st.session_state[llave] = valor_defecto

# ==============================================================================
# 3. NAVEGACIÓN SUPERIOR INTEGRAL DE 10 PESTAÑAS CORPORATIVAS
# ==============================================================================
tab_dashboard, tab_bancos, tab_xml, tab_saldos, tab_multidivisa, tab_nomina, tab_inventarios, tab_iva, tab_configuracion, tab_ayuda = st.tabs([
    "📊 Dashboard", "🏦 Bancos vs Auxiliar", "📄 XML vs Contabilidad", "🧾 Clientes y Proveedores", 
    "🌐 Multidivisa USD", "👔 Nómina CFDI", "📦 Inventarios", "💸 IVA Flujo", "⚙️ Configuración", "❓ Ayuda"
])

# ==============================================================================
# 4. PANEL LATERAL (IDENTIDAD CORPORATIVA FIJA Y UTILERÍAS)
# ==============================================================================
if st.session_state.logo_bytes is not None: st.sidebar.image(st.session_state.logo_bytes, use_container_width=True)
else: st.sidebar.info("🏢 Sin Logotipo Institucional. Configúralo en la pestaña superior de Configuración.")

if st.sidebar.button("🔒 Cerrar Sesión", type="primary", use_container_width=True, key="sidebar_logout_btn"):
    for llave in variables_sesion.keys(): st.session_state[llave] = variables_sesion[llave]
    st.rerun()

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
    pattern = r'^[A-Z&Ñ]{3,4}[0-9]{2}(0[1-9]|1[0-2])(0[1-9]|[0-9]|3)[A-Z0-9]{3}$'
    return bool(re.match(pattern, str(rfc).upper().strip()))
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

with tab_dashboard:
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
with tab_configuracion:
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

    # RESTAURADOS AQUÍ LOS BOTONES DE RESPALDO JSON COMPLETOS
    st.markdown("---")
    st.subheader("💾 Copias de Seguridad de la Auditoría (.JSON)")
    col_j1, col_j2 = st.columns(2)
    with col_j1:
        if st.session_state.bancos_ejecutado or st.session_state.xml_ejecutado or st.session_state.saldos_ejecutado:
            respaldo_dinamico = {}
            for llave in variables_sesion.keys():
                valor = st.session_state[llave]
                if isinstance(valor, pd.DataFrame): respaldo_dinamico[llave] = {"tipo": "dataframe", "datos": valor.to_json(orient='split')}
                elif llave == 'logo_bytes' and valor is not None: respaldo_dinamico[llave] = {"tipo": "bytes", "datos": valor.hex()}
                else: respaldo_dinamico[llave] = {"tipo": "nativo", "datos": valor}
            st.download_button(label="📥 Descargar Respaldo JSON", data=json.dumps(respaldo_dinamico), file_name="Backup_TaxFlow.json", mime="application/json", use_container_width=True)
        else:
            st.info("💡 Ejecuta algún módulo de conciliación primero para poder descargar un respaldo .JSON")
            
    with col_j2:
        archivo_json_cargado = st.file_uploader("Sube tu archivo de respaldo (.JSON)", type=["json"], key="json_config_uploader")
        if archivo_json_cargado is not None:
            try:
                datos_restaurados = json.load(archivo_json_cargado)
                for llave, paquete in datos_restaurados.items():
                    if paquete["tipo"] == "dataframe" and paquete["datos"] is not None: st.session_state[llave] = pd.read_json(io.StringIO(paquete["datos"]), orient='split')
                    elif paquete["tipo"] == "bytes" and paquete["datos"] is not None: st.session_state[llave] = bytes.fromhex(paquete["datos"])
                    else: st.session_state[llave] = paquete["datos"]
                st.success("✓ Ecosistema restaurado desde el JSON con éxito.")
                st.rerun()
            except Exception as e: st.error(f"Error JSON: {e}")
with tab_bancos:
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

with tab_xml:
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

with tab_saldos:
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
            st.session_state.saldos_ejecutado = True; st.rerun()
        if st.session_state.saldos_ejecutado:
            t_s1, t_s2 = st.tabs(["✅ Saldos Correctos", "⚠️ Discrepancias Encontradas"])
            with t_s1: st.dataframe(st.session_state.saldos_conciliados, use_container_width=True)
            with t_s2: st.dataframe(st.session_state.saldos_discrepancias, use_container_width=True)
with tab_multidivisa:
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

with tab_nomina:
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

with tab_inventarios:
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

with tab_iva:
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

with tab_ayuda:
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
    st.markdown('<div class="help-card"><div class="help-title">⚙️ 9. Configuración y Copias JSON</div>Gestión de membretes, tolerancia decimal y carga/descarga de respaldos de sesión.</div>', unsafe_allow_html=True)
