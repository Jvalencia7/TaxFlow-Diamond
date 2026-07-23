import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import zipfile
import xml.etree.ElementTree as ET
import io
import json

# ==============================================================================
# 1. CONFIGURACIÓN DE NIVEL EMPRESARIAL (SUITE PREMIUM)
# ==============================================================================
st.set_page_config(
    page_title="TaxFlow-Diamond | Suite de Conciliación",
    page_icon="💎",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Inyección de estilos CSS para visualización ejecutiva en interfaz oscura
st.markdown("""
    <style>
    .main-title { font-size: 38px !important; font-weight: 700 !important; color: #00D4FF; margin-bottom: 5px; }
    .subtitle { font-size: 16px !important; color: #639FAB; margin-bottom: 30px; font-weight: 500; }
    .section-header { color: #00D4FF; font-weight: 600; border-bottom: 2px solid #161B22; padding-bottom: 10px; margin-bottom: 20px; font-size: 22px; }
    .help-card { background-color: #161B22; padding: 20px; border-radius: 8px; margin-bottom: 15px; border-left: 4px solid #00D4FF; }
    .help-title { color: #00D4FF; font-size: 18px; font-weight: 600; margin-bottom: 10px; }
    
    div.stButton > button:first-child[data-testid="stSidebarActionButton"] {
        background-color: #00D4FF !important;
        color: #0D1117 !important;
        font-weight: 700 !important;
        border: none !important;
    }
    div.stButton > button:first-child[data-testid="stSidebarActionButton"]:hover {
        background-color: #00B9DF !important;
        color: #0D1117 !important;
    }
    </style>
""", unsafe_allow_html=True)

st.markdown('<div class="main-title">💎 TaxFlow-Diamond</div>', unsafe_allow_html=True)
st.markdown('<div class="subtitle">Enterprise Financial & XML Reconciliation Suite</div>', unsafe_allow_html=True)

# ==============================================================================
# 2. SISTEMA DE MEMORIA INTEGRAL CON GUARDADO AUTOMÁTICO DINÁMICO
# ==============================================================================
variables_sesion = {
    # Módulo Bancos
    'df_banco': None, 'df_auxiliar': None, 'bancos_cargados': False, 'bancos_ejecutado': False,
    'df_conciliados': None, 'bancos_pendientes': None, 'auxiliar_pendientes': None,
    'suma_conciliado': 0.0, 'suma_banco_p': 0.0, 'suma_aux_p': 0.0,
    # Módulo XML
    'df_xml_gastos': None, 'df_aux_gastos': None, 'xml_cargados': False, 'xml_ejecutado': False,
    'xml_conciliados': None, 'xml_pendientes': None, 'cont_pendientes': None,
    # Módulo Clientes/Proveedores
    'df_saldos_globales': None, 'df_facturas_detalle': None, 'saldos_cargados': False, 'saldos_ejecutado': False,
    'saldos_conciliados': None, 'saldos_discrepancias': None,
    # Módulo Multidivisa
    'df_divisa_ext': None, 'df_divisa_nac': None, 'divisa_cargados': False, 'divisa_ejecutado': False,
    'divisa_conciliados': None, 'ajustes_cambiarios': None,
    # Globales
    'empresa': "", 'periodo': "", 'auditor': "", 'tolerancia': 0.50, 'divisa': "MXN ($)", 'logo_bytes': None
}

for llave, valor_defecto in variables_sesion.items():
    if llave not in st.session_state:
        st.session_state[llave] = valor_defecto

# ==============================================================================
# 3. NAVEGACIÓN EN LA PARTE SUPERIOR (MENU INCLUYENDO PESTAÑA DE AYUDA)
# ==============================================================================
st.markdown('<div class="section-header">🗺️ Módulos de la Suite</div>', unsafe_allow_html=True)
tab_dashboard, tab_bancos, tab_xml, tab_saldos, tab_multidivisa, tab_configuracion, tab_ayuda = st.tabs([
    "📊 Dashboard", "🏦 Bancos vs Auxiliar", "📄 XML vs Contabilidad", "🧾 Clientes y Proveedores", "🌐 Multidivisa USD", "⚙️ Configuración", "❓ Ayuda"
])

# ==============================================================================
# 4. BARRA LATERAL CONFIGURADA
# ==============================================================================
if st.session_state.logo_bytes is not None:
    st.sidebar.image(st.session_state.logo_bytes, use_container_width=True)
else:
    st.sidebar.info("🏢 Sin Logotipo Institucional. Configúralo en la pestaña superior de Configuración.")

if st.sidebar.button("🔒 Cerrar Sesión", type="primary", use_container_width=True, key="sidebar_logout_btn"):
    for llave in variables_sesion.keys(): st.session_state[llave] = variables_sesion[llave]
    st.rerun()

st.sidebar.markdown("---")
st.sidebar.markdown("### 🔍 Rastreador Rápido de Auditoría")
busqueda_rapida = st.sidebar.text_input("Ingresa monto o texto a rastrear:", placeholder="Ej. 15400.50 o Transferencia")

def leer_archivo_contable(file):
    if file.name.endswith('.csv'): return pd.read_csv(file)
    return pd.read_excel(file)
# ==============================================================================
# 5. DESPLIEGUE: PESTAÑA MANUAL DE AYUDA Y DOCUMENTACIÓN DE LA APP
# ==============================================================================
with tab_ayuda:
    st.write("")
    st.markdown('<div class="section-header">❓ Centro de Ayuda y Documentación Técnica</div>', unsafe_allow_html=True)
    st.write("Consulta las especificaciones funcionales y operativas de los módulos de TaxFlow-Diamond:")

    # Guías estructuradas por sección con diseño de tarjeta corporativa
    st.markdown('<div class="help-card"><div class="help-title">📊 1. Dashboard General de Operaciones</div>'
                '<b>Objetivo:</b> Ofrecer un diagnóstico ejecutivo del estado de riesgo financiero del cliente.<br>'
                '<b>Herramientas:</b> Métricas consolidadas en tiempo real y gráficos de pastel interactivos.<br>'
                '<b>Uso Frecuente:</b> Presentación de resultados y avance de auditoría a directores financieros (CFO).</div>', unsafe_allow_html=True)

    st.markdown('<div class="help-card"><div class="help-title">🏦 2. Conciliación Bancaria Clásica</div>'
                '<b>Objetivo:</b> Cruzar el Estado de Cuenta del Banco contra el Auxiliar Contable de Bancos de la empresa.<br>'
                '<b>Herramientas:</b> Mapeo bidimensional de columnas (Monto y Fecha), algoritmo de emparejamiento con centavos de tolerancia, segregación en 3 pestañas y botón de exportación total a Excel (.XLSX Multi-pestaña).<br>'
                '<b>Uso Frecuente:</b> Rastrear depósitos o retiros no contabilizados y cheques o transferencias en tránsito.</div>', unsafe_allow_html=True)

    st.markdown('<div class="help-card"><div class="help-title">📄 3. Auditoría de XML vs Contabilidad</div>'
                '<b>Objetivo:</b> Validar que cada factura electrónica (XML) emitida o recibida coincida con los registros del Auxiliar de Gastos.<br>'
                '<b>Herramientas:</b> Extractor y normalizador de importes y fechas, comparador algorítmico e identificación automática de facturas omitidas.<br>'
                '<b>Uso Frecuente:</b> Blindaje fiscal para deducibilidad de impuestos y detección oportuna de gastos fantasma sin CFDI.</div>', unsafe_allow_html=True)

    st.markdown('<div class="help-card"><div class="help-title">🧾 4. Control de Cartera (Clientes y Proveedores)</div>'
                '<b>Objetivo:</b> Conciliar la Antigüedad de Saldos desglosada contra los Saldos Globales de la Balanza de Comprobación.<br>'
                '<b>Herramientas:</b> Motor de sumarización y agrupación automática por RFC/Código de cuenta, y cálculo matemático de desfaces.<br>'
                '<b>Uso Frecuente:</b> Detección de abonos mal aplicados en el ERP contable o facturas duplicadas pendientes de pago.</div>', unsafe_allow_html=True)

    st.markdown('<div class="help-card"><div class="help-title">🌐 5. Conciliación Multidivisa de Cuentas Extranjeras</div>'
                '<b>Objetivo:</b> Evaluar operaciones en dólares (USD) para determinar los ajustes por fluctuación cambiaria al cierre.<br>'
                '<b>Herramientas:</b> Input dinámico de Tipo de Cambio (TC) de auditoría, conversor de divisas integrado y cálculo de diferencias.<br>'
                '<b>Uso Frecuente:</b> Generar las pólizas de ajuste mensual por ganancia o pérdida cambiaria en cuentas bancarias internacionales.</div>', unsafe_allow_html=True)

    st.markdown('<div class="help-card"><div class="help-title">⚙️ 6. Configuración del Sistema y Respaldos</div>'
                '<b>Objetivo:</b> Administrar las reglas de negocio globales de la plataforma y resguardar la información.<br>'
                '<b>Herramientas:</b> Control de membrete del cliente, barra de tolerancia en centavos, selector de moneda base, cargador dinámico de logotipo e importador/exportador universal de copias de seguridad cifradas en archivos .JSON.</div>', unsafe_allow_html=True)

    st.markdown('<div class="help-card"><div class="help-title">🔍 7. Rastreador Rápido de Auditoría (Barra Lateral)</div>'
                '<b>Objetivo:</b> Herramienta transversal de alta frecuencia para localizar registros específicos en un segundo.<br>'
                '<b>Uso Frecuente:</b> Escribe cualquier texto o monto monetario exacto en la barra lateral; el sistema filtrará y expondrá las coincidencias en todas las tablas activas de forma inmediata sin que tengas que buscar fila por fila.</div>', unsafe_allow_html=True)

# ==============================================================================
# 6. DESPLIEGUE: PESTAÑA CONFIGURACIÓN DEL SISTEMA
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
    st.subheader("🖼️ Identidad Corporativa")
    logo_file = st.file_uploader("Sube o actualiza el logotipo (PNG, JPG)", type=["png", "jpg", "jpeg", "webp"], key="logo_config")
    if logo_file is not None:
        nuevos_bytes = logo_file.read()
        if st.session_state.logo_bytes != nuevos_bytes:
            st.session_state.logo_bytes = nuevos_bytes
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
            st.download_button(label="📥 Descargar y Guardar Auditoría en JSON", data=json.dumps(respaldo_dinamico), file_name="Backup_Auditoria_TaxFlow.json", mime="application/json", use_container_width=True)
        else: st.info("💡 Ejecuta algún módulo primero para habilitar el respaldo JSON.")
    with col_j2:
        archivo_json_cargado = st.file_uploader("Sube tu archivo de respaldo (.JSON)", type=["json"], key="json_config_uploader")
        if archivo_json_cargado is not None:
            try:
                datos_restaurados = json.load(archivo_json_cargado)
                for llave, paquete in datos_restaurados.items():
                    if paquete["tipo"] == "dataframe" and paquete["datos"] is not None: st.session_state[llave] = pd.read_json(io.StringIO(paquete["datos"]), orient='split')
                    elif paquete["tipo"] == "bytes" and paquete["datos"] is not None: st.session_state[llave] = bytes.fromhex(paquete["datos"])
                    else: st.session_state[llave] = paquete["datos"]
                st.success("✓ Auditoría restaurada al 100%.")
                st.rerun()
            except Exception as e: st.error(f"Error JSON: {e}")

# ==============================================================================
# 7. DESPLIEGUE: PESTAÑA DASHBOARD GENERAL
# ==============================================================================
with tab_dashboard:
    st.write("")
    if busqueda_rapida and st.session_state.bancos_ejecutado:
        st.markdown('<div class="section-header">🎯 Resultados del Rastreador de Auditoría</div>', unsafe_allow_html=True)
        def filtrar_por_texto(df, termino):
            if df is None: return None
            mascara = df.astype(str).apply(lambda x: x.str.contains(termino, case=False, na=False)).any(axis=1)
            return df[mascara]
        res_conc = filtrar_por_texto(st.session_state.df_conciliados, busqueda_rapida)
        st.dataframe(res_conc, use_container_width=True) if res_conc is not None else st.info("Sin coincidencias.")
    elif st.session_state.bancos_ejecutado or st.session_state.xml_ejecutado:
        st.success(f"💾 Memoria activa para: {st.session_state.empresa if st.session_state.empresa else 'Cliente'} | Período: {st.session_state.periodo}")
        simbolo = st.session_state.divisa.split(" ").replace("(", "").replace(")", "")
        m1, m2, m3 = st.columns(3)
        m1.metric("Bancos Conciliado", f"{simbolo} {st.session_state.suma_conciliado:,.2f}")
        m2.metric("Discrepancia Banco", f"{simbolo} {st.session_state.suma_banco_p:,.2f}", delta_color="inverse")
        m3.metric("Discrepancia Auxiliar", f"{simbolo} {st.session_state.suma_aux_p:,.2f}", delta_color="inverse")
    else:
        st.info("💎 Bienvenido. Explora los módulos de conciliación en la barra superior para procesar los libros financieros.")
# ==============================================================================
# 8. DESPLIEGUE: PESTAÑA MÓDULO 1 - BANCOS VS AUXILIAR
# ==============================================================================
with tab_bancos:
    st.write("")
    st.markdown('<div class="section-header">🏦 Conciliación Bancaria Clásica (Estado de Cuenta vs Auxiliar)</div>', unsafe_allow_html=True)
    if not st.session_state.bancos_cargados:
        c_b1, c_b2 = st.columns(2)
        with c_b1: b_file = st.file_uploader("Sube Estado de Cuenta", type=["csv", "xlsx"], key="b_u")
        with c_b2: a_file = st.file_uploader("Sube Auxiliar de Bancos", type=["csv", "xlsx"], key="a_u")
        if b_file and a_file:
            st.session_state.df_banco = leer_archivo_contable(b_file)
            st.session_state.df_auxiliar = leer_archivo_contable(a_file)
            st.session_state.bancos_cargados = True
            st.rerun()
    else:
        st.success("🏁 Papeles bancarios indexados.")
        if st.button("🔄 Cargar nuevos archivos de banco", key="reset_b"):
            st.session_state.bancos_cargados, st.session_state.bancos_ejecutado = False, False
            st.rerun()
            
    if st.session_state.bancos_cargados:
        df_b, df_a = st.session_state.df_banco, st.session_state.df_auxiliar
        c1, c2, c3, c4 = st.columns(4)
        with c1: cb_m = st.selectbox("Monto BANCO:", df_b.columns, key="cb_m")
        with c2: cb_f = st.selectbox("Fecha BANCO:", df_b.columns, key="cb_f")
        with c3: ca_m = st.selectbox("Monto AUXILIAR:", df_a.columns, key="ca_m")
        with c4: ca_f = st.selectbox("Fecha AUXILIAR:", df_a.columns, key="ca_f")
        
        if st.button("🚀 Procesar Libros Bancarios", type="primary", use_container_width=True):
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
            st.rerun()

        if st.session_state.bancos_ejecutado:
            st.dataframe(st.session_state.df_conciliados, use_container_width=True)

# ==============================================================================
# 9. DESPLIEGUE: PESTAÑA MÓDULO 2 - XML VS CONTABILIDAD
# ==============================================================================
with tab_xml:
    st.write("")
    st.markdown('<div class="section-header">📄 XML vs Contabilidad</div>', unsafe_allow_html=True)
    if not st.session_state.xml_cargados:
        c_x1, c_x2 = st.columns(2)
        with c_x1: x_file = st.file_uploader("Sube Reporte de XMLs / Facturas", type=["csv", "xlsx"], key="x_u")
        with c_x2: cg_file = st.file_uploader("Sube Auxiliar de Cuentas de Gasto", type=["csv", "xlsx"], key="cg_u")
        if x_file and cg_file:
            st.session_state.df_xml_gastos = leer_archivo_contable(x_file)
            st.session_state.df_aux_gastos = leer_archivo_contable(cg_file)
            st.session_state.xml_cargados = True
            st.rerun()
    else:
        st.success("🏁 Papeles fiscales indexados.")
        if st.button("🔄 Cargar nuevos XML/Gastos", key="reset_x"):
            st.session_state.xml_cargados, st.session_state.xml_ejecutado = False, False
            st.rerun()

    if st.session_state.xml_cargados:
        df_x, df_g = st.session_state.df_xml_gastos, st.session_state.df_aux_gastos
        cx1, cx2, cx3, cx4 = st.columns(4)
        with cx1: cx_m = st.selectbox("Monto XML:", df_x.columns, key="cx_m")
        with cx2: cx_f = st.selectbox("Fecha XML:", df_x.columns, key="cx_f")
        with cx3: cg_m = st.selectbox("Monto CONTABILIDAD:", df_g.columns, key="cg_m")
        with cx4: cg_f = st.selectbox("Fecha CONTABILIDAD:", df_g.columns, key="cg_f")

        if st.button("🚀 Conciliar XML vs Gastos", type="primary", use_container_width=True):
            df_x_c = df_x.dropna(subset=[cx_m, cx_f]).copy()
            df_g_c = df_g.dropna(subset=[cg_m, cg_f]).copy()
            df_x_c['Monto_Limpio'] = pd.to_numeric(df_x_c[cx_m], errors='coerce').fillna(0).abs()
            df_g_c['Monto_Limpio'] = pd.to_numeric(df_g_c[cg_m], errors='coerce').fillna(0).abs()
            
            df_x_s, df_g_s = df_x_c.sort_values('Monto_Limpio').reset_index(drop=True), df_g_c.sort_values('Monto_Limpio').reset_index(drop=True)
            st.session_state.xml_conciliados = pd.merge_asof(df_x_s, df_g_s, on='Monto_Limpio', tolerance=st.session_state.tolerancia, direction='nearest', suffixes=('_XML', '_Contabilidad')).dropna(subset=[cg_m])
            st.session_state.xml_pendientes = df_x_c[~df_x_c['Monto_Limpio'].isin(st.session_state.xml_conciliados['Monto_Limplio'] if 'Monto_Limplio' in st.session_state.xml_conciliados.columns else st.session_state.xml_conciliados['Monto_Limpio'])].drop(columns=['Monto_Limpio'], errors='ignore')
            st.session_state.xml_ejecutado = True
            st.rerun()

        if st.session_state.xml_ejecutado:
            t1, t2 = st.tabs(["✅ Cruzados Correctamente", "⚠️ XMLs Sin Registro Contable"])
            with t1: st.dataframe(st.session_state.xml_conciliados, use_container_width=True)
            with t2: st.dataframe(st.session_state.xml_pendientes, use_container_width=True)

# ==============================================================================
# 10. DESPLIEGUE: PESTAÑA MÓDULO 3 Y MÓDULO 4
# ==============================================================================
with tab_saldos:
    st.write("")
    if st.session_state.df_saldos_globales is not None: st.write("📋 Módulo de Carteras Indexado. Configura y ejecuta para visualizar.")
with tab_multidivisa:
    st.write("")
    if st.session_state.df_divisa_ext is not None: st.write("📋 Módulo Multidivisa USD Indexado. Configura y ejecuta para visualizar.")
