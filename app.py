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
    'df_xml_gastos': None, 'df_aux_gastos': None, 'xml_cargados': False, 'xml_ejecutado': False, 'xml_conciliados': None, 'xml_pendientes': None,
    'df_saldos_globales': None, 'df_facturas_detalle': None, 'saldos_cargados': False, 'saldos_ejecutado': False, 'saldos_conciliados': None, 'saldos_discrepancias': None,
    'df_divisa_ext': None, 'df_divisa_nac': None, 'divisa_cargados': False, 'divisa_ejecutado': False, 'divisa_conciliados': None, 'tc_auditoria_val': 17.50,
    'df_cfdi_nomina': None, 'df_aux_nomina': None, 'nomina_cargados': False, 'nomina_ejecutado': False, 'nomina_conciliados': None, 'nomina_discrepancias': None,
    'df_inv_fisico': None, 'df_kardex_er': None, 'inventarios_cargados': False, 'inventarios_ejecutado': False, 'inventarios_conciliados': None, 'inventarios_discrepancias': None,
    'df_iva_banco': None, 'df_iva_aux': None, 'iva_cargados': False, 'iva_ejecutado': False, 'iva_conciliados': None, 'iva_discrepancias': None,
    'fase_progreso': 1, 'empresa': "", 'periodo': "", 'auditor': "", 'tolerancia': 0.50, 'divisa': "MXN ($)", 'logo_bytes': None
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

with tab_dashboard:
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
    col_conf1, col_conf2 = st.columns(2)
    with col_conf1: st.session_state.tolerancia = st.slider("Tolerancia Centavos:", 0.00, 5.00, value=float(st.session_state.tolerancia), step=0.10)
    with col_conf2:
        lista_divisas = ["MXN ($)", "USD ($)", "EUR (€)"]
        st.session_state.divisa = st.selectbox("Divisa Base:", lista_divisas, index=lista_divisas.index(st.session_state.divisa) if st.session_state.divisa in lista_divisas else 0)
    
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
            df_b_c = df_b.dropna(subset=[cb_m, cb_f]).copy(); df_a_c = df_a.dropna(subset=[ca_m, ca_f]).copy()
            df_b_c['Monto_Limpio'] = pd.to_numeric(df_b_c[cb_m], errors='coerce').fillna(0).abs(); df_a_c['Monto_Limpio'] = pd.to_numeric(df_a_c[ca_m], errors='coerce').fillna(0).abs()
            df_b_c['Fecha_Limpia'] = pd.to_datetime(df_b_c[cb_f], format='mixed', dayfirst=True).dt.date; df_a_c['Fecha_Limpia'] = pd.to_datetime(df_a_c[ca_f], format='mixed', dayfirst=True).dt.date
            df_b_s, df_a_s = df_b_c.sort_values('Monto_Limpio').reset_index(drop=True), df_a_c.sort_values('Monto_Limpio').reset_index(drop=True)
            df_m = pd.merge_asof(df_b_s, df_a_s, on='Monto_Limpio', tolerance=st.session_state.tolerancia, direction='nearest', suffixes=('_Banco', '_Auxiliar')).dropna(subset=[ca_m])
            st.session_state.df_conciliados = df_m[df_m['Fecha_Limpia_Banco'] == df_m['Fecha_Limpia_Auxiliar']]
            st.session_state.bancos_pendientes = df_b_c[~df_b_c['Monto_Limpio'].isin(st.session_state.df_conciliados['Monto_Limpio'])].drop(columns=['Monto_Limpio', 'Fecha_Limpia'], errors='ignore')
            st.session_state.auxiliar_pendientes = df_a_c[~df_a_c['Monto_Limpio'].isin(st.session_state.df_conciliados['Monto_Limpio'])].drop(columns=['Monto_Limpio', 'Fecha_Limpia'], errors='ignore')
            st.session_state.suma_conciliado = st.session_state.df_conciliados[cb_m].astype(float).abs().sum(); st.session_state.suma_banco_p = st.session_state.bancos_pendientes[cb_m].astype(float).abs().sum(); st.session_state.suma_aux_p = st.session_state.auxiliar_pendientes[ca_m].astype(float).abs().sum(); st.session_state.bancos_ejecutado = True; st.session_state.fase_progreso = 4; st.rerun()
        if st.session_state.bancos_ejecutado:
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
    if st.session_state.xml_cargados:
        cx1, cx2 = st.columns(2); xml_m = st.selectbox("Monto XML:", st.session_state.df_xml_gastos.columns, key="xml_m"); cont_m = st.selectbox("Monto Auxiliar Gasto:", st.session_state.df_aux_gastos.columns, key="cont_m")
        if st.button("🚀 Cruce XML vs Contabilidad", type="primary", use_container_width=True):
            st.session_state.df_xml_gastos['Monto_Limpio'] = pd.to_numeric(st.session_state.df_xml_gastos[xml_m], errors='coerce').fillna(0).abs()
            st.session_state.df_aux_gastos['Monto_Limpio'] = pd.to_numeric(st.session_state.df_aux_gastos[cont_m], errors='coerce').fillna(0).abs()
            st.session_state.xml_conciliados = pd.merge(st.session_state.df_xml_gastos, st.session_state.df_aux_gastos, on='Monto_Limpio', how='inner'); st.session_state.xml_ejecutado = True; st.rerun()
        if st.session_state.xml_ejecutado: st.dataframe(st.session_state.xml_conciliados, use_container_width=True)

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
            df_fd_grouped = df_fd.groupby(id_cte)[fd_m].sum().reset_index()
            df_fd_grouped.columns = [id_cte, 'Suma_Detalle_Facturas']
            df_cruce = pd.merge(df_sg, df_fd_grouped, on=id_cte, how='outer')
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
        col_v1, col_v2 = st.columns(2)
        with col_v1: de_m = st.selectbox("Monto en Dólares (USD):", df_ext.columns, key="de_m_new")
        with col_v2: dn_m = st.selectbox("Monto en Moneda Nacional (MXN):", df_nac.columns, key="dn_m_new")
        if st.button("🚀 Calcular Fluctuación Cambiaria Analítica", type="primary", use_container_width=True):
            df_ext['Monto_Limpio'] = pd.to_numeric(df_ext[de_m], errors='coerce').fillna(0).abs(); df_nac['Monto_Limpio'] = pd.to_numeric(df_nac[dn_m], errors='coerce').fillna(0).abs()
            df_ext_s, df_nac_s = df_ext.sort_values('Monto_Limpio').reset_index(drop=True), df_nac.sort_values('Monto_Limpio').reset_index(drop=True)
            df_v_m = pd.merge_asof(df_ext_s, df_nac_s, on='Monto_Limpio', direction='nearest', suffixes=('_USD', '_Local'))
            df_v_m['Valor_Contable_Esperado'] = (df_v_m['Monto_Limpio'] * st.session_state.tc_auditoria_val).round(2)
            df_v_m['Monto_Local_Real'] = pd.to_numeric(df_v_m[dn_m], errors='coerce').fillna(0).abs()
            df_v_m['Diferencia_Fluctuacion'] = (df_v_m['Valor_Contable_Esperado'] - df_v_m['Monto_Local_Real']).round(2)
            st.session_state.divisa_conciliados = df_v_m; st.session_state.divisa_ejecutado = True; st.rerun()
        if st.session_state.divisa_ejecutado: st.dataframe(st.session_state.divisa_conciliados, use_container_width=True)

with tab_nomina:
    st.write("")
    st.markdown('<div class="section-header">👔 Auditoría de Nómina: CFDI Timbrados vs Auxiliar</div>', unsafe_allow_html=True)
    if not st.session_state.nomina_cargados:
        cn_1, cn_2 = st.columns(2)
        with cn_1: n_xml = st.file_uploader("Sube XML Nómina", type=["csv", "xlsx"], key="nx")
        with cn_2: n_aux = st.file_uploader("Sube Auxiliar Sueldos", type=["csv", "xlsx"], key="na")
        if n_xml and n_aux: st.session_state.df_cfdi_nomina = leer_archivo_contable(n_xml); st.session_state.df_aux_nomina = leer_archivo_contable(n_aux); st.session_state.nomina_cargados = True; st.rerun()
    if st.session_state.nomina_cargados:
        cln1, cln2 = st.columns(2); nx_m = st.selectbox("Monto CFDI:", st.session_state.df_cfdi_nomina.columns, key="nx_m"); na_m = st.selectbox("Monto Libros:", st.session_state.df_aux_nomina.columns, key="na_m")
        if st.button("🚀 Conciliar Nóminas", type="primary", use_container_width=True):
            st.session_state.df_cfdi_nomina['Monto_Limpio'] = pd.to_numeric(st.session_state.df_cfdi_nomina[nx_m], errors='coerce').fillna(0).abs()
            st.session_state.df_aux_nomina['Monto_Limpio'] = pd.to_numeric(st.session_state.df_aux_nomina[na_m], errors='coerce').fillna(0).abs()
            st.session_state.nomina_conciliados = pd.merge(st.session_state.df_cfdi_nomina, st.session_state.df_aux_nomina, on='Monto_Limpio', how='inner'); st.session_state.nomina_ejecutado = True; st.rerun()
        if st.session_state.nomina_ejecutado: st.dataframe(st.session_state.nomina_conciliados, use_container_width=True)

with tab_inventarios:
    st.write("")
    st.markdown('<div class="section-header">📦 Inventarios Físicos vs Almacén ERP</div>', unsafe_allow_html=True)
    if not st.session_state.inventarios_cargados:
        ci_1, ci_2 = st.columns(2)
        with ci_1: inf = st.file_uploader("Conteo Físico Real", type=["csv", "xlsx"], key="inf")
        with ci_2: ke = st.file_uploader("Kárdex Teórico Contable", type=["csv", "xlsx"], key="ke")
        if inf and ke: st.session_state.df_inv_fisico = leer_archivo_contable(inf); st.session_state.df_kardex_er = leer_archivo_contable(ke); st.session_state.inventarios_cargados = True; st.rerun()
    if st.session_state.inventarios_cargados:
        cli1, cli2, cli3 = st.columns(3); id_prod = st.selectbox("SKU/Código:", st.session_state.df_inv_fisico.columns, key="id_p"); if_q = st.selectbox("Cant Física:", st.session_state.df_inv_fisico.columns, key="if_q"); ke_q = st.selectbox("Cant ERP:", st.session_state.df_kardex_er.columns, key="ke_q")
        if st.button("🚀 Auditar Almacenes", type="primary", use_container_width=True):
            st.session_state.df_inv_fisico['Q_Fisica'] = pd.to_numeric(st.session_state.df_inv_fisico[if_q], errors='coerce').fillna(0)
            st.session_state.df_kardex_er['Q_ERP'] = pd.to_numeric(st.session_state.df_kardex_er[ke_q], errors='coerce').fillna(0)
            st.session_state.inventarios_conciliados = pd.merge(st.session_state.df_inv_fisico, st.session_state.df_kardex_er, on=id_prod, how='outer'); st.session_state.inventarios_ejecutado = True; st.rerun()
        if st.session_state.inventarios_ejecutado: st.dataframe(st.session_state.inventarios_conciliados, use_container_width=True)

with tab_iva:
    st.write("")
    st.markdown('<div class="section-header">💸 IVA Efectivamente Cobrado / Pagado (Flujo de Efectivo)</div>', unsafe_allow_html=True)
    if not st.session_state.iva_cargados:
        civ_1, civ_2 = st.columns(2)
        with civ_1: iv_b = st.file_uploader("Flujo Bancos con IVA", type=["csv", "xlsx"], key="iv_b")
        with civ_2: iv_a = st.file_uploader("Determinación Mensual IVA", type=["csv", "xlsx"], key="iv_a")
        if iv_b and iv_a: st.session_state.df_iva_banco = leer_archivo_contable(iv_b); st.session_state.df_iva_aux = leer_archivo_contable(iv_a); st.session_state.iva_cargados = True; st.rerun()
    if st.session_state.iva_cargados:
        cliv1, cliv2 = st.columns(2); ib_m = st.selectbox("Importe Banco:", st.session_state.df_iva_banco.columns, key="ib_m"); ia_m = st.selectbox("Importe Papel IVA:", st.session_state.df_iva_aux.columns, key="ia_m")
        if st.button("🚀 Amarre IVA Flujo", type="primary", use_container_width=True):
            st.session_state.df_iva_banco['Monto_Limpio'] = pd.to_numeric(st.session_state.df_iva_banco[ib_m], errors='coerce').fillna(0).abs()
            st.session_state.df_iva_aux['Monto_Limpio'] = pd.to_numeric(st.session_state.df_iva_aux[ia_m], errors='coerce').fillna(0).abs()
            st.session_state.iva_conciliados = pd.merge(st.session_state.df_iva_banco, st.session_state.df_iva_aux, on='Monto_Limpio', how='inner'); st.session_state.iva_ejecutado = True; st.rerun()
        if st.session_state.iva_ejecutado: st.dataframe(st.session_state.iva_conciliados, use_container_width=True)

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
