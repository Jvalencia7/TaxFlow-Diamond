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
modulo_activo = st.sidebar.radio(
    "Selecciona la herramienta a operar:",
    ["📊 Dashboard General", "🏦 Conciliación Bancaria (Estado de Cuenta vs Auxiliar Contable)"]
)

st.sidebar.markdown("---")
st.sidebar.markdown("### 🏢 Membrete de Auditoría")
empresa = st.sidebar.text_input("Razón Social del Cliente:", placeholder="Ej. Empresa SA de CV")
periodo = st.sidebar.text_input("Periodo Fiscal:", placeholder="Ej. Enero 2026")
auditor = st.sidebar.text_input("Auditor Encargado:", placeholder="Ej. Lic. Juan Pérez")

st.sidebar.markdown("---")
st.sidebar.markdown("### ⚙️ Parámetros de Precisión")
tolerancia = st.sidebar.slider("Margen de Tolerancia de Centavos:", 0.00, 5.00, 0.50, step=0.10, help="Ignora diferencias menores por redondeo decimal.")

# Funciones globales de extracción e ingeniería de datos en memoria
def leer_archivo_contable(file):
    if file.name.endswith('.csv'):
        return pd.read_csv(file)
    return pd.read_excel(file)
# ==============================================================================
# 3. MÓDULO A: DASHBOARD GENERAL
# ==============================================================================
if modulo_activo == "📊 Dashboard General":
    st.markdown('<div class="section-header">📊 Resumen General de Operaciones</div>', unsafe_allow_html=True)
    st.info("Bienvenido a TaxFlow-Diamond. Selecciona la pestaña 'Conciliación Bancaria' en la barra lateral izquierda para comenzar a cruzar tu Estado de Cuenta contra el Auxiliar de Contabilidad.")

# ==============================================================================
# 4. MÓDULO B: PÁGINA EXCLUSIVA DE CONCILIACIÓN (BANCO VS AUXILIAR)
# ==============================================================================
else:
    st.markdown('<div class="section-header">🏦 Conciliación Bancaria: Estado de Cuenta vs Auxiliar Contable</div>', unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("1. Estado de Cuenta Emitido por el Banco")
        banco_file = st.file_uploader("Sube el archivo del Banco (Excel o CSV)", type=["csv", "xlsx"], key="banco_aux")
    with col2:
        st.subheader("2. Auxiliar de Contabilidad de Bancos (ERP/Sistema)")
        auxiliar_file = st.file_uploader("Sube el Auxiliar Contable Interno (Excel o CSV)", type=["csv", "xlsx"], key="aux_cont")

    if banco_file and auxiliar_file:
        try:
            df_banco = leer_archivo_contable(banco_file)
            df_auxiliar = leer_archivo_contable(auxiliar_file)
            
            if len(df_banco) > 0 and len(df_auxiliar) > 0:
                st.success("🏁 Estado de cuenta bancario y Auxiliar contable indexados correctamente.")
                
                st.markdown('<div class="section-header">⚙️ Configuración del Mapeo de Auditoría</div>', unsafe_allow_html=True)
                st.write("Selecciona los campos de importe y fecha para validar de forma cruzada:")
                
                c1, c2, c3, c4 = st.columns(4)
                with c1: col_monto_banco = st.selectbox("Columna de Monto (BANCO):", df_banco.columns)
                with c2: col_fecha_banco = st.selectbox("Columna de Fecha (BANCO):", df_banco.columns)
                with c3: col_monto_auxiliar = st.selectbox("Columna de Monto (AUXILIAR):", df_auxiliar.columns)
                with c4: col_fecha_auxiliar = st.selectbox("Columna de Fecha (AUXILIAR):", df_auxiliar.columns)
                
                if st.button("🚀 Ejecutar Conciliación de Libros Contables", type="primary", use_container_width=True):
                    
                    # Depuración de filas nulas o vacías en columnas clave
                    df_banco = df_banco.dropna(subset=[col_monto_banco, col_fecha_banco])
                    df_auxiliar = df_auxiliar.dropna(subset=[col_monto_auxiliar, col_fecha_auxiliar])
                    
                    # Homologación a valores absolutos (así neutralizamos la inversión de Cargo/Abono)
                    df_banco['Monto_Limpio'] = pd.to_numeric(df_banco[col_monto_banco], errors='coerce').fillna(0).abs()
                    df_auxiliar['Monto_Limpio'] = pd.to_numeric(df_auxiliar[col_monto_auxiliar], errors='coerce').fillna(0).abs()
                    
                    # Eliminar registros en cero
                    df_banco = df_banco[df_banco['Monto_Limpio'] > 0]
                    df_auxiliar = df_auxiliar[df_auxiliar['Monto_Limpio'] > 0]
                    
                    # Conversión homologada de formatos de fecha
                    df_banco['Fecha_Limpia'] = pd.to_datetime(df_banco[col_fecha_banco], format='mixed', dayfirst=True).dt.date
                    df_auxiliar['Fecha_Limpia'] = pd.to_datetime(df_auxiliar[col_fecha_auxiliar], format='mixed', dayfirst=True).dt.date
                    
                    # Reordenamiento secuencial para algoritmo de aproximación
                    df_banco_sorted = df_banco.sort_values('Monto_Limpio').reset_index(drop=True)
                    df_auxiliar_sorted = df_auxiliar.sort_values('Monto_Limpio').reset_index(drop=True)
                    
                    # Ejecución del cruce por proximidad numérica de importe
                    df_cruce_monto = pd.merge_asof(
                        df_banco_sorted,
                        df_auxiliar_sorted,
                        on='Monto_Limpio',
                        tolerance=tolerancia,
                        direction='nearest',
                        suffixes=('_Banco', '_Auxiliar')
                    ).dropna(subset=[col_monto_auxiliar])
                    
                    # Validación contable rigurosa por empate de fecha exacta
                    df_conciliados = df_cruce_monto[df_cruce_monto['Fecha_Limpia_Banco'] == df_cruce_monto['Fecha_Limpia_Auxiliar']]
                    
                    # Detección analítica de partidas pendientes de conciliar
                    bancos_pendientes = df_banco[~df_banco['Monto_Limpio'].isin(df_conciliados['Monto_Limpio'])].drop(columns=['Monto_Limpio', 'Fecha_Limpia'], errors='ignore')
                    auxiliar_pendientes = df_auxiliar[~df_auxiliar['Monto_Limpio'].isin(df_conciliados['Monto_Limpio'])].drop(columns=['Monto_Limpio', 'Fecha_Limpia'], errors='ignore')
                    
                    df_conciliados = df_conciliados.drop(columns=['Monto_Limpio', 'Fecha_Linter_Banco', 'Fecha_Limpia_Banco', 'Fecha_Limpia_Auxiliar'], errors='ignore')
                    
                    # Totales financieros
                    suma_conciliado = df_conciliados[col_monto_banco].astype(float).abs().sum()
                    suma_banco_p = bancos_pendientes[col_monto_banco].astype(float).abs().sum()
                    suma_aux_p = auxiliar_pendientes[col_monto_auxiliar].astype(float).abs().sum()
                    
                    # Despliegue del Dashboard Corporativo de Auditoría
                    st.markdown('<div class="section-header">📊 Resumen Ejecutivo del Papel de Trabajo</div>', unsafe_allow_html=True)
                    if empresa: st.info(f"📋 **Papel de Trabajo Contable:** {empresa} | **Periodo:** {periodo} | **Auditor:** {auditor}")
                    
                    m1, m2, m3 = st.columns(3)
                    m1.metric("Importe Conciliado (Alineado)", f"${suma_conciliado:,.2f}", "✓ Correcto")
                    m2.metric("Pendientes en Banco", f"${suma_banco_p:,.2f}", "⚠️ Mov. No Contabilizados", delta_color="inverse")
                    m3.metric("Pendientes en Auxiliar", f"${suma_aux_p:,.2f}", "⚠️ Tránsitos / No Bancarizados", delta_color="inverse")
                    
                    # Gráfica analítica de distribución de saldos
                    df_grafico = pd.DataFrame({
                        "Concepto": ["Saldos Conciliados", "Partidas Pendientes Banco", "Partidas Pendientes Auxiliar"],
                        "Importe ($)": [suma_conciliado, suma_banco_p, suma_aux_p]
                    })
                    fig = px.pie(df_grafico, values="Importe ($)", names="Concepto", color_discrete_sequence=["#00D4FF", "#FF4B4B", "#FFA500"], hole=0.4)
                    fig.update_layout(template="plotly_dark", paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
                    st.plotly_chart(fig, use_container_width=True)
                    
                    # Centro de Exportación a Libro de Excel Conciliado
                    st.markdown('<div class="section-header">💾 Centro de Exportación de Papeles de Trabajo</div>', unsafe_allow_html=True)
                    buffer = io.BytesIO()
                    with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
                        df_conciliados.to_excel(writer, sheet_name='Partidas_Conciliadas', index=False)
                        bancos_pendientes.to_excel(writer, sheet_name='Pendientes_Solo_Banco', index=False)
                        auxiliar_pendientes.to_excel(writer, sheet_name='Pendientes_Solo_Auxiliar', index=False)
                    
                    st.download_button(
                        label="📥 Descargar Libro de Conciliación Bancaria Completo (.XLSX)",
                        data=buffer.getvalue(),
                        file_name=f"Conciliacion_Bancaria_Libros_{empresa if empresa else 'TaxFlow'}.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                        use_container_width=True
                    )
                    
                    # Desglose de registros técnicos en pestañas
                    st.write("")
                    tab1, tab2, tab3 = st.tabs(["✅ Partidas Conciliadas", "⚠️ Movimientos Solo en Banco", "📖 Movimientos Solo en Auxiliar"])
                    with tab1: st.dataframe(df_conciliados, use_container_width=True)
                    with tab2: st.dataframe(bancos_pendientes, use_container_width=True)
                    with tab3: st.dataframe(auxiliar_pendientes, use_container_width=True)
                    
        except Exception as e:
            st.error(f"Error Estructural: Asegúrate de mapear correctamente las columnas de importe y fecha de tus papeles de trabajo.")
            st.info(f"Detalle técnico de auditoría: {e}")
    else:
        st.info("💎 Módulo de Conciliación Bancaria Formal activo. Por favor, sube el Estado de Cuenta del Banco y tu reporte de Auxiliar Contable Interno para iniciar el cruce de libros.")
