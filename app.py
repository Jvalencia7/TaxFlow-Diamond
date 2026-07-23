import streamlit as st
import pandas as pd
import io

# ==========================================
# 1. CONFIGURACIÓN CORPORATIVA DE LA SUITE
# ==========================================
st.set_page_config(
    page_title="TaxFlow-Diamond | Suite de Conciliación",
    page_icon="💎",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Estilos CSS personalizados para la identidad de marca
st.markdown("""
    <style>
    .main-title {
        font-size: 38px !important;
        font-weight: 700 !important;
        color: #0A2540; /* Azul corporativo profundo */
        margin-bottom: 5px;
    }
    .subtitle {
        font-size: 16px !important;
        color: #639FAB;
        margin-bottom: 30px;
        font-weight: 500;
    }
    .section-header {
        color: #0A2540;
        font-weight: 600;
        border-bottom: 2px solid #F4F6F8;
        padding-bottom: 10px;
        margin-bottom: 15px;
    }
    </style>
""", unsafe_allow_html=True)

# Encabezado principal
st.markdown('<div class="main-title">💎 TaxFlow-Diamond</div>', unsafe_style_html=True)
st.markdown('<div class="subtitle">Enterprise Financial & XML Reconciliation Suite</div>', unsafe_style_html=True)

# ==========================================
# 2. SECCIÓN DE CARGA DE DOCUMENTOS
# ==========================================
st.markdown('<div class="section-header">📂 Importación de Datos Financieros</div>', unsafe_style_html=True)

col1, col2 = st.columns(2)

with col1:
    st.subheader("1. Estado de Cuenta Bancario")
    banco_file = st.file_uploader("Sube el archivo del Banco (CSV o Excel)", type=["csv", "xlsx"], key="banco")
    
with col2:
    st.subheader("2. Reporte de Facturas / XML")
    facturas_file = st.file_uploader("Sube el reporte de XML/Facturas (CSV o Excel)", type=["csv", "xlsx"], key="facturas")

# Función optimizada para la lectura de datos
def cargar_archivo(file):
    if file.name.endswith('.csv'):
        return pd.read_csv(file)
    else:
        return pd.read_excel(file)

# ==========================================
# 3. PROCESAMIENTO Y CONFIGURACIÓN DE COLUMNAS
# ==========================================
if banco_file and facturas_file:
    try:
        # Carga de dataframes en memoria
        df_banco = cargar_archivo(banco_file)
        df_facturas = cargar_archivo(facturas_file)
        
        st.success("🏁 Ambos estados financieros han sido indexados correctamente en el sistema.")
        
        st.markdown('<div class="section-header">⚙️ Configuración del Mapeo de Columnas</div>', unsafe_style_html=True)
        st.write("Identifica las columnas que corresponden a los importes monetarios en cada archivo para ejecutar el cruce:")
        
        c1, c2 = st.columns(2)
        with c1:
            col_monto_banco = st.selectbox("Columna de Monto/Importe en el BANCO:", df_banco.columns)
        with c2:
            col_monto_factura = st.selectbox("Columna de Monto/Importe en FACTURAS/XML:", df_facturas.columns)
            
        # Botón de ejecución con diseño prioritario
        st.write("")
        if st.button("🚀 Ejecutar Algoritmo de Conciliación", type="primary", use_container_width=True):
            
            # Estandarización de datos: conversión numérica y valores absolutos
            df_banco['Monto_Abs'] = df_banco[col_monto_banco].astype(float).abs()
            df_facturas['Monto_Abs'] = df_facturas[col_monto_factura].astype(float).abs()
            
            # --- ALGORITMO DE CRUCE DE DATOS ---
            # Matcheo exacto (Inner Join)
            df_conciliados = pd.merge(
                df_banco, 
                df_facturas, 
                on='Monto_Abs', 
                how='inner', 
                suffixes=('_Banco', '_Factura')
            )
            
            # Registros huérfanos (Pendientes de conciliar)
            bancos_pendientes = df_banco[~df_banco['Monto_Abs'].isin(df_conciliados['Monto_Abs'])].drop(columns=['Monto_Abs'])
            facturas_pendientes = df_facturas[~df_facturas['Monto_Abs'].isin(df_conciliados['Monto_Abs'])].drop(columns=['Monto_Abs'])
            
            # Limpieza del dataframe conciliado final para la visualización
            if 'Monto_Abs' in df_conciliados.columns:
                df_conciliados = df_conciliados.drop(columns=['Monto_Abs'])

            # ==========================================
            # 4. TABLERO DE RESULTADOS CORPORATIVOS
            # ==========================================
            st.markdown('<div class="section-header">📊 Dashboard de Auditoría Analítica</div>', unsafe_style_html=True)
            
            # Métricas de alto impacto visual
            m1, m2, m3 = st.columns(3)
            m1.metric("Movimientos Conciliados", f"{len(df_conciliados)} registros", "✓ Correcto")
            m2.metric("Discrepancias en Banco", f"{len(bancos_pendientes)} registros", f"-{len(bancos_pendientes)} pendientes", delta_color="inverse")
            m3.metric("XMLs sin Asignación", f"{len(facturas_pendientes)} registros", f"-{len(facturas_pendientes)} pendientes", delta_color="inverse")
            
            # Pestañas corporativas para la segregación de cuentas
            tab1, tab2, tab3 = st.tabs([
                "✅ Movimientos Conciliados", 
                "⚠️ Pendientes en Estado de Cuenta", 
                "📄 Facturas XML sin Cobrar/Pagar"
            ])
            
            with tab1:
                st.write("Registros que coinciden perfectamente en monto entre el banco y los comprobantes fiscales:")
                st.dataframe(df_conciliados, use_container_width=True)
                
            with tab2:
                st.write("Flujos de efectivo detectados en el banco que no cuentan con un XML asociado:")
                st.dataframe(bancos_pendientes, use_container_width=True)
                
            with tab3:
                st.write("Comprobantes fiscales emitidos/recibidos que no presentan movimientos de pago en la cuenta bancaria:")
                st.dataframe(facturas_pendientes, use_container_width=True)
                
    except Exception as e:
        st.error(f"Error Operacional: No se pudo procesar la conciliación automatizada.")
        st.info(f"Detalle técnico: {e}. Valida que las columnas seleccionadas contengan valores estrictamente numéricos.")
else:
    # Contenedor de espera inicial para guiar al usuario corporativo
    st.info("💡 Suite lista para operar. Por favor, cargue los archivos del Estado de Cuenta Bancario y el Reporte de Facturas en la sección superior para iniciar el análisis.")
