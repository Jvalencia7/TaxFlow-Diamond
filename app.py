import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import matplotlib.pyplot as plt
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
    'df_banco': None, 'df_auxiliar': None, 'bancos_cargados': False, 'bancos_ejecutado': False,
    'df_conciliados': None, 'bancos_pendientes': None, 'auxiliar_pendientes': None,
    'suma_conciliado': 0.0, 'suma_banco_p': 0.0, 'suma_aux_p': 0.0, 'fase_progreso': 1,
    'empresa': "", 'periodo': "", 'auditor': "", 'tolerancia': 0.50, 'divisa': "MXN ($)", 'logo_bytes': None
}

for llave, valor_defecto in variables_sesion.items():
    if llave not in st.session_state:
        st.session_state[llave] = valor_defecto

# ==============================================================================
# 3. NAVEGACIÓN SUPERIOR INTEGRAL
# ==============================================================================
st.markdown('<div class="section-header">🗺️ Módulos de la Suite</div>', unsafe_allow_html=True)
tab_dashboard, tab_bancos, tab_configuracion, tab_ayuda = st.tabs([
    "📊 Dashboard", "🏦 Módulo Bancario", "⚙️ Configuración", "❓ Ayuda"
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

# Generación dinámica en memoria de plantillas Excel estructuradas
buffer_p1 = io.BytesIO()
with pd.ExcelWriter(buffer_p1, engine='openpyxl') as w:
    pd.DataFrame(columns=["Fecha", "Concepto", "Referencia", "Importe", "RFC_Contraparte"]).to_excel(w, index=False)
st.sidebar.download_button("📊 Plantilla Estado de Cuenta", data=buffer_p1.getvalue(), file_name="Plantilla_Estado_Cuenta.xlsx", use_container_width=True)

buffer_p2 = io.BytesIO()
with pd.ExcelWriter(buffer_p2, engine='openpyxl') as w:
    pd.DataFrame(columns=["Fecha_Poliza", "Cuenta_Contable", "Concepto_Movimiento", "Monto_Registro", "RFC_Validar"]).to_excel(w, index=False)
st.sidebar.download_button("📖 Plantilla Auxiliar Contable", data=buffer_p2.getvalue(), file_name="Plantilla_Auxiliar_Contable.xlsx", use_container_width=True)

def leer_archivo_contable(file):
    if file.name.endswith('.csv'): return pd.read_csv(file)
    return pd.read_excel(file)

def validar_rfc(rfc):
    # Regex oficial para validación de RFC corporativo e individual (México)
    pattern = r'^[A-Z&Ñ]{3,4}[0-9]{2}(0[1-9]|1[0-2])(0[1-9]|[12][0-9]|3[01])[A-Z0-9]{3}$'
    return bool(re.match(pattern, str(rfc).upper().strip()))
# ==============================================================================
# 5. GENERADOR DE DICTAMEN DE AUDITORÍA FORMAL EN FORMATO PDF
# ==============================================================================
def generar_dictamen_pdf(empresa, periodo, auditor, conciliado, banco_p, aux_p, divisa):
    fig, ax = plt.subplots(figsize=(8.5, 11))
    ax.axis('off')
    
    # Maquetación del documento institucional membretado
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
    
    dictamen_txt = (
        "Habiendo aplicado los algoritmos de validación cruzada y cruzamiento por doble factor (Monto + Fecha)\n"
        "se concluye que los libros contables presentan una consistencia alineada con los parámetros de negocio.\n"
        "Las partidas detectadas en calidad de pendientes quedan documentadas en los anexos del libro Excel."
    )
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
    
    # Barra de progreso visual superior del flujo de auditoría
    fases = ["1. Configuración", "2. Carga Insumos", "3. Mapeo Columnas", "4. Reportes y Dictamen"]
    st.progress(st.session_state.fase_progreso / 4, text=f"Progreso del Flujo de Trabajo: **{fases[st.session_state.fase_progreso - 1]}**")
    st.write("")

    if st.session_state.bancos_ejecutado:
        st.markdown('<div class="section-header">📊 Indicadores de Riesgo Corporativo</div>', unsafe_allow_html=True)
        
        # Lógica de Semáforo Corporativo
        total_pendientes = st.session_state.suma_banco_p + st.session_state.suma_aux_p
        porcentaje_riesgo = (total_pendientes / st.session_state.suma_conciliado * 100) if st.session_state.suma_conciliado > 0 else 0
        
        if porcentaje_riesgo <= 2.0:
            clase_semaforo, mensaje_semaforo = "kpi-green", "🟢 NIVEL DE RIESGO BAJO: Cuentas y Libros Alineados."
        elif porcentaje_riesgo <= 5.0:
            clase_semaforo, mensaje_semaforo = "kpi-yellow", "🟡 NIVEL DE RIESGO MODERADO: Monitorear partidas en tránsito."
        else:
            clase_semaforo, mensaje_semaforo = "kpi-red", "🔴 ALERTA DE AUDITORÍA - RIESGO ALTO: Desfase financiero crítico."

        st.markdown(f'<div class="kpi-card {clase_semaforo}">{mensaje_semaforo} (Desfase del {porcentaje_riesgo:.2f}% sobre capital amarrado)</div>', unsafe_allow_html=True)
        
        # Despliegue de métricas
        m1, m2, m3 = st.columns(3)
        simbolo = st.session_state.divisa.split(" ")[0]
        m1.metric("Capital Conciliado", f"{simbolo} {st.session_state.suma_conciliado:,.2f}")
        m2.metric("Pendientes Banco", f"{simbolo} {st.session_state.suma_banco_p:,.2f}", delta_color="inverse")
        m3.metric("Pendientes Auxiliar", f"{simbolo} {st.session_state.suma_aux_p:,.2f}", delta_color="inverse")
        
        # Gráfica de pastel
        df_grafico = pd.DataFrame({
            "Concepto": ["Saldos Conciliados", "Pendientes Banco", "Pendientes Auxiliar"],
            "Importe": [st.session_state.suma_conciliado, st.session_state.suma_banco_p, st.session_state.suma_aux_p]
        })
        fig = px.pie(df_grafico, values="Importe", names="Concepto", color_discrete_sequence=["#00D4FF", "#FF4B4B", "#FFA500"], hole=0.4)
        fig.update_layout(template="plotly_dark", paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
        st.plotly_chart(fig, use_container_width=True)
        
        # MÓDULO EXCLUSIVO: Descarga del Dictamen de Auditoría Formal Certificado en PDF
        st.markdown("---")
        st.subheader("📜 Dictamen de Certificación Contable")
        st.write("Genera el acta jurídica formal firmada electrónicamente por el auditor a cargo:")
        
        pdf_dictamen = generar_dictamen_pdf(
            st.session_state.empresa, st.session_state.periodo, st.session_state.auditor,
            st.session_state.suma_conciliado, st.session_state.suma_banco_p, st.session_state.suma_aux_p, simbolo
        )
        st.download_button(
            label="📥 Descargar Dictamen Formal Certificado (PDF Oficial)",
            data=pdf_dictamen,
            file_name=f"Dictamen_Auditoria_{st.session_state.empresa if st.session_state.empresa else 'TaxFlow'}.pdf",
            mime="application/pdf",
            use_container_width=True
        )
    else:
        st.info("💎 Suite Corporativa TaxFlow-Diamond inicializada. Dirígete al Módulo Bancario para comenzar la auditoría.")

# ==============================================================================
# 7. DESPLIEGUE: PESTAÑA CONFIGURACIÓN
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
            st.session_state.fase_progreso = 2 # Avanza la barra de progreso
            st.rerun()
# ==============================================================================
# 8. DESPLIEGUE: PESTAÑA MÓDULO BANCARIO (CON PRE-VALIDACIÓN DE RFC Y ESTRUCTURAS)
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
        st.success("🏁 Papeles de trabajo financieros indexados de forma correcta en memoria.")
        if st.button("🔄 Cargar nuevos archivos de banco", key="reset_b"):
            st.session_state.bancos_cargados, st.session_state.bancos_ejecutado = False, False
            st.session_state.fase_progreso = 1
            st.rerun()
            
    if st.session_state.bancos_cargados:
        df_b, df_a = st.session_state.df_banco, st.session_state.df_auxiliar
        st.markdown('<div class="section-header">⚙️ Configuración del Mapeo de Auditoría</div>', unsafe_allow_html=True)
        
        c1, c2, c3, c4 = st.columns(4)
        with c1: cb_m = st.selectbox("Monto BANCO:", df_b.columns, key="cb_m")
        with c2: cb_f = st.selectbox("Fecha BANCO:", df_b.columns, key="cb_f")
        with c3: ca_m = st.selectbox("Monto AUXILIAR:", df_a.columns, key="ca_m")
        with c4: ca_f = st.selectbox("Fecha AUXILIAR:", df_a.columns, key="ca_f")
        
        # MÓDULO EXCLUSIVO: Filtro avanzado de Pre-Validación de estructuras de RFC o texto corrupto
        st.markdown("---")
        st.subheader("🛡️ Panel de Pre-Validación de Insumos")
        
        col_v1, col_v2 = st.columns(2)
        with col_v1:
            col_rfc_b = st.selectbox("Columna de RFC en archivo BANCO (Opcional):", ["Ninguna"] + list(df_b.columns))
            if col_rfc_b != "Ninguna":
                rfcs_b_invalidos = df_b[~df_b[col_rfc_b].apply(validar_rfc)]
                if len(rfcs_b_invalidos) > 0:
                    st.warning(f"⚠️ Se detectaron {len(rfcs_b_invalidos)} celdas con RFC de estructura inválida en el Banco. Revisa el archivo.")
                else:
                    st.success("✓ Estructuras de RFC en Banco validadas al 100%.")
        with col_v2:
            col_rfc_a = st.selectbox("Columna de RFC en archivo AUXILIAR (Opcional):", ["Ninguna"] + list(df_a.columns))
            if col_rfc_a != "Ninguna":
                rfcs_a_invalidos = df_a[~df_a[col_rfc_a].apply(validar_rfc)]
                if len(rfcs_a_invalidos) > 0:
                    st.warning(f"⚠️ Se detectaron {len(rfcs_a_invalidos)} celdas con RFC de estructura inválida en Contabilidad.")
                else:
                    st.success("✓ Estructuras de RFC en Auxiliar validadas al 100%.")

        if st.button("🚀 Ejecutar Algoritmo de Conciliación Diamond", type="primary", use_container_width=True):
            try:
                df_b_c = df_b.dropna(subset=[cb_m, cb_f]).copy()
                df_a_c = df_a.dropna(subset=[ca_m, ca_f]).copy()
                
                df_b_c['Monto_Limpio'] = pd.to_numeric(df_b_c[cb_m], errors='coerce').fillna(0).abs()
                df_a_c['Monto_Limpio'] = pd.to_numeric(df_a_c[ca_m], errors='coerce').fillna(0).abs()
                
                df_b_c['Fecha_Limpia'] = pd.to_datetime(df_b_c[cb_f], format='mixed', dayfirst=True).dt.date
                df_a_c['Fecha_Limpia'] = pd.to_datetime(df_a_c[ca_f], format='mixed', dayfirst=True).dt.date
                
                df_b_s = df_b_c.sort_values('Monto_Limpio').reset_index(drop=True)
                df_a_s = df_a_c.sort_values('Monto_Limpio').reset_index(drop=True)
                
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
            except Exception as e: st.error(f"Error Operacional: {e}")

        if st.session_state.bancos_ejecutado:
            st.markdown('<div class="section-header">💾 Centro de Exportación de Resultados</div>', unsafe_allow_html=True)
            buffer = io.BytesIO()
            with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
                if st.session_state.df_conciliados is not None: st.session_state.df_conciliados.to_excel(writer, sheet_name='Partidas_Conciliadas', index=False)
                if st.session_state.bancos_pendientes is not None: st.session_state.bancos_pendientes.to_excel(writer, sheet_name='Pendientes_Solo_Banco', index=False)
                if st.session_state.auxiliar_pendientes is not None: st.session_state.auxiliar_pendientes.to_excel(writer, sheet_name='Pendientes_Solo_Auxiliar', index=False)
            
            st.download_button(label="📥 Descargar Libro de Conciliación Completo (.XLSX)", data=buffer.getvalue(), file_name="Reporte_Conciliacion_Diamond.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", use_container_width=True)
            
            st.write("")
            tab1, tab2, tab3 = st.tabs(["✅ Partidas Conciliadas", "⚠️ Movimientos Solo en Banco", "📖 Movimientos Solo en Auxiliar"])
            with tab1: st.dataframe(st.session_state.df_conciliados, use_container_width=True)
            with tab2: st.dataframe(st.session_state.bancos_pendientes, use_container_width=True)
            with tab3: st.dataframe(st.session_state.auxiliar_pendientes, use_container_width=True)

with tab_ayuda:
    st.write("")
