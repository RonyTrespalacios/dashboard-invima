"""
HU05: Visualizar Reportes de Errores (Datos Anónimos)
"""
import streamlit as st
import requests
import os
import pandas as pd
from datetime import datetime
from typing import Dict, List

st.set_page_config(page_title="Ver Reportes de Errores", page_icon="📊", layout="wide")

FASTAPI_URL = os.getenv("FASTAPI_URL", "http://localhost:8000")
API_REPORTES = f"{FASTAPI_URL}/api/v1/reportes/listar-anonimos"

st.title("📊 Reportes de Errores Registrados")
st.markdown("Visualización de reportes de errores con datos anónimos para análisis y seguimiento")

# Información sobre privacidad
st.info("""
🔒 **Privacidad y Anonimización**

Los datos personales (nombres y correos electrónicos) han sido anonimizados para proteger 
la privacidad de los usuarios. Solo se muestran datos técnicos relevantes para el análisis.
""")

# Los datos ya vienen anonimizados desde la API

# Función para obtener reportes
@st.cache_data(ttl=300)  # Cache por 5 minutos
def obtener_reportes():
    """Obtiene los reportes desde la API"""
    try:
        response = requests.get(API_REPORTES, timeout=10)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        st.error(f"❌ Error al obtener reportes: {str(e)}")
        return {"reportes": [], "total": 0}

# Cargar datos
with st.spinner("Cargando reportes..."):
    data = obtener_reportes()
    reportes = data.get("reportes", [])
    total_reportes = data.get("total", 0)

if not reportes:
    st.warning("📭 No hay reportes registrados aún.")
    st.info("Los reportes aparecerán aquí una vez que los usuarios comiencen a reportar errores.")
else:
    st.success(f"📈 Se encontraron **{total_reportes}** reportes registrados")
    
    # Los reportes ya vienen anonimizados desde la API
    # Crear DataFrame para análisis
    df = pd.DataFrame(reportes)
    
    # Convertir fecha para análisis
    df['fecha_reporte'] = pd.to_datetime(df['fecha_reporte'], errors='coerce')
    
    # Filtros
    st.subheader("🔍 Filtros de Búsqueda")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        tipo_filtro = st.selectbox(
            "Filtrar por tipo de error",
            options=["Todos"] + list(df['tipo_error'].unique()),
            key="filtro_tipo"
        )
    
    with col2:
        contacto_filtro = st.selectbox(
            "Filtrar por contacto",
            options=["Todos", "Con contacto", "Sin contacto"],
            key="filtro_contacto"
        )
    
    with col3:
        fecha_filtro = st.date_input(
            "Filtrar por fecha (desde)",
            value=None,
            key="filtro_fecha"
        )
    
    # Aplicar filtros
    df_filtrado = df.copy()
    
    if tipo_filtro != "Todos":
        df_filtrado = df_filtrado[df_filtrado['tipo_error'] == tipo_filtro]
    
    if contacto_filtro == "Con contacto":
        df_filtrado = df_filtrado[df_filtrado['tiene_contacto'] == "Sí"]
    elif contacto_filtro == "Sin contacto":
        df_filtrado = df_filtrado[df_filtrado['tiene_contacto'] == "No"]
    
    if fecha_filtro:
        df_filtrado = df_filtrado[df_filtrado['fecha_reporte'].dt.date >= fecha_filtro]
    
    st.info(f"📊 Mostrando **{len(df_filtrado)}** reportes filtrados")
    
    # Estadísticas generales
    st.subheader("📈 Estadísticas Generales")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Reportes", len(df_filtrado))
    
    with col2:
        tipos_unicos = df_filtrado['tipo_error'].nunique()
        st.metric("Tipos de Error", tipos_unicos)
    
    with col3:
        con_contacto = len(df_filtrado[df_filtrado['tiene_contacto'] == 'Sí'])
        st.metric("Con Contacto", con_contacto)
    
    with col4:
        sin_contacto = len(df_filtrado[df_filtrado['tiene_contacto'] == 'No'])
        st.metric("Sin Contacto", sin_contacto)
    
    # Gráficos
    st.subheader("📊 Análisis Visual")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Gráfico de tipos de error
        tipo_counts = df_filtrado['tipo_error'].value_counts()
        if not tipo_counts.empty:
            st.bar_chart(tipo_counts)
            st.caption("Distribución por tipo de error")
    
    with col2:
        # Gráfico de contacto
        contacto_counts = df_filtrado['tiene_contacto'].value_counts()
        if not contacto_counts.empty:
            st.bar_chart(contacto_counts)
            st.caption("Reportes con/sin información de contacto")
    
    # Tabla detallada
    st.subheader("📋 Lista Detallada de Reportes")
    
    # Configurar columnas para mostrar
    columnas_mostrar = ['reporte_id', 'tipo_error', 'fecha_reporte', 'tiene_contacto', 'numero_radicado']
    
    # Mostrar tabla
    st.dataframe(
        df_filtrado[columnas_mostrar],
        use_container_width=True,
        hide_index=True
    )
    
    # Expandir para ver descripción
    st.subheader("📝 Descripciones de los Reportes")
    
    for idx, reporte in df_filtrado.iterrows():
        with st.expander(f"Reporte {reporte['reporte_id']} - {reporte['tipo_error']}"):
            col1, col2 = st.columns(2)
            
            with col1:
                st.write(f"**ID:** {reporte['reporte_id']}")
                st.write(f"**Tipo:** {reporte['tipo_error']}")
                st.write(f"**Fecha:** {reporte['fecha_reporte']}")
                st.write(f"**Tiene Contacto:** {reporte['tiene_contacto']}")
                if reporte['numero_radicado'] != 'N/A':
                    st.write(f"**Radicado:** {reporte['numero_radicado']}")
            
            with col2:
                st.write("**Descripción:**")
                st.write(reporte['descripcion'])

# Información adicional
st.divider()

with st.expander("ℹ️ Información sobre la Visualización"):
    st.markdown("""
    ### ¿Qué información se muestra?
    
    - **ID del Reporte**: Identificador único para seguimiento
    - **Tipo de Error**: Categorización del problema reportado
    - **Fecha**: Cuándo fue reportado el error
    - **Tiene Contacto**: Si el usuario proporcionó datos de contacto
    - **Radicado**: Número de radicado si aplica
    - **Descripción**: Detalles del problema reportado
    
    ### ¿Por qué los datos están anonimizados?
    
    - **Privacidad**: Protección de datos personales de los usuarios
    - **Cumplimiento**: Respeto a las políticas de privacidad
    - **Enfoque**: Análisis técnico sin exposición de información personal
    
    ### ¿Cómo usar esta información?
    
    - **Identificar patrones**: Tipos de errores más comunes
    - **Priorizar correcciones**: Enfocar esfuerzos en problemas frecuentes
    - **Seguimiento**: Monitorear la efectividad de las correcciones
    - **Análisis temporal**: Ver tendencias en el tiempo
    """)

# Botón para actualizar datos
if st.button("🔄 Actualizar Datos", use_container_width=True):
    st.cache_data.clear()
    st.rerun()
