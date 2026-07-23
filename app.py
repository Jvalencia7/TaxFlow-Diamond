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

# Encabezado de la Plataforma
st.markdown('<div class="main-title">💎 TaxFlow-Diamond</div>', unsafe_allow_html=True)
st.markdown('<div class="subtitle">Enterprise Financial & XML Reconciliation Suite (Version 2.0 Corporate)</div>', unsafe_allow_html=True)

# ==============================================================================
# 2. SECCIÓN 1: PANEL DE CONTROL Y METADATOS (BARRA LATERAL)
# ==============================================================================
st.sidebar.markdown("### 🏢 Membrete de Auditoría")
empresa = st.sidebar.text_input("Razón Social del Cliente:", placeholder="Ej. Empresa SA de CV")
periodo = st.sidebar.text_input("Periodo Fiscal:", placeholder="Ej. Enero 2026")
auditor = st.sidebar.text_input("Auditor Encargado:", placeholder="Ej. Lic. Juan Pérez")

st.sidebar.markdown("---")
st.sidebar.markdown("### ⚙️ Parámetros de Precisión")
# Sistema de tolerancia de centavos para mitigar discrepancias por redondeo de impuestos
tolerancia = st.sidebar.slider("Margen de Tolerancia de Centavos:", 0.00, 5.00, 0.50, step=0.10, help="Ignora discrepancias menores causadas por redondeo en decimales.")

# ==============================================================================
# 3. SECCIÓN 2: INGESTA INTEGRAL DE ARCHIVOS FINANCIEROS Y XML
# ==============================================================================
st.markdown('<div class="section-header">📂 Sección I: Ingesta Integral de Datos</div>', unsafe_allow_html=True)

col1, col2 = st.columns(2)

with col1:
    st.subheader("1. Ingesta de Estado de Cuenta")
    banco_file = st.file_uploader("Sube el archivo del Banco (CSV o Excel)", type=["csv", "xlsx"], key="banco_corp")
    
with col2:
    st.subheader("2. Ingesta de Facturas / XML Nativo")
    origen_facturas = st.radio("Selecciona el formato de origen de las facturas:", ["Reporte en Excel / CSV", "Archivo Comprimido (.ZIP) con XMLs del SAT"])
    
    if origen_facturas == "Reporte en Excel / CSV":
        facturas_file = st.file_uploader("Sube el reporte estructurado de Facturas", type=["csv", "xlsx"], key="fact_corp")
        df_facturas = None
    else:
        facturas_file = st.file_uploader("Sube el archivo comprimido con tus XML fiscales", type=["zip"], key="zip_corp")
        df_facturas = None

# Funciones de extracción e ingeniería de datos en memoria
def leer_banco_o_factura(file):
    if file.name.endswith('.csv'):
        return pd.read_csv(file)
    return pd.read_excel(file)

def procesar_zip_xml(zip_file):
    # Lector masivo de carpetas comprimidas con XMLs emitidos o recibidos
    lista_xml = []
    with zipfile.ZipFile(zip_file) as archive:
        for file_name in archive.namelist():
            if file_name.endswith('.xml'):
                try:
                    xml_data = archive.read(file_name)
                    root = ET.fromstring(xml_data)
                    # Eliminación de namespaces para lectura universal del árbol XML
                    for elem in root.iter():
                        if '}' in elem.tag:
                            elem.tag = elem.tag.split('}', 1)
                    
                    # Extracción parametrizada de nodos críticos de control fiscal
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
                    pass # Control de omisión de archivos corruptos internos del ZIP
    return pd.DataFrame(lista_xml)
# ==============================================================================
# 4. SECCIÓN 3: MAPEO DINÁMICO Y PROCESAMIENTO ANALÍTICO
# ==============================================================================
if banco_file and facturas_file:
    try:
        df_banco = leer_banco_o_factura(banco_file)
        
        if origen_facturas == "Reporte en Excel / CSV":
            df_facturas = leer_banco_o_factura(facturas_file)
        else:
            with st.spinner("Decodificando estructura ZIP e indexando XMLs fiscales..."):
                df_facturas = procesar_zip_xml(facturas_file)
        
        if len(df_banco) > 0 and len(df_facturas) > 0:
            st.success(f"🏁 Datos de control indexados con éxito. Banco: {len(df_banco)} filas | Facturas/XML: {len(df_facturas)} registros.")
            
            st.markdown('<div class="section-header">⚙️ Sección II: Mapeo Avanzado de Columnas</div>', unsafe_allow_html=True)
            
            c1, c2 = st.columns(2)
            with c1:
                col_monto_banco = st.selectbox("Columna de importe financiero (BANCO):", df_banco.columns)
            with c2:
                col_monto_factura = st.selectbox("Columna de importe fiscal (FACTURAS/XML):", df_facturas.columns)
                
            if st.button("🚀 Ejecutar Conciliación Avanzada", type="primary", use_container_width=True):
                
                # Normalización de signos monetarios a valores absolutos flotantes
                df_banco['Monto_Limpio'] = df_banco[col_monto_banco].astype(float).abs()
                df_facturas['Monto_Limpio'] = df_facturas[col_monto_factura].astype(float).abs()
                
                # ALGORITMO DE CRUCE CON TOLERANCIA FLEXIBLE DE CENTAVOS
                df_banco_sorted = df_banco.sort_values('Monto_Limpio')
                df_facturas_sorted = df_facturas.sort_values('Monto_Limpio')
                
                df_conciliados = pd.merge_asof(
                    df_banco_sorted,
                    df_facturas_sorted,
                    on='Monto_Limpio',
                    tolerance=tolerancia,
                    direction='nearest',
                    suffixes=('_Banco', '_Factura')
                ).dropna(subset=[col_monto_factura])
                
                # Identificación matemática de registros huérfanos residuales
                bancos_pendientes = df_banco[~df_banco['Monto_Limpio'].isin(df_conciliados['Monto_Limpio'])].drop(columns=['Monto_Limpio'], errors='ignore')
                facturas_pendientes = df_facturas[~df_facturas['Monto_Limplio'].isin(df_conciliados['Monto_Limpio']) if 'Monto_Limplio' in df_conciliados.columns else ~df_facturas['Monto_Limpio'].isin(df_conciliados['Monto_Limpio'])].drop(columns=['Monto_Limpio'], errors='ignore')
                
                df_conciliados = df_conciliados.drop(columns=['Monto_Limpio'], errors='ignore')
                
                # Cálculo de capital financiero para el análisis de riesgo ejecutivo
                suma_conciliado = df_conciliados[col_monto_banco].astype(float).abs().sum()
                suma_banco_p = bancos_pendientes[col_monto_banco].astype(float).abs().sum()
                suma_fact_p = facturas_pendientes[col_monto_factura].astype(float).abs().sum()

                # ==============================================================================
                # 5. SECCIÓN 4: DASHBOARD EJECUTIVO Y REPORTES DE RIESGO
                # ==============================================================================
                st.markdown('<div class="section-header">📊 Sección III: Dashboard de Resultados Corporativos</div>', unsafe_allow_html=True)
                
                if empresa or periodo:
                    st.info(f"📋 **Papel de Trabajo de Auditoría:** {empresa} | **Periodo:** {periodo} | **Auditoría por:** {auditor}")
                
                m1, m2, m3 = st.columns(3)
                m1.metric("Capital Total Conciliado", f"${suma_conciliado:,.2f}", "✓ Amarrado")
                m2.metric("Riesgo Financiero en Banco", f"${suma_banco_p:,.2f}", "⚠️ Sin Factura", delta_color="inverse")
                m3.metric("Riesgo Fiscal en XML", f"${suma_fact_p:,.2f}", "⚠️ Sin Cobrar/Pagar", delta_color="inverse")
                
                # Distribución analítica visual para la toma de decisiones ejecutivas
                st.write("")
                st.subheader("💡 Análisis de Distribución de Riesgo Financiero")
                df_grafico = pd.DataFrame({
                    "Categoría Financiera": ["Capital Conciliado", "Riesgo en Banco (Sin XML)", "Riesgo en Facturas (Sin Flujo)"],
                    "Monto Total ($)": [suma_conciliado, suma_banco_p, suma_fact_p]
                })
                fig = px.pie(df_grafico, values="Monto Total ($)", names="Categoría Financiera", 
                             color_discrete_sequence=["#00D4FF", "#FF4B4B", "#FFA500"], hole=0.4)
                fig.update_layout(template="plotly_dark", paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
                st.plotly_chart(fig, use_container_width=True)

                # ==============================================================================
                # 6. SECCIÓN 5: CENTRO DE DESCARGAS MULTI-PESTAÑA (EXCEL AUDITABLE)
                # ==============================================================================
                st.markdown('<div class="section-header">💾 Sección IV: Centro de Exportación de Datos</div>', unsafe_allow_html=True)
                
                buffer = io.BytesIO()
                with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
                    df_conciliados.to_excel(writer, sheet_name='Conciliados', index=False)
                    bancos_pendientes.to_excel(writer, sheet_name='Pendientes_Banco', index=False)
                    facturas_pendientes.to_excel(writer, sheet_name='Pendientes_XML', index=False)
                
                st.download_button(
                    label="📥 Descargar Reporte Completo en Excel (.XLSX Multi-Pestaña)",
                    data=buffer.getvalue(),
                    file_name=f"Reporte_Conciliacion_{empresa if empresa else 'TaxFlow'}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    use_container_width=True
                )
                
                # Visualización interna mediante segregación en pestañas interactivas
                st.write("")
                st.subheader("🔍 Desglose Técnico de Registros")
                tab1, tab2, tab3 = st.tabs(["✅ Conciliados", "⚠️ Pendientes Banco", "📄 XMLs Huérfanos"])
                with tab1: st.dataframe(df_conciliados, use_container_width=True)
                with tab2: st.dataframe(bancos_pendientes, use_container_width=True)
                with tab3: st.dataframe(facturas_pendientes, use_container_width=True)
                
    except Exception as e:
        st.error(f"Error Estructural: Valida que las columnas seleccionadas correspondan a importes numéricos válidos. Detalle: {e}")
else:
    st.info("💎 Suite Corporativa TaxFlow-Diamond lista para operar. Sube tu Estado de Cuenta y tus Comprobantes Fiscales en la parte superior para desplegar la auditoría analítica.")
