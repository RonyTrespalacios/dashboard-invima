"""
HU03: Tablero Público
"""
import streamlit as st
import requests
import pandas as pd
import os

st.set_page_config(page_title="Tablero Público", page_icon="🌐", layout="wide")

FASTAPI_URL = os.getenv("FASTAPI_URL", "http://localhost:8000")
API_TABLERO = f"{FASTAPI_URL}/api/v1/public/tablero"

st.title("🌐 Tablero Público")
st.markdown("Información pública de trámites del INVIMA")

# Auto-refresh
if st.button("🔄 Actualizar", use_container_width=True):
    st.cache_data.clear()

@st.cache_data(ttl=600)  # Cache por 10 minutos
def load_tablero():
    try:
        response = requests.get(API_TABLERO)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        st.error(f"Error al cargar tablero: {str(e)}")
        return None

# Cargar datos
with st.spinner("Cargando tablero público..."):
    tablero = load_tablero()

if tablero:
    stats = tablero.get('estadisticas', {})
    ultimos = tablero.get('ultimos_tramites', [])
    
    # Banner de información
    st.info("ℹ️ Este tablero muestra información pública sobre los trámites del INVIMA en tiempo real.")
    
    # Resumen ejecutivo
    st.subheader("📊 Resumen Ejecutivo")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        total = stats.get('total_tramites', 0)
        st.metric(
            label="📝 Total de Trámites",
            value=f"{total:,}",
            help="Cantidad total de trámites registrados"
        )
    
    with col2:
        por_estado = stats.get('por_estado', [])
        estados_activos = len([e for e in por_estado if int(e.get('cantidad', 0)) > 0])
        st.metric(
            label="🏷️ Estados Activos",
            value=estados_activos,
            help="Cantidad de estados con trámites"
        )
    
    with col3:
        if por_estado:
            estado_principal = por_estado[0]
            st.metric(
                label="⭐ Estado Principal",
                value=estado_principal.get('estado', 'N/A'),
                delta=f"{estado_principal.get('cantidad', 0)} trámites",
                help="Estado con más trámites"
            )
    
    st.divider()
    
    # Distribución rápida
    st.subheader("📈 Distribución de Estados (Top 5)")
    
    if por_estado:
        df_estados = pd.DataFrame(por_estado[:5])
        df_estados['cantidad'] = pd.to_numeric(df_estados['cantidad'], errors='coerce')
        
        for _, row in df_estados.iterrows():
            estado = row['estado']
            cantidad = int(row['cantidad'])
            
            col1, col2 = st.columns([3, 1])
            with col1:
                st.progress(
                    cantidad / total if total > 0 else 0,
                    text=estado
                )
            with col2:
                st.metric("", f"{cantidad:,}")
    
    st.divider()
    
    # Últimos trámites
    st.subheader("🕐 Últimos Trámites Registrados")
    
    if ultimos:
        df_ultimos = pd.DataFrame(ultimos)
        
        # Seleccionar columnas principales
        columnas_mostrar = []
        for col in ['numero_radicado', 'nombre_tramite', 'estado', 'fecha_radicacion']:
            if col in df_ultimos.columns:
                columnas_mostrar.append(col)
        
        if columnas_mostrar:
            st.dataframe(
                df_ultimos[columnas_mostrar],
                use_container_width=True,
                hide_index=True
            )
        else:
            st.dataframe(df_ultimos, use_container_width=True, hide_index=True)
    else:
        st.warning("No hay trámites recientes disponibles")
    
    st.divider()
    
    # Información de actualización
    st.caption("ℹ️ Los datos se actualizan cada 10 minutos automáticamente")
    
else:
    st.error("⚠️ No se pudo cargar el tablero público. Por favor, intenta más tarde.")

# Información adicional
with st.expander("📖 Acerca del Tablero Público"):
    st.markdown("""
    ### ¿Qué es el Tablero Público?
    
    El tablero público proporciona una vista general y en tiempo real de los trámites 
    registrados en el INVIMA, accesible para cualquier ciudadano.
    
    ### Información Mostrada
    
    - **Resumen Ejecutivo**: Métricas principales del sistema
    - **Distribución de Estados**: Los 5 estados con más trámites
    - **Últimos Trámites**: Los 10 trámites más recientes
    
    ### Fuente de Datos
    
    Toda la información proviene del portal de Datos Abiertos de Colombia,
    consultada en tiempo real a través de la API Socrata.
    
    ### Privacidad
    
    Solo se muestra información de carácter público según las políticas
    de datos abiertos del gobierno colombiano.
    """)
