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
# 1. CONFIGURACIÓN DE NIVEL EMPRESARIAL (SUITE PREMIUM)
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
    
    /* Tarjetas de Alerta Semafórica Condicional */
    .kpi-card { padding: 15px; border-radius: 6px; color: #0D1117; font-weight: 700; text-align: center; margin-bottom: 15px; }
    .kpi-green { background-color: #2ECC71 !important; }
    .kpi-yellow { background-color: #F1C40F !important; }
    .kpi-red { background-color: #E74C3C !important; }
    
    div.stButton > button:first-child[data-testid="stSidebarActionButton"] {
        background-color: #00D4FF !important;
        color: #0D1117 !important;
        font-weight: 700 !important;
        border: none !important;
    }
    </style>
""", unsafe_allow_html=True)

st.markdown('<div class="main-title">💎 TaxFlow-Diamond</div>', unsafe_allow_html=True)
st.markdown('<div class="subtitle">Enterprise Financial & XML Reconciliation Suite</div>', unsafe_allow_html=True)

# ==============================================================================
# 2. SISTEMA DE MEMORIA INTEGRAL CON PERSISTENCIA DE WORKFLOW
# ==============================================================================
variables_sesion = {
    # Módulo Bancos
    'df_banco': None, 'df_auxiliar': None, 'bancos_cargados': False, 'bancos_ejecutado': False,
    'df_conciliados': None, 'bancos_pendientes': None, 'auxiliar_pendientes': None,
    'suma_conciliado': 0.0, 'suma_banco_p': 0.0, 'suma_aux_p': 0.0,
    # Módulo XML
    'df_xml_gastos': None, 'df_aux_gastos': None, 'xml_cargados': False, 'xml_ejecutado': False,
    'xml_conciliados': None, 'xml_pendientes': None,
    # Módulo Clientes/Proveedores
    'df_saldos_globales': None, 'df_facturas_detalle': None, 'saldos_cargados': False, 'saldos_ejecutado': False,
    'saldos_conciliados': None, 'saldos_discrepancias': None,
    # Módulo Multidivisa
    'df_divisa_ext': None, 'df_divisa_nac': None, 'divisa_cargados': False, 'divisa_ejecutado': False,
    'divisa_conciliados': None, 'tc_auditoria_val': 17.50,
    # Globales
    'fase_progreso': 1, 'empresa': "", 'periodo': "", 'auditor': "", 'tolerancia': 0.50, 'divisa': "MXN ($)", 'logo_bytes': None
}

for llave, valor_defecto in variables_sesion.items():
    if llave not in st.session_state:
        st.session_state[llave] = valor_defecto

# ==============================================================================
# 3. NAVEGACIÓN SUPERIOR INTEGRAL (7 PESTAÑAS COMPLETAS)
# ==============================================================================
st.markdown('<div class="section-header">🗺️ Módulos de la Suite</div>', unsafe_allow_html=True)
tab_dashboard, tab_bancos, tab_xml, tab_saldos, tab_multidivisa, tab_configuracion, tab_ayuda = st.tabs([
    "📊 Dashboard", "🏦 Bancos vs Auxiliar", "📄 XML vs Contabilidad", "🧾 Clientes y Proveedores", "🌐 Multidivisa USD", "⚙️ Configuración", "❓ Ayuda"
])

# ==============================================================================
# 4. BARRA LATERAL CON LOGOTIPO FIJO Y PLANTILLAS DE EJEMPLO CORPORATIVAS
# ==============================================================================
if st.session_state.logo_bytes is not None:
    st.sidebar.image(st.session_state.logo_bytes, use_container_width=True)
else:
    st.sidebar.info("🏢 Sin Logotipo Institucional. Configúralo en la pestaña superior de Configuración.")

if st.sidebar.button("🔒 Cerrar Sesión", type="primary", use_container_width=True, key="sidebar_logout_btn"):
    for llave in variables_sesion.keys(): st.session_state[llave] = variables_sesion[llave]
    st.rerun()

st.sidebar.markdown("---")
st.sidebar.markdown("### 📥 Descarga de Plantillas Corporativas")
st.sidebar.write("Descarga los formatos estándar para evitar errores de estructura:")

buffer_p1 = io.BytesIO()
with pd.ExcelWriter(buffer_p1, engine='openpyxl') as w:
    pd.DataFrame(columns=["Fecha", "Concepto", "Referencia", "Importe", "RFC_Contraparte"]).to_excel(w, index=False)
st.sidebar.download_button("📊 Plantilla Estado de Cuenta", data=buffer_p1.getvalue(), file_name="Plantilla_Estado_Cuenta.xlsx", use_container_width=True)

buffer_p2 = io.BytesIO()
with pd.ExcelWriter(buffer_p2, engine='openpyxl') as w:
    pd.DataFrame(columns=["Fecha_Poliza", "Cuenta_Contable", "Concepto_Movimiento", "Monto_Registro", "RFC_Validar"]).to_excel(w, index=False)
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
# ==============================================================================
# 5. GENERADOR DE DICTAMEN DE AUDITORÍA FORMAL EN FORMATO PDF
# ==============================================================================
def generar_dictamen_pdf(empresa, periodo, auditor, conciliado, banco_p, aux_p, divisa):
    fig, ax = plt.subplots(figsize=(8.5, 11))
    ax.axis('off')
    plt.text(0.1, 0.92, "TAXFLOW-DIAMOND FINANCIAL SUITE", fontsize=16, weight='bold', color='#00A4CC')
    plt.text(0.1, 0.89, "DICTAMEN FORMAL DE AUDITORÍA Y CONCILIACIÓN DE LIBROS", fontsize=12, weight='bold')
    plt.text(0.1, 0.85, "------------------------------------------------------------------------------------------------------------------------", color='gray')
    plt.text(0.1, 0.78, f"Razón Social del Cliente: {empresa if empresa else 'No Especificada'}", fontsize=11)
    plt.text(0.1, 0.75, f"Periodo Fiscal Auditado: {periodo if periodo else 'No Especificado'}", fontsize=11)
    plt.text(0.1, 0.72, f"Auditor Responsable: {auditor if auditor else 'No Especificado'}", fontsize=11)
    plt.text(0.1, 0.65, "RESUMEN DE CUENTAS EVALUADAS", fontsize=12, weight='bold', color='#00A4CC')
    plt.text(0.1, 0.60, f"(*) Capital Conciliado y Alineado: {divisa} {conciliado:,.2f}", fontsize=11)
    plt.text(0.1, 0.57, f"(*) Inconsistencias en Estado de Cuenta (Banco): {divisa} {banco_p:,.2f}", fontsize=11)
    plt.text(0.1, 0.54, f"(*) Inconsistencias en Libro Mayor (Auxiliar): {divisa} {aux_p:,.2f}", fontsize=11)
    total_desfase = banco_p + aux_p
    riesgo_status = "CRÍTICO" if total_desfase > (conciliado * 0.05) else "ACEPTABLE"
    plt.text(0.1, 0.45, f"DICTAMEN FINAL DEL AUDITOR: REVISIÓN CON STATUS {riesgo_status}", fontsize=12, weight='bold', color='red' if riesgo_status == "CRÍTICO" else 'green')
    dictamen_txt = "Habiendo aplicado los algoritmos de validación cruzada y cruzamiento por doble factor (Monto + Fecha)\nse concluye que los libros contables presentan una consistencia alineada con los parámetros de negocio."
    plt.text(0.1, 0.35, dictamen_txt, fontsize=10, style='italic')
    plt.text(0.1, 0.18, "___________________________________", weight='bold')
    plt.text(0.1, 0.14, f"{auditor if auditor else 'Firma del Auditor Encargado'}\nRepresentante de Auditoría Externa", fontsize=10)
    pdf_buffer = io.BytesIO()
    plt.savefig(pdf_buffer, format='pdf', bbox_inches='tight', dpi=300)
    plt.close()
    return pdf_buffer.getvalue()

# ==============================================================================
# 6. DESPLIEGUE: PESTAÑA DASHBOARD GENERAL (SEMÁFORO DE RIESGO Y KPIS)
# ==============================================================================
with tab_dashboard:
    st.write("")
    fases = ["1. Configuración", "2. Carga Insumos", "3. Mapeo Columnas", "4. Reportes y Dictamen"]
    st.progress(st.session_state.fase_progreso / 4, text=f"Progreso del Flujo de Trabajo: **{fases[st.session_state.fase_progreso - 1]}**")
    st.write("")

    if st.session_state.bancos_ejecutado:
        st.markdown('<div class="section-header">📊 Indicadores de Riesgo Corporativo</div>', unsafe_allow_html=True)
        total_pendientes = st.session_state.suma_banco_p + st.session_state.suma_aux_p
        porcentaje_riesgo = (total_pendientes / st.session_state.suma_conciliado * 100) if st.session_state.suma_conciliado > 0 else 0
        if porcentaje_riesgo <= 2.0: class_semaforo, mensaje_semaforo = "kpi-green", "🟢 NIVEL DE RIESGO BAJO: Cuentas y Libros Alineados."
        elif porcentaje_riesgo <= 5.0: class_semaforo, mensaje_semaforo = "kpi-yellow", "🟡 NIVEL DE RIESGO MODERADO: Monitorear partidas en tránsito."
        else: class_semaforo, mensaje_semaforo = "kpi-red", "🔴 ALERTA DE AUDITORÍA - RIESGO ALTO: Desfase financiero crítico."
        st.markdown(f'<div class="kpi-card {clase_semaforo}">{mensaje_semaforo} ({porcentaje_riesgo:.2f}% de desfase)</div>', unsafe_allow_html=True)
        
        m1, m2, m3 = st.columns(3)
        simbolo = st.session_state.divisa.split(" ")
        m1.metric("Capital Conciliado", f"{simbolo} {st.session_state.suma_conciliado:,.2f}")
        m2.metric("Pendientes Banco", f"{simbolo} {st.session_state.suma_banco_p:,.2f}", delta_color="inverse")
        m3.metric("Pendientes Auxiliar", f"{simbolo} {st.session_state.suma_aux_p:,.2f}", delta_color="inverse")
        
        df_grafico = pd.DataFrame({"Concepto": ["Saldos Conciliados", "Pendientes Banco", "Pendientes Auxiliar"], "Importe": [st.session_state.suma_conciliado, st.session_state.suma_banco_p, st.session_state.suma_aux_p]})
        fig = px.pie(df_grafico, values="Importe", names="Concepto", color_discrete_sequence=["#00D4FF", "#FF4B4B", "#FFA500"], hole=0.4)
        fig.update_layout(template="plotly_dark", paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
        st.plotly_chart(fig, use_container_width=True)
        
        pdf_dictamen = generar_dictamen_pdf(st.session_state.empresa, st.session_state.periodo, st.session_state.auditor, st.session_state.suma_conciliado, st.session_state.suma_banco_p, st.session_state.suma_aux_p, simbolo)
        st.download_button(label="📥 Descargar Dictamen Formal Certificado (PDF Oficial)", data=pdf_dictamen, file_name="Dictamen_Auditoria.pdf", mime="application/pdf", use_container_width=True)
    else: st.info("💎 Suite Corporativa TaxFlow-Diamond inicializada. Dirígete al Módulo Bancario para comenzar la auditoría.")

# ==============================================================================
# 7. DESPLIEGUE: PESTAÑA CONFIGURACIÓN Y BACKUPS
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
    with col_conf1: st.session_state.tolerancia = st.slider("Margen de Tolerancia de Centavos:", 0.00, 5.00, value=float(st.session_state.tolerancia), step=0.10)
    with col_conf2:
        lista_divisas = ["MXN ($)", "USD ($)", "EUR (€)"]
        st.session_state.divisa = st.selectbox("Divisa de Presentación de Reportes:", lista_divisas, index=lista_divisas.index(st.session_state.divisa) if st.session_state.divisa in lista_divisas else 0)
    
    st.markdown("---")
    logo_file = st.file_uploader("Sube o actualiza el logotipo corporativo (PNG, JPG)", type=["png", "jpg", "jpeg", "webp"], key="logo_config")
    if logo_file is not None:
        nuevos_bytes = logo_file.read()
        if st.session_state.logo_bytes != nuevos_bytes:
            st.session_state.logo_bytes = nuevos_bytes
            st.session_state.fase_progreso = 2
            st.rerun()

    st.markdown("---")
    st.subheader("💾 Copias de Seguridad de la Auditoría (.JSON)")
    col_j1, col_j2 = st.columns(2)
    with col_j1:
        if st.session_state.bancos_ejecutado or st.session_state.xml_ejecutado:
            respaldo_dinamico = {}
            for llave in variables_sesion.keys():
                valor = st.session_state[llave]
                if isinstance(valor, pd.DataFrame): respaldo_dinamico[llave] = {"tipo": "dataframe", "datos": valor.to_json(orient='split')}
                elif llave == 'logo_bytes' and valor is not None: respaldo_dinamico[llave] = {"tipo": "bytes", "datos": valor.hex()}
                else: respaldo_dinamico[llave] = {"tipo": "nativo", "datos": valor}
            st.download_button(label="📥 Descargar Respaldo JSON", data=json.dumps(respaldo_dinamico), file_name="Backup_TaxFlow.json", mime="application/json", use_container_width=True)
    with col_j2:
        archivo_json_cargado = st.file_uploader("Sube tu archivo de respaldo (.JSON)", type=["json"], key="json_config_uploader")
        if archivo_json_cargado is not None:
            try:
                datos_restaurados = json.load(archivo_json_cargado)
                for llave, paquete in datos_restaurados.items():
                    if paquete["tipo"] == "dataframe" and paquete["datos"] is not None: st.session_state[llave] = pd.read_json(io.StringIO(paquete["datos"]), orient='split')
                    elif paquete["tipo"] == "bytes" and paquete["datos"] is not None: st.session_state[llave] = bytes.fromhex(paquete["datos"])
                    else: st.session_state[llave] = paquete["datos"]
                st.success("✓ Restaurado al 100%.")
                st.rerun()
            except Exception as e: st.error(f"Error JSON: {e}")
# ==============================================================================
# 8. DESPLIEGUE: PESTAÑA MÓDULO 1 - BANCOS VS AUXILIAR
# ==============================================================================
with tab_bancos:
    st.write("")
    st.markdown('<div class="section-header">🏦 Módulo Bancario: Estado de Cuenta vs Auxiliar Contable Interno</div>', unsafe_allow_html=True)
    if not st.session_state.bancos_cargados:
        st.session_state.fase_progreso = 2
        c_b1, c_b2 = st.columns(2)
        with c_b1: b_file = st.file_uploader("Sube Estado de Cuenta Bancario", type=["csv", "xlsx"], key="b_u")
        with c_b2: a_file = st.file_uploader("Sube Auxiliar Contable de Bancos", type=["csv", "xlsx"], key="a_u")
        if b_file and a_file:
            st.session_state.df_banco = leer_archivo_contable(b_file)
            st.session_state.df_auxiliar = leer_archivo_contable(a_file)
            st.session_state.bancos_cargados = True
            st.session_state.fase_progreso = 3
            st.rerun()
    else:
        st.success("🏁 Insumos bancarios indexados.")
        if st.button("🔄 Cargar nuevos archivos de banco", key="reset_b"):
            st.session_state.bancos_cargados, st.session_state.bancos_ejecutado = False, False
            st.session_state.fase_progreso = 1
            st.rerun()
            
    if st.session_state.bancos_cargados:
        df_b, df_a = st.session_state.df_banco, st.session_state.df_auxiliar
        c1, c2, c3, c4 = st.columns(4)
        with c1: cb_m = st.selectbox("Monto BANCO:", df_b.columns, key="cb_m")
        with c2: cb_f = st.selectbox("Fecha BANCO:", df_b.columns, key="cb_f")
        with c3: ca_m = st.selectbox("Monto AUXILIAR:", df_a.columns, key="ca_m")
        with c4: ca_f = st.selectbox("Fecha AUXILIAR:", df_a.columns, key="ca_f")
        
        # Panel de Pre-Validación de Estructuras
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
            df_b_c = df_b.dropna(subset=[cb_m, cb_f]).copy()
            df_a_c = df_a.dropna(subset=[ca_m, ca_f]).copy()
            df_b_c['Monto_Limpio'] = pd.to_numeric(df_b_c[cb_m], errors='coerce').fillna(0).abs()
            df_a_c['Monto_Limpio'] = pd.to_numeric(df_a_c[ca_m], errors='coerce').fillna(0).abs()
            df_b_c['Fecha_Limpia'] = pd.to_datetime(df_b_c[cb_f], format='mixed', dayfirst=True).dt.date
            df_a_c['Fecha_Limpia'] = pd.to_datetime(df_a_c[ca_f], format='mixed', dayfirst=True).dt.date
            
            df_b_s, df_a_s = df_b_c.sort_values('Monto_Limpio').reset_index(drop=True), df_a_c.sort_values('Monto_Limpio').reset_index(drop=True)
            df_m = pd.merge_asof(df_b_s, df_a_s, on='Monto_Limpio', tolerance=st.session_state.tolerancia, direction='nearest', suffixes=('_Banco', '_Auxiliar')).dropna(subset=[ca_m])
            
            st.session_state.df_conciliados = df_m[df_m['Fecha_Limpia_Banco'] == df_m['Fecha_Limpia_Auxiliar']]
            st.session_state.bancos_pendientes = df_b_c[~df_b_c['Monto_Limpio'].isin(st.session_state.df_conciliados['Monto_Limpio'])].drop(columns=['Monto_Limpio', 'Fecha_Limpia'], errors='ignore')
            st.session_state.auxiliar_pendientes = df_a_c[~df_a_c['Monto_Limpio'].isin(st.session_state.df_conciliados['Monto_Limpio'])].drop(columns=['Monto_Limpio', 'Fecha_Limpia'], errors='ignore')
            
            st.session_state.suma_conciliado = st.session_state.df_conciliados[cb_m].astype(float).abs().sum()
            st.session_state.suma_banco_p = st.session_state.bancos_pendientes[cb_m].astype(float).abs().sum()
            st.session_state.suma_aux_p = st.session_state.auxiliar_pendientes[ca_m].astype(float).abs().sum()
            st.session_state.bancos_ejecutado = True
            st.session_state.fase_progreso = 4
            st.rerun()

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

# ==============================================================================
# 9. DESPLIEGUE: PESTAÑA MÓDULO 2 - XML VS CONTABILIDAD
# ==============================================================================
with tab_xml:
    st.write("")
    st.markdown('<div class="section-header">📄 Auditoría Fiscal: Comprobantes XML vs Auxiliar de Contabilidad</div>', unsafe_allow_html=True)
    if not st.session_state.xml_cargados:
        cx_1, cx_2 = st.columns(2)
        with cx_1: x_file = st.file_uploader("Sube Reporte de Facturas", type=["csv", "xlsx"], key="x_u")
        with cx_2: cg_file = st.file_uploader("Sube Auxiliar de Gastos", type=["csv", "xlsx"], key="cg_u")
        if x_file and cg_file:
            st.session_state.df_xml_gastos = leer_archivo_contable(x_file)
            st.session_state.df_aux_gastos = leer_archivo_contable(cg_file)
            st.session_state.xml_cargados = True
            st.rerun()
    else:
        st.success("🏁 Papeles fiscales indexados.")
        if st.button("🔄 Cargar nuevos XML", key="reset_x"):
            st.session_state.xml_cargados, st.session_state.xml_ejecutado = False, False
            st.rerun()

    if st.session_state.xml_cargados:
        df_x, df_g = st.session_state.df_xml_gastos, st.session_state.df_aux_gastos
        cx1, cx2 = st.columns(2)
        with cx1: xml_m = st.selectbox("Monto XML:", df_x.columns, key="xml_m")
        with cx2: cont_m = st.selectbox("Monto Auxiliar Gasto:", df_g.columns, key="cont_m")
        
        if st.button("🚀 Cruce XML vs Contabilidad", type="primary", use_container_width=True):
            df_x['Monto_Limpio'] = pd.to_numeric(df_x[xml_m], errors='coerce').fillna(0).abs()
            df_g['Monto_Limpio'] = pd.to_numeric(df_g[cont_m], errors='coerce').fillna(0).abs()
            st.session_state.xml_conciliados = pd.merge(df_x, df_g, on='Monto_Limpio', how='inner')
            st.session_state.xml_ejecutado = True
            st.rerun()
            
        if st.session_state.xml_ejecutado: st.dataframe(st.session_state.xml_conciliados, use_container_width=True)
# ==============================================================================
# 10. DESPLIEGUE: PESTAÑA MÓDULO 3 - CLIENTES Y PROVEEDORES
# ==============================================================================
with tab_saldos:
    st.write("")
    st.markdown('<div class="section-header">🧾 Herramienta de Auditoría de Cartera: Clientes y Proveedores</div>', unsafe_allow_html=True)
    if not st.session_state.saldos_cargados:
        cs_1, cs_2 = st.columns(2)
        with cs_1: sg_file = st.file_uploader("Sube Reporte de Saldos Globales (ERP)", type=["csv", "xlsx"], key="sg_u_new")
        with cs_2: fd_file = st.file_uploader("Sube Desglose de Facturas / Antigüedad", type=["csv", "xlsx"], key="fd_u_new")
        if sg_file and fd_file:
            st.session_state.df_saldos_globales = leer_archivo_contable(sg_file)
            st.session_state.df_facturas_detalle = leer_archivo_contable(fd_file)
            st.session_state.saldos_cargados = True
            st.rerun()
    else:
        st.success("🏁 Libros de cuentas corporativas cargados.")
        if st.button("🔄 Reestablecer Carteras", key="reset_s_new"):
            st.session_state.saldos_cargados, st.session_state.saldos_ejecutado = False, False
            st.rerun()

    if st.session_state.saldos_cargados:
        df_sg, df_fd = st.session_state.df_saldos_globales, st.session_state.df_facturas_detalle
        col_s1, col_s2, col_s3 = st.columns(3)
        with col_s1: id_cte = st.selectbox("Columna Identificador (Código/RFC):", df_sg.columns, key="id_cte_new")
        with col_s2: sg_m = st.selectbox("Monto Saldo Global Contable:", df_sg.columns, key="sg_m_new")
        with col_s3: fd_m = st.selectbox("Monto Factura en Desglose:", df_fd.columns, key="fd_m_new")
        
        if st.button("🚀 Ejecutar Cruce de Antigüedad de Saldos", type="primary", use_container_width=True):
            df_fd_grouped = df_fd.groupby(id_cte)[fd_m].sum().reset_index()
            df_fd_grouped.columns = [id_cte, 'Suma_Detalle_Facturas']
            df_cruce = pd.merge(df_sg, df_fd_grouped, on=id_cte, how='outer')
            df_cruce['Saldo_Global_Num'] = pd.to_numeric(df_cruce[sg_m], errors='coerce').fillna(0)
            df_cruce['Suma_Detalle_Num'] = pd.to_numeric(df_cruce['Suma_Detalle_Facturas'], errors='coerce').fillna(0)
            df_cruce['Diferencia_Calculada'] = (df_cruce['Saldo_Global_Num'] - df_cruce['Suma_Detalle_Num']).round(2)
            
            st.session_state.saldos_conciliados = df_cruce[df_cruce['Diferencia_Calculada'].abs() <= st.session_state.tolerancia]
            st.session_state.saldos_discrepancias = df_cruce[df_cruce['Diferencia_Calculada'].abs() > st.session_state.tolerancia]
            st.session_state.saldos_ejecutado = True
            st.rerun()
            
        if st.session_state.saldos_ejecutado:
            t_s1, t_s2 = st.tabs(["✅ Saldos Correctos", "⚠️ Discrepancias Encontradas"])
            with t_s1: st.dataframe(st.session_state.saldos_conciliados, use_container_width=True)
            with t_s2: st.dataframe(st.session_state.saldos_discrepancias, use_container_width=True)

# ==============================================================================
# 11. DESPLIEGUE: PESTAÑA MÓDULO 4 - MULTIDIVISA USD
# ==============================================================================
with tab_multidivisa:
    st.write("")
    st.markdown('<div class="section-header">🌐 Herramienta Cambiaria: Conciliación de Cuentas en Dólares (USD)</div>', unsafe_allow_html=True)
    st.session_state.tc_auditoria_val = st.number_input("Tipo de Cambio (TC) de Cierre Mensual:", min_value=1.0000, value=float(st.session_state.tc_auditoria_val), step=0.0100, key="tc_num_input")
    
    if not st.session_state.divisa_cargados:
        cv_1, cv_2 = st.columns(2)
        with cv_1: de_file = st.file_uploader("Sube Estado de Cuenta Extranjero (USD)", type=["csv", "xlsx"], key="de_u_new")
        with cv_2: dn_file = st.file_uploader("Sube Registro en Moneda Nacional (Pólizas)", type=["csv", "xlsx"], key="dn_u_new")
        if de_file and dn_file:
            st.session_state.df_divisa_ext = leer_archivo_contable(de_file)
            st.session_state.df_divisa_nac = leer_archivo_contable(dn_file)
            st.session_state.divisa_cargados = True
            st.rerun()
    else:
        st.success("🏁 Papeles de divisas extranjeras indexados.")
        if st.button("🔄 Reestablecer Módulo Multidivisa", key="reset_v_new"):
            st.session_state.divisa_cargados, st.session_state.divisa_ejecutado = False, False
            st.rerun()

    if st.session_state.divisa_cargados:
        df_ext, df_nac = st.session_state.df_divisa_ext, st.session_state.df_divisa_nac
        col_v1, col_v2 = st.columns(2)
        with col_v1: de_m = st.selectbox("Monto en Dólares (USD):", df_ext.columns, key="de_m_new")
        with col_v2: dn_m = st.selectbox("Monto en Moneda Nacional (MXN):", df_nac.columns, key="dn_m_new")
        
        if st.button("🚀 Calcular Fluctuación Cambiaria Analítica", type="primary", use_container_width=True):
            df_ext['Monto_Limpio'] = pd.to_numeric(df_ext[de_m], errors='coerce').fillna(0).abs()
            df_nac['Monto_Limpio'] = pd.to_numeric(df_nac[dn_m], errors='coerce').fillna(0).abs()
            df_ext_s, df_nac_s = df_ext.sort_values('Monto_Limpio').reset_index(drop=True), df_nac.sort_values('Monto_Limpio').reset_index(drop=True)
            df_v_m = pd.merge_asof(df_ext_s, df_nac_s, on='Monto_Limpio', direction='nearest', suffixes=('_USD', '_Local'))
            df_v_m['Valor_Contable_Esperado'] = (df_v_m['Monto_Limpio'] * st.session_state.tc_auditoria_val).round(2)
            df_v_m['Monto_Local_Real'] = pd.to_numeric(df_v_m[dn_m], errors='coerce').fillna(0).abs()
            df_v_m['Diferencia_Fluctuacion'] = (df_v_m['Valor_Contable_Esperado'] - df_v_m['Monto_Local_Real']).round(2)
            st.session_state.divisa_conciliados = df_v_m
            st.session_state.divisa_ejecutado = True
            st.rerun()
            
        if st.session_state.divisa_ejecutado: st.dataframe(st.session_state.divisa_conciliados, use_container_width=True)

# ==============================================================================
# 12. DESPLIEGUE: PESTAÑA MANUAL DE AYUDA Y GUÍA TÉCNICA
# ==============================================================================
with tab_ayuda:
    st.write("")
    st.markdown('<div class="section-header">❓ Centro de Ayuda y Documentación Técnica</div>', unsafe_allow_html=True)
    st.markdown('<div class="help-card"><div class="help-title">📊 1. Dashboard General</div>Diagnóstico ejecutivo con semáforo y dictamen en PDF.</div>', unsafe_allow_html=True)
    st.markdown('<div class="help-card"><div class="help-title">🏦 2. Módulo Bancario</div>Cruce exacto por Monto y Fecha (Banco vs Auxiliar).</div>', unsafe_allow_html=True)
    st.markdown('<div class="help-card"><div class="help-title">📄 3. XML vs Contabilidad</div>Alineación fiscal de comprobantes de egresos/gastos.</div>', unsafe_allow_html=True)
    st.markdown('<div class="help-card"><div class="help-title">🧾 4. Clientes y Proveedores</div>Validación global de balanzas contra desgloses.</div>', unsafe_allow_html=True)
    st.markdown('<div class="help-card"><div class="help-title">🌐 5. Multidivisa USD</div>Análisis cambiario y cálculo de utilidad/pérdida.</div>', unsafe_allow_html=True)
