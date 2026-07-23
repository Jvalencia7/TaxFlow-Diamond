import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import zipfile
import xml.etree.ElementTree as ET
import io

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
    </style>
""", unsafe_allow_html=True)

# Encabezado Global de la Plataforma
st.markdown('<div class="main-title">💎 TaxFlow-Diamond</div>', unsafe_allow_html=True)
st.markdown('<div class="subtitle">Enterprise Financial & XML Reconciliation Suite</div>', unsafe_allow_html=True)

# ==============================================================================
# 2. ENTRADAS DE CONTROL CONTABLE (BARRA LATERAL Y NAVEGACIÓN)
# ==============================================================================
st.sidebar.markdown("### 🗺️ Módulos del Sistema")
# Menú de navegación corporativo para cambiar entre herramientas de la Suite
modulo_activo = st.sidebar.radio(
    "Selecciona la herramienta a operar:",
    ["📊 Dashboard General", "🏦 Conciliación Bancaria Avanzada (Monto + Fecha)"]
)

st.sidebar.markdown("---")
st.sidebar.markdown("### 🏢 Membrete de Auditoría")
empresa = st.sidebar.text_input("Razón Social del Cliente:", placeholder="Ej. Empresa SA de CV")
periodo = st.sidebar.text_input("Periodo Fiscal:", placeholder="Ej. Enero 2026")
auditor = st.sidebar.text_input("Auditor Encargado:", placeholder="Ej. Lic. Juan Pérez")

st.sidebar.markdown("---")
st.sidebar.markdown("### ⚙️ Parámetros de Precisión")
tolerancia = st.sidebar.slider("Margen de Tolerancia de Centavos:", 0.00, 5.00, 0.50, step=0.10, help="Ignora discrepancias menores causadas por redondeo en decimales.")

# Funciones globales de extracción e ingeniería de datos en memoria
def leer_banco_o_factura(file):
    if file.name.endswith('.csv'):
        return pd.read_csv(file)
    return pd.read_excel(file)

def procesar_zip_xml(zip_file):
    lista_xml = []
    with zipfile.ZipFile(zip_file) as archive:
        for file_name in archive.namelist():
            if file_name.endswith('.xml'):
                try:
                    xml_data = archive.read(file_name)
                    root = ET.fromstring(xml_data)
                    for elem in root.iter():
                        if '}' in elem.tag:
                            elem.tag = elem.tag.split('}', 1)
                    total = root.get('Total') or root.get('total')
                    fecha = root.get('Fecha') or root.get('fecha')
                    receptor_node = root.find('Receptor')
                    emisor_node = root.find('Emisor')
                    timbre_node = root.find('.//TimbreFiscalDigital')
                    
                    rfc_cliente = receptor_node.get('Rfc') if receptor_node is not None else "N/A"
                    nombre_emisor = emisor_node.get('Nombre') if emisor_node is not None else "N/A"
                    uuid = timbre_node.get('UUID') if timbre_node is not None else "N/A"
                    
                    if total and fecha:
                        lista_xml.append({
                            "UUID_Fiscal": uuid,
                            "Fecha_Factura": fecha[:10],
                            "RFC_Asociado": rfc_cliente,
                            "Emisor": nombre_emisor,
                            "Monto_XML": float(total)
                        })
                except Exception:
                    pass
    return pd.DataFrame(lista_xml)
# ==============================================================================
# 3. MÓDULO A: DASHBOARD GENERAL
# ==============================================================================
if modulo_activo == "📊 Dashboard General":
    st.markdown('<div class="section-header">📊 Resumen General de Operaciones</div>', unsafe_allow_html=True)
    st.info("Bienvenido a TaxFlow-Diamond. Selecciona la pestaña 'Conciliación Bancaria Avanzada' en la barra lateral izquierda para comenzar a cruzar tus estados financieros por Monto y Fecha.")

# ==============================================================================
# 4. MÓDULO B: PÁGINA EXCLUSIVA DE CONCILIACIÓN (MONTO + FECHA)
# ==============================================================================
else:
    st.markdown('<div class="section-header">🏦 Sección Exclusiva: Conciliación Bancaria Cruzada</div>', unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("1. Ingesta de Estado de Cuenta")
        banco_file = st.file_uploader("Sube el archivo del Banco (CSV o Excel)", type=["csv", "xlsx"], key="banco_excl")
    with col2:
        st.subheader("2. Ingesta de Facturas / XML Nativo")
        origen_facturas = st.radio("Selecciona el formato de origen de las facturas:", ["Reporte en Excel / CSV", "Archivo Comprimido (.ZIP) con XMLs del SAT"], key="origen_excl")
        if origen_facturas == "Reporte en Excel / CSV":
            facturas_file = st.file_uploader("Sube el reporte estructurado de Facturas", type=["csv", "xlsx"], key="fact_excl")
        else:
            facturas_file = st.file_uploader("Sube el archivo comprimido con tus XML fiscales", type=["zip"], key="zip_excl")

    if banco_file and facturas_file:
        try:
            df_banco = leer_banco_o_factura(banco_file)
            df_facturas = leer_banco_o_factura(facturas_file) if origen_facturas == "Reporte en Excel / CSV" else procesar_zip_xml(facturas_file)
            
            if len(df_banco) > 0 and len(df_facturas) > 0:
                st.success("🏁 Registros contables e indexación fiscal cargados correctamente.")
                
                st.markdown('<div class="section-header">⚙️ Configuración del Mapeo Bidimensional</div>', unsafe_allow_html=True)
                st.write("Selecciona los cuatro campos críticos para ejecutar la validación cruzada:")
                
                c1, c2, c3, c4 = st.columns(4)
                with c1: col_monto_banco = st.selectbox("Monto en el BANCO:", df_banco.columns)
                with c2: col_fecha_banco = st.selectbox("Fecha en el BANCO:", df_banco.columns)
                with c3: col_monto_factura = st.selectbox("Monto en XML/FACTURAS:", df_facturas.columns)
                with c4: col_fecha_factura = st.selectbox("Fecha en XML/FACTURAS:", df_facturas.columns)
                
                if st.button("🚀 Ejecutar Conciliación Exacta (Monto + Fecha)", type="primary", use_container_width=True):
                    # Ingeniería de variables: Homologación numérica y de fechas
                    df_banco['Monto_Limpio'] = df_banco[col_monto_banco].astype(float).abs()
                    df_facturas['Monto_Limpio'] = df_facturas[col_monto_factura].astype(float).abs()
                    
                    df_banco['Fecha_Limpia'] = pd.to_datetime(df_banco[col_fecha_banco]).dt.date
                    df_facturas['Fecha_Limpia'] = pd.to_datetime(df_facturas[col_fecha_factura]).dt.date
                    
                    # ALGORITMO DE CRUCE POR DOBLE CRITERIO: El registro debe coincidir en Fecha e Importe (con tolerancia)
                    df_banco_sorted = df_banco.sort_values('Monto_Limpio')
                    df_facturas_sorted = df_facturas.sort_values('Monto_Limpio')
                    
                    # Merge por aproximación numérica
                    df_cruce_monto = pd.merge_asof(
                        df_banco_sorted,
                        df_facturas_sorted,
                        on='Monto_Limpio',
                        tolerance=tolerancia,
                        direction='nearest',
                        suffixes=('_Banco', '_Factura')
                    ).dropna(subset=[col_monto_factura])
                    
                    # Filtrado de validación estricta: Mantener solo si las fechas limpias empatan exactamente
                    df_conciliados = df_cruce_monto[df_cruce_monto['Fecha_Limpia._Banco' if 'Fecha_Limpia_Banco' in df_cruce_monto.columns else 'Fecha_Limpia_Banco'] == df_cruce_monto['Fecha_Limpia_Factura']]
                    
                    # Identificación analítica de registros pendientes
                    bancos_pendientes = df_banco[~df_banco['Monto_Limpio'].isin(df_conciliados['Monto_Limpio'])].drop(columns=['Monto_Limpio', 'Fecha_Limpia'], errors='ignore')
                    facturas_pendientes = df_facturas[~df_facturas['Monto_Limpio'].isin(df_conciliados['Monto_Limpio'])].drop(columns=['Monto_Limpio', 'Fecha_Limpia'], errors='ignore')
                    
                    df_conciliados = df_conciliados.drop(columns=['Monto_Limpio', 'Fecha_Limpia_Banco', 'Fecha_Limpia_Factura'], errors='ignore')
                    
                    # Cálculos para Tablero Ejecutivo
                    suma_conciliado = df_conciliados[col_monto_banco].astype(float).abs().sum()
                    suma_banco_p = bancos_pendientes[col_monto_banco].astype(float).abs().sum()
                    suma_fact_p = facturas_pendientes[col_monto_factura].astype(float).abs().sum()
                    
                    # Presentación del Dashboard corporativo de riesgos financieros
                    st.markdown('<div class="section-header">📊 Dashboard de Auditoría Analítica</div>', unsafe_allow_html=True)
                    if empresa: st.info(f"📋 **Papel de Trabajo:** {empresa} | **Periodo:** {periodo} | **Auditor:** {auditor}")
                    
                    m1, m2, m3 = st.columns(3)
                    m1.metric("Capital Conciliado (Monto + Fecha)", f"${suma_conciliado:,.2f}", "✓ Cuadrado")
                    m2.metric("Discrepancia en Banco", f"${suma_banco_p:,.2f}", "⚠️ Sin Factura", delta_color="inverse")
                    m3.metric("Discrepancia en XML", f"${suma_fact_p:,.2f}", "⚠️ Sin Flujo", delta_color="inverse")
                    
                    # Gráfico de pastel corporativo
                    df_grafico = pd.DataFrame({
                        "Categoría": ["Capital Conciliado", "Pendiente Banco", "Pendiente XML"],
                        "Monto ($)": [suma_conciliado, suma_banco_p, suma_fact_p]
                    })
                    fig = px.pie(df_grafico, values="Monto ($)", names="Categoría", color_discrete_sequence=["#00D4FF", "#FF4B4B", "#FFA500"], hole=0.4)
                    fig.update_layout(template="plotly_dark", paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
                    st.plotly_chart(fig, use_container_width=True)
                    
                    # Centro de Exportación Multi-Pestaña a Excel
                    st.markdown('<div class="section-header">💾 Centro de Exportación de Datos</div>', unsafe_allow_html=True)
                    buffer = io.BytesIO()
                    with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
                        df_conciliados.to_excel(writer, sheet_name='Conciliados', index=False)
                        bancos_pendientes.to_excel(writer, sheet_name='Pendientes_Banco', index=False)
                        facturas_pendientes.to_excel(writer, sheet_name='Pendientes_XML', index=False)
                    
                    st.download_button(
                        label="📥 Descargar Reporte Completo en Excel (.XLSX)",
                        data=buffer.getvalue(),
                        file_name=f"Conciliacion_Bidimensional_{empresa if empresa else 'TaxFlow'}.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                        use_container_width=True
                    )
                    
                    # Desglose en tablas interactivas
                    st.write("")
                    tab1, tab2, tab3 = st.tabs(["✅ Conciliados Rigurosos", "⚠️ Pendientes Banco", "📄 XMLs Huérfanos"])
                    with tab1: st.dataframe(df_conciliados, use_container_width=True)
                    with tab2: st.dataframe(bancos_pendientes, use_container_width=True)
                    with tab3: st.dataframe(facturas_pendientes, use_container_width=True)
                    
        except Exception as e:
            st.error(f"Error Estructural: Asegúrate de mapear las columnas correctas de Importe y Fecha. Detalle: {e}")
    else:
        st.info("💎 Módulo exclusivo de Conciliación Bancaria activo. Sube tus registros en la parte superior para mapear Importes y Fechas simultáneamente.")
