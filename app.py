import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
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
    </style>
""", unsafe_allow_html=True)

# Encabezado Global de la Plataforma
st.markdown('<div class="main-title">💎 TaxFlow-Diamond</div>', unsafe_allow_html=True)
st.markdown('<div class="subtitle">Enterprise Financial & XML Reconciliation Suite</div>', unsafe_allow_html=True)

# ==============================================================================
# 2. SISTEMA DE MEMORIA DINÁMICA AUTOSUSTENTABLE (SESSION STATE)
# ==============================================================================
# Diccionario maestro de inicialización contable
variables_sesion = {
    'df_banco': None, 'df_auxiliar': None, 'archivos_cargados': False,
    'df_conciliados': None, 'bancos_pendientes': None, 'auxiliar_pendientes': None,
    'suma_conciliado': 0.0, 'suma_banco_p': 0.0, 'suma_aux_p': 0.0, 'ejecutado': False,
    'empresa': "", 'periodo': "", 'auditor': ""
}

for llave, valor_defecto in variables_sesion.items():
    if llave not in st.session_state:
        st.session_state[llave] = valor_defecto

# ==============================================================================
# 3. PANEL DE CONTROL (BARRA LATERAL) Y ENTRADAS DE AUDITORÍA
# ==============================================================================
st.sidebar.markdown("### 🗺️ Módulos del Sistema")
modulo_activo = st.sidebar.radio(
    "Selecciona la herramienta a operar:",
    ["📊 Dashboard General", "🏦 Conciliación Bancaria (Estado de Cuenta vs Auxiliar Contable)"]
)

st.sidebar.markdown("---")
st.sidebar.markdown("### 🏢 Membrete de Auditoría")
st.session_state.empresa = st.sidebar.text_input("Razón Social del Cliente:", value=st.session_state.empresa, placeholder="Ej. Empresa SA de CV")
st.session_state.periodo = st.sidebar.text_input("Periodo Fiscal:", value=st.session_state.periodo, placeholder="Ej. Enero 2026")
st.session_state.auditor = st.sidebar.text_input("Auditor Encargado:", value=st.session_state.auditor, placeholder="Ej. Lic. Juan Pérez")

st.sidebar.markdown("---")
st.sidebar.markdown("### ⚙️ Parámetros de Precisión")
tolerancia = st.sidebar.slider("Margen de Tolerancia de Centavos:", 0.00, 5.00, 0.50, step=0.10)

# Funciones globales de extracción contable
def leer_archivo_contable(file):
    if file.name.endswith('.csv'): return pd.read_csv(file)
    return pd.read_excel(file)
# ==============================================================================
# 4. MOTOR SERIALIZADOR UNIVERSAL (RESPALDO AUTOMÁTICO DE SECCIONES EN JSON)
# ==============================================================================
st.sidebar.markdown("---")
st.sidebar.markdown("### 💾 Copias de Seguridad (.JSON)")

# ACCIÓN 1: El algoritmo lee dinámicamente CUALQUIER sección nueva agregada a st.session_state
if st.session_state.ejecutado:
    respaldo_dinamico = {}
    for llave, valor in st.session_state.items():
        # Si la sección es una tabla (Dataframe), la convierte a JSON estructurado
        if isinstance(valor, pd.DataFrame):
            respaldo_dinamico[llave] = {"tipo": "dataframe", "datos": valor.to_json(orient='split')}
        # Si la sección es un texto, número o booleano válido, lo empaqueta directo
        elif isinstance(valor, (str, int, float, bool)) or valor is None:
            respaldo_dinamico[llave] = {"tipo": "nativo", "datos": valor}
            
    json_string = json.dumps(respaldo_dinamico)
    
    st.sidebar.download_button(
        label="📥 Guardar Auditoría en JSON",
        data=json_string,
        file_name=f"Backup_Universal_{st.session_state.empresa if st.session_state.empresa else 'TaxFlow'}.json",
        mime="application/json",
        use_container_width=True
    )
else:
    st.sidebar.info("💡 Ejecuta una conciliación primero para habilitar el respaldo dinámico de secciones.")

# ACCIÓN 2: Lector e inyector universal de datos guardados
archivo_json_cargado = st.sidebar.file_uploader("📂 Cargar Auditoría (.JSON)", type=["json"], key="json_uploader")

if archivo_json_cargado is not None:
    try:
        datos_restaurados = json.load(archivo_json_cargado)
        
        # El motor inyecta de vuelta las variables a st.session_state sin importar cuántas secciones existan
        for llave, contenedor in datos_restaurados.items():
            if contenedor["tipo"] == "dataframe" and contenedor["datos"] is not None:
                st.session_state[llave] = pd.read_json(io.StringIO(contenedor["datos"]), orient='split')
            else:
                st.session_state[llave] = contenedor["datos"]
        
        st.session_state.archivos_cargados = True
        st.session_state.ejecutado = True
        st.sidebar.success("✓ Todas las secciones restauradas.")
        st.rerun()
    except Exception as e:
        st.sidebar.error(f"Error de compatibilidad en el respaldo universal: {e}")

# Botón de Cierre de Sesión Completo
st.sidebar.markdown("---")
if st.sidebar.button("🔒 Cerrar Sesión y Limpiar Todo", type="secondary", use_container_width=True):
    for llave in variables_sesion.keys(): st.session_state[llave] = variables_sesion[llave]
    st.rerun()

# ==============================================================================
# 5. MÓDULO A: DASHBOARD GENERAL
# ==============================================================================
if modulo_activo == "📊 Dashboard General":
    st.markdown('<div class="section-header">📊 Resumen General de Operaciones</div>', unsafe_allow_html=True)
    
    if st.session_state.ejecutado:
        st.success(f"💾 Información retenida en memoria activa para: {st.session_state.empresa if st.session_state.empresa else 'Cliente Genérico'}")
        
        m1, m2, m3 = st.columns(3)
        m1.metric("Capital Conciliado", f"${st.session_state.suma_conciliado:,.2f}", "✓ Resguardado")
        m2.metric("Pendientes en Banco", f"${st.session_state.suma_banco_p:,.2f}", "⚠️ Alerta", delta_color="inverse")
        m3.metric("Pendientes en Auxiliar", f"${st.session_state.suma_aux_p:,.2f}", "⚠️ Alerta", delta_color="inverse")
        
        df_grafico = pd.DataFrame({
            "Concepto": ["Saldos Conciliados", "Partidas Pendientes Banco", "Partidas Pendientes Auxiliar"],
            "Importe ($)": [st.session_state.suma_conciliado, st.session_state.suma_banco_p, st.session_state.suma_aux_p]
        })
        fig = px.pie(df_grafico, values="Importe ($)", names="Concepto", color_discrete_sequence=["#00D4FF", "#FF4B4B", "#FFA500"], hole=0.4)
        fig.update_layout(template="plotly_dark", paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Bienvenido a TaxFlow-Diamond. Ve a la pestaña 'Conciliación Bancaria' en la barra lateral para indexar tus papeles de trabajo o arrastra un archivo .JSON de respaldo.")

# ==============================================================================
# 6. MÓDULO B: PÁGINA EXCLUSIVA DE CONCILIACIÓN
# ==============================================================================
else:
    st.markdown('<div class="section-header">🏦 Conciliación Bancaria: Estado de Cuenta vs Auxiliar Contable</div>', unsafe_allow_html=True)
    
    if not st.session_state.archivos_cargados:
        col1, col2 = st.columns(2)
        with col1: banco_file = st.file_uploader("Sube el archivo del Banco (Excel o CSV)", type=["csv", "xlsx"], key="banco_state")
        with col2: auxiliar_file = st.file_uploader("Sube el Auxiliar Contable Interno (Excel o CSV)", type=["csv", "xlsx"], key="aux_state")

        if banco_file and auxiliar_file:
            try:
                st.session_state.df_banco = leer_archivo_contable(banco_file)
                st.session_state.df_auxiliar = leer_archivo_contable(auxiliar_file)
                st.session_state.archivos_cargados = True
                st.rerun()
            except Exception as e: st.error(f"Error Operacional: {e}")
    else:
        st.success("🏁 Tablas financieras indexadas y retenidas en la sesión contable.")
        if st.button("🔄 Cambiar / Subir nuevos archivos contables", type="secondary"):
            st.session_state.archivos_cargados, st.session_state.ejecutado = False, False
            st.rerun()

    if st.session_state.archivos_cargados:
        df_b, df_a = st.session_state.df_banco, st.session_state.df_auxiliar
        st.markdown('<div class="section-header">⚙️ Configuración del Mapeo de Auditoría</div>', unsafe_allow_html=True)
        
        c1, c2, c3, c4 = st.columns(4)
        with c1: col_monto_banco = st.selectbox("Monto en el BANCO:", df_b.columns)
        with c2: col_fecha_banco = st.selectbox("Fecha en el BANCO:", df_b.columns)
        with c3: col_monto_auxiliar = st.selectbox("Monto en el AUXILIAR:", df_a.columns)
        with c4: col_fecha_auxiliar = st.selectbox("Fecha en el AUXILIAR:", df_a.columns)
        
        if st.button("🚀 Ejecutar o Actualizar Conciliación de Libros", type="primary", use_container_width=True):
            try:
                df_b_clean = df_b.dropna(subset=[col_monto_banco, col_fecha_banco]).copy()
                df_a_clean = df_a.dropna(subset=[col_monto_auxiliar, col_fecha_auxiliar]).copy()
                df_b_clean['Monto_Limpio'] = pd.to_numeric(df_b_clean[col_monto_banco], errors='coerce').fillna(0).abs()
                df_a_clean['Monto_Limpio'] = pd.to_numeric(df_a_clean[col_monto_auxiliar], errors='coerce').fillna(0).abs()
                df_b_clean, df_a_clean = df_b_clean[df_b_clean['Monto_Limpio'] > 0], df_a_clean[df_a_clean['Monto_Limpio'] > 0]
                df_b_clean['Fecha_Limpia'] = pd.to_datetime(df_b_clean[col_fecha_banco], format='mixed', dayfirst=True).dt.date
                df_a_clean['Fecha_Limpia'] = pd.to_datetime(df_a_clean[col_fecha_auxiliar], format='mixed', dayfirst=True).dt.date
                
                df_b_sorted, df_a_sorted = df_b_clean.sort_values('Monto_Limpio').reset_index(drop=True), df_a_clean.sort_values('Monto_Limpio').reset_index(drop=True)
                df_cruce_monto = pd.merge_asof(df_b_sorted, df_a_sorted, on='Monto_Limpio', tolerance=tolerancia, direction='nearest', suffixes=('_Banco', '_Auxiliar')).dropna(subset=[col_monto_auxiliar])
                
                st.session_state.df_conciliados = df_cruce_monto[df_cruce_monto['Fecha_Limpia_Banco'] == df_cruce_monto['Fecha_Limpia_Auxiliar']]
                st.session_state.bancos_pendientes = df_b_clean[~df_b_clean['Monto_Limplio' if 'Monto_Limplio' in df_b_clean.columns else 'Monto_Limpio'].isin(st.session_state.df_conciliados['Monto_Limplio'] if 'Monto_Limplio' in st.session_state.df_conciliados.columns else st.session_state.df_conciliados['Monto_Limpio'])].drop(columns=['Monto_Limpio', 'Fecha_Limpia'], errors='ignore')
                st.session_state.auxiliar_pendientes = df_a_clean[~df_a_clean['Monto_Limplio' if 'Monto_Limplio' in df_a_clean.columns else 'Monto_Limpio'].isin(st.session_state.df_conciliados['Monto_Limplio'] if 'Monto_Limplio' in st.session_state.df_conciliados.columns else st.session_state.df_conciliados['Monto_Limpio'])].drop(columns=['Monto_Limpio', 'Fecha_Limpia'], errors='ignore')
                st.session_state.df_conciliados = st.session_state.df_conciliados.drop(columns=['Monto_Limpio', 'Fecha_Limpia_Banco', 'Fecha_Limpia_Auxiliar'], errors='ignore')
                
                st.session_state.suma_conciliado = st.session_state.df_conciliados[col_monto_banco].astype(float).abs().sum()
                st.session_state.suma_banco_p = st.session_state.bancos_pendientes[col_monto_banco].astype(float).abs().sum()
                st.session_state.suma_aux_p = st.session_state.auxiliar_pendientes[col_monto_auxiliar].astype(float).abs().sum()
                st.session_state.ejecutado = True
                st.rerun()
            except Exception as e: st.error(f"Error Estructural en Mapeo: {e}")

        if st.session_state.ejecutado:
            st.markdown('<div class="section-header">📊 Visualización de Datos Resguardados</div>', unsafe_allow_html=True)
            buffer = io.BytesIO()
            with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
                st.session_state.df_conciliados.to_excel(writer, sheet_name='Partidas_Conciliadas', index=False)
st.session_state.bancos_pendientes.to_excel(writer, sheet_name='Pendientes_Solo_Banco', index=False)
st.session_state.auxiliar_pendientes.to_excel(writer, sheet_name='Pendientes_Solo_Auxiliar', index=False)
st.download_button(label="📥 Descargar Libro de Conciliación Bancaria (.XLSX)", data=buffer.getvalue(), file_name=f"Conciliacion_Libros_{st.session_state.empresa if st.session_state.empresa else 'TaxFlow'}.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", use_container_width=True)
st.write("")
tab1, tab2, tab3 = st.tabs(["✅ Partidas Conciliadas", "⚠️ Movimientos Solo en Banco", "📖 Movimientos Solo en Auxiliar"])
with tab1: st.dataframe(st.session_state.df_conciliados, use_container_width=True)
with tab2: st.dataframe(st.session_state.bancos_pendientes, use_container_width=True)
with tab3: st.dataframe(st.session_state.auxiliar_pendientes, use_container_width=True)
