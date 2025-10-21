"""
HU02: Estadísticas del Dashboard
"""
import streamlit as st
import requests
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import os

st.set_page_config(page_title="Estadísticas", page_icon="📊", layout="wide")

FASTAPI_URL = os.getenv("FASTAPI_URL", "http://localhost:8000")
API_STATS = f"{FASTAPI_URL}/api/v1/dashboard/estadisticas"
API_METRICS = f"{FASTAPI_URL}/api/v1/dashboard/metricas"

st.title("📊 Estadísticas del Dashboard")
st.markdown("Visualización de métricas y tendencias de trámites INVIMA")

# Botón de actualizar
if st.button("🔄 Actualizar Datos", use_container_width=True):
    st.cache_data.clear()

# Función para cargar estadísticas
@st.cache_data(ttl=300)
def load_stats():
    try:
        response = requests.get(API_STATS)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        st.error(f"Error al cargar estadísticas: {str(e)}")
        return None

@st.cache_data(ttl=300)
def load_metrics():
    try:
        response = requests.get(API_METRICS)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        st.error(f"Error al cargar métricas: {str(e)}")
        return None

# Cargar datos
with st.spinner("Cargando estadísticas..."):
    stats = load_stats()
    metrics = load_metrics()

if stats and metrics:
    # Métricas principales
    st.subheader("📈 Métricas Principales")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric(
            label="Total de Trámites",
            value=f"{stats.get('total_tramites', 0):,}",
            help="Cantidad total de trámites registrados"
        )
    
    with col2:
        estados_count = len(metrics.get('estados_disponibles', []))
        st.metric(
            label="Estados Diferentes",
            value=estados_count,
            help="Cantidad de estados únicos"
        )
    
    with col3:
        por_estado = stats.get('por_estado', [])
        if por_estado:
            promedio = sum(int(e.get('cantidad', 0)) for e in por_estado) // len(por_estado)
            st.metric(
                label="Promedio por Estado",
                value=f"{promedio:,}",
                help="Promedio de trámites por estado"
            )
    
    st.divider()
    
    # Gráfico de trámites por estado
    st.subheader("📊 Distribución por Estado")
    por_estado = stats.get('por_estado', [])
    
    if por_estado:
        df_estado = pd.DataFrame(por_estado)
        df_estado['cantidad'] = pd.to_numeric(df_estado['cantidad'], errors='coerce')
        df_estado = df_estado.sort_values('cantidad', ascending=False).head(10)
        
        col1, col2 = st.columns([2, 1])
        
        with col1:
            fig_bar = px.bar(
                df_estado,
                x='estado',
                y='cantidad',
                title='Top 10 Estados con Más Trámites',
                labels={'estado': 'Estado', 'cantidad': 'Cantidad'},
                color='cantidad',
                color_continuous_scale='Blues'
            )
            fig_bar.update_layout(showlegend=False)
            st.plotly_chart(fig_bar, use_container_width=True)
        
        with col2:
            fig_pie = px.pie(
                df_estado,
                values='cantidad',
                names='estado',
                title='Proporción de Estados'
            )
            st.plotly_chart(fig_pie, use_container_width=True)
    
    st.divider()
    
    # Gráfico de tendencia por mes
    st.subheader("📅 Tendencia Mensual")
    por_mes = stats.get('por_mes', [])
    
    if por_mes:
        df_mes = pd.DataFrame(por_mes)
        df_mes['cantidad'] = pd.to_numeric(df_mes['cantidad'], errors='coerce')
        df_mes = df_mes.sort_values('mes')
        
        fig_line = go.Figure()
        fig_line.add_trace(go.Scatter(
            x=df_mes['mes'],
            y=df_mes['cantidad'],
            mode='lines+markers',
            name='Trámites',
            line=dict(color='#1f77b4', width=3),
            marker=dict(size=8)
        ))
        
        fig_line.update_layout(
            title='Trámites por Mes (Últimos 12 meses)',
            xaxis_title='Mes',
            yaxis_title='Cantidad de Trámites',
            hovermode='x unified'
        )
        
        st.plotly_chart(fig_line, use_container_width=True)
        
        # Tabla resumen
        with st.expander("📋 Ver tabla de datos"):
            st.dataframe(df_mes, use_container_width=True, hide_index=True)
    
    st.divider()
    
    # Lista de estados disponibles
    st.subheader("🏷️ Estados Disponibles")
    estados = metrics.get('estados_disponibles', [])
    if estados:
        estados_filtrados = [e for e in estados if e]  # Filtrar valores vacíos
        cols = st.columns(4)
        for idx, estado in enumerate(estados_filtrados):
            with cols[idx % 4]:
                st.info(estado)

else:
    st.warning("⚠️ No se pudieron cargar las estadísticas. Verifica la conexión con la API.")

# Información adicional
with st.expander("ℹ️ Acerca de las estadísticas"):
    st.markdown("""
    ### Métricas Mostradas
    
    - **Total de Trámites**: Cantidad total de registros en el sistema
    - **Estados Diferentes**: Cantidad de estados únicos en los que pueden estar los trámites
    - **Distribución por Estado**: Muestra los 10 estados con más trámites
    - **Tendencia Mensual**: Evolución de trámites en los últimos 12 meses
    
    ### Actualización
    Los datos se actualizan cada 5 minutos automáticamente. 
    Usa el botón "Actualizar Datos" para forzar una actualización inmediata.
    """)
