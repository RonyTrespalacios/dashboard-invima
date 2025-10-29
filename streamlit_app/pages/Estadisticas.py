"""
Estadísticas de Trámites del INVIMA
Dashboard de análisis y visualización de datos
"""
import streamlit as st
import requests
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import os
from io import BytesIO
import xlsxwriter

st.set_page_config(page_title="Estadísticas INVIMA", page_icon="📊", layout="wide")

FASTAPI_URL = os.getenv("FASTAPI_URL", "http://localhost:8000")
API_STATS_SUIT = f"{FASTAPI_URL}/api/v1/dashboard/estadisticas-suit"

# Header
st.title("📊 Estadísticas de Trámites")
st.markdown("Análisis y visualización de datos del INVIMA")

# Info de conectividad
info_col1, info_col2 = st.columns([3, 1])
with info_col2:
    if st.button("🔄 Recargar", help="Limpiar caché y recargar datos"):
        st.cache_data.clear()
        st.rerun()

st.divider()

# Sidebar - Filtros
st.sidebar.header("🔍 Filtros")
st.sidebar.markdown("Personaliza tu búsqueda")

# Cargar datos iniciales para opciones de filtros
@st.cache_data(ttl=300)
def cargar_datos_filtros():
    try:
        response = requests.get(API_STATS_SUIT, timeout=10)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        st.sidebar.error(f"⚠️ Error conectando con la API: {str(e)}")
        st.sidebar.info("Asegúrate de que el backend FastAPI esté corriendo en http://localhost:8000")
        return None

# Inicializar listas por defecto
anos_disponibles = ["Todos"]
clases_disponibles = ["Todas"]

# Intentar cargar datos de filtros
with st.spinner("Cargando opciones de filtros..."):
    datos_filtros = cargar_datos_filtros()
    
if datos_filtros:
    anos_disponibles += datos_filtros.get("anos_disponibles", [])
    clases_disponibles += datos_filtros.get("clases_disponibles", [])
else:
    st.warning("⚠️ No se pudieron cargar los filtros. Usando valores por defecto.")

# Filtros
ano_seleccionado = st.sidebar.selectbox(
    "📅 Año",
    options=anos_disponibles,
    help="Filtrar trámites por año de registro"
)

clase_seleccionada = st.sidebar.selectbox(
    "📂 Clase de Trámite",
    options=clases_disponibles,
    help="Filtrar por clase de trámite"
)

palabra_clave = st.sidebar.text_input(
    "🔎 Palabra Clave",
    placeholder="Ej: sanitario, medicamento",
    help="Buscar en nombre del trámite"
)

aplicar_filtros = st.sidebar.button("🔄 Aplicar Filtros", use_container_width=True)

if aplicar_filtros:
    st.cache_data.clear()

# Cargar estadísticas con filtros
@st.cache_data(ttl=300)
def cargar_estadisticas(ano=None, clase=None, kw=None):
    try:
        params = {}
        if ano and ano != "Todos":
            params["ano"] = ano
        if clase and clase != "Todas":
            params["clase"] = clase
        if kw:
            params["palabra_clave"] = kw
        
        response = requests.get(API_STATS_SUIT, params=params, timeout=30)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.Timeout:
        st.error("⏱️ Consulta tardó más de 30 segundos. Intenta con filtros más específicos.")
        return None
    except Exception as e:
        st.error(f"❌ Error: {str(e)}")
        return None

filtro_ano = None if ano_seleccionado == "Todos" else ano_seleccionado
filtro_clase = None if clase_seleccionada == "Todas" else clase_seleccionada
filtro_kw = palabra_clave.strip() if palabra_clave.strip() else None

with st.spinner("⏳ Cargando estadísticas... (criterio: <5 segundos para 10,000 registros)"):
    data = cargar_estadisticas(filtro_ano, filtro_clase, filtro_kw)

if data:
    total_registros = data.get("total_registros", 0)
    por_ano = data.get("por_ano", [])
    por_clase = data.get("por_clase", [])
    top_tramites = data.get("top_tramites", [])
    distribucion_categorias = data.get("distribucion_categorias", [])
    filtros_aplicados = data.get("filtros_aplicados", {})
    
    # Mostrar filtros aplicados
    if any(filtros_aplicados.values()):
        with st.expander("ℹ️ Filtros Activos", expanded=False):
            cols = st.columns(3)
            if filtros_aplicados.get("ano"):
                cols[0].metric("Año", filtros_aplicados["ano"])
            if filtros_aplicados.get("clase"):
                cols[1].metric("Clase", filtros_aplicados["clase"][:30] + "...")
            if filtros_aplicados.get("palabra_clave"):
                cols[2].metric("Palabra Clave", filtros_aplicados["palabra_clave"])
    
    # Métricas resumen
    st.subheader("📊 Resumen General")
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("📋 Total Registros", f"{total_registros:,}", 
                 help="Cálculo directo sobre datos del SUIT")
    
    with col2:
        st.metric("📅 Años", len(por_ano))
    
    with col3:
        st.metric("📂 Clases", len(por_clase))
    
    with col4:
        st.metric("🏷️ Categorías", len(distribucion_categorias))
    
    st.divider()
    
    # Evolución temporal
    st.subheader("📅 Evolución Temporal de Trámites")
    
    if por_ano and len(por_ano) > 0:
        df_ano = pd.DataFrame(por_ano)
        df_ano['cantidad'] = pd.to_numeric(df_ano['cantidad'], errors='coerce')
        df_ano = df_ano.sort_values('ano')
        
        # Gráfico de barras vertical
        fig = go.Figure()
        
        # Crear gradiente de colores basado en la cantidad
        colors_scale = px.colors.sequential.Blues
        color_values = df_ano['cantidad'] / df_ano['cantidad'].max()
        bar_colors = [colors_scale[min(int(v * (len(colors_scale)-1)), len(colors_scale)-1)] for v in color_values]
        
        fig.add_trace(go.Bar(
            x=df_ano['ano'],
            y=df_ano['cantidad'],
            text=df_ano['cantidad'].apply(lambda x: f"{int(x):,}"),
            textposition='outside',
            marker=dict(
                color=bar_colors,
                line=dict(color='white', width=2)
            ),
            hovertemplate='<b>Año %{x}</b><br>Trámites: %{y:,}<extra></extra>'
        ))
        
        fig.update_layout(
            title='Evolución de Trámites por Año',
            xaxis_title='Año',
            yaxis_title='Cantidad de Trámites',
            height=450,
            showlegend=False,
            xaxis=dict(type='category'),
            plot_bgcolor='rgba(0,0,0,0)',
            yaxis=dict(gridcolor='rgba(128,128,128,0.2)')
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        # Mostrar análisis básico
        if len(df_ano) > 1:
            cambio = df_ano.iloc[-1]['cantidad'] - df_ano.iloc[0]['cantidad']
            porcentaje = (cambio / df_ano.iloc[0]['cantidad'] * 100) if df_ano.iloc[0]['cantidad'] > 0 else 0
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Primer Año", f"{df_ano.iloc[0]['ano']}", f"{int(df_ano.iloc[0]['cantidad']):,} trámites")
            with col2:
                st.metric("Último Año", f"{df_ano.iloc[-1]['ano']}", f"{int(df_ano.iloc[-1]['cantidad']):,} trámites")
            with col3:
                st.metric("Cambio Total", f"{porcentaje:+.1f}%", f"{int(cambio):+,} trámites")
    else:
        st.info("📊 Datos insuficientes para mostrar evolución temporal")
    
    st.divider()
    
    # Distribución por Categorías (más visual y útil)
    st.subheader("🏷️ Distribución por Categorías")
    
    if distribucion_categorias and len(distribucion_categorias) > 0:
        df_cat = pd.DataFrame(distribucion_categorias)
        df_cat = df_cat.sort_values('cantidad', ascending=False)
        df_cat['porcentaje'] = (df_cat['cantidad'] / df_cat['cantidad'].sum() * 100).round(1)
        
        # Crear visualización combinada
        col1, col2 = st.columns([2, 1])
        
        with col1:
            # Gráfico de barras horizontales con porcentajes
            fig = go.Figure()
            
            colors = px.colors.qualitative.Set3[:len(df_cat)]
            
            fig.add_trace(go.Bar(
                y=df_cat['categoria'],
                x=df_cat['cantidad'],
                orientation='h',
                text=[f"{int(c):,} ({p}%)" for c, p in zip(df_cat['cantidad'], df_cat['porcentaje'])],
                textposition='outside',
                marker=dict(
                    color=colors,
                    line=dict(color='white', width=2)
                ),
                hovertemplate='<b>%{y}</b><br>Cantidad: %{x:,}<br>Porcentaje: %{customdata:.1f}%<extra></extra>',
                customdata=df_cat['porcentaje']
            ))
            
            fig.update_layout(
                title='Categorías de Trámites',
                xaxis_title='Cantidad de Trámites',
                yaxis_title='',
                height=max(400, len(df_cat) * 50),
                showlegend=False,
                yaxis=dict(autorange="reversed")
            )
            
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            # Gráfico de dona
            fig_pie = px.pie(
                df_cat,
                values='cantidad',
                names='categoria',
                hole=0.4,
                color_discrete_sequence=colors
            )
            
            fig_pie.update_traces(
                textposition='inside',
                textinfo='percent',
                hovertemplate='<b>%{label}</b><br>%{value:,} trámites<br>%{percent}<extra></extra>'
            )
            
            fig_pie.update_layout(
                title='Proporción',
                height=400,
                showlegend=False
            )
            
            st.plotly_chart(fig_pie, use_container_width=True)
        
        # Tabla resumen
        with st.expander("📋 Ver detalle completo"):
            df_display = df_cat[['categoria', 'cantidad', 'porcentaje']].copy()
            df_display.columns = ['Categoría', 'Cantidad', 'Porcentaje (%)']
            df_display['Cantidad'] = df_display['Cantidad'].apply(lambda x: f"{int(x):,}")
            st.dataframe(df_display, use_container_width=True, hide_index=True)
    else:
        st.info("📊 No hay datos de categorías disponibles")
    
    st.divider()
    
    # Distribución por Clase (mejorado - solo si hay múltiples clases)
    if por_clase and len(por_clase) > 1:
        st.subheader("📑 Distribución por Clase")
        
        df_clase = pd.DataFrame(por_clase)
        df_clase['cantidad'] = pd.to_numeric(df_clase['cantidad'], errors='coerce')
        df_clase = df_clase.sort_values('cantidad', ascending=False)
        
        # Mostrar solo si hay variedad
        top_n = min(15, len(df_clase))
        df_clase_top = df_clase.head(top_n)
        
        fig = go.Figure()
        
        fig.add_trace(go.Bar(
            y=df_clase_top['clase'],
            x=df_clase_top['cantidad'],
            orientation='h',
            text=df_clase_top['cantidad'].apply(lambda x: f"{int(x):,}"),
            textposition='outside',
            marker=dict(
                color=df_clase_top['cantidad'],
                colorscale='Reds',
                showscale=False,
                line=dict(color='white', width=1)
            ),
            hovertemplate='<b>%{y}</b><br>Cantidad: %{x:,}<extra></extra>'
        ))
        
        fig.update_layout(
            title=f'Top {top_n} Clases de Trámites',
            xaxis_title='Cantidad de Trámites',
            yaxis_title='',
            height=max(400, top_n * 40),
            yaxis=dict(autorange="reversed")
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        with st.expander("📋 Ver todas las clases"):
            df_display = df_clase[['clase', 'cantidad']].copy()
            df_display.columns = ['Clase', 'Cantidad']
            df_display['Cantidad'] = df_display['Cantidad'].apply(lambda x: f"{int(x):,}")
            st.dataframe(df_display, use_container_width=True, hide_index=True)
    
    st.divider()
    
    # Top trámites más frecuentes
    st.subheader("🏆 Trámites Más Frecuentes")
    
    if top_tramites and len(top_tramites) > 0:
        df_top = pd.DataFrame(top_tramites)
        df_top['cantidad'] = pd.to_numeric(df_top['cantidad'], errors='coerce')
        df_top = df_top.sort_values('cantidad', ascending=False).head(10)
        
        # Acortar nombres para mejor visualización
        df_top['nombre_corto'] = df_top['nombre'].apply(
            lambda x: (str(x)[:50] + '...') if len(str(x)) > 50 else str(x)
        )
        
        fig = go.Figure()
        
        fig.add_trace(go.Bar(
            y=df_top['nombre_corto'],
            x=df_top['cantidad'],
            orientation='h',
            text=df_top['cantidad'].apply(lambda x: f"{int(x):,}"),
            textposition='outside',
            marker=dict(
                color=df_top['cantidad'],
                colorscale='Greens',
                showscale=False,
                line=dict(color='white', width=1)
            ),
            hovertemplate='<b>%{customdata}</b><br>Cantidad: %{x:,}<extra></extra>',
            customdata=df_top['nombre']
        ))
        
        fig.update_layout(
            title='Top 10 Trámites Más Solicitados',
            xaxis_title='Cantidad de Solicitudes',
            yaxis_title='',
            height=500,
            yaxis=dict(autorange="reversed")
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        with st.expander("📋 Ver nombres completos y detalles"):
            df_display_top = df_top[['nombre', 'cantidad']].copy()
            df_display_top.columns = ['Nombre del Trámite', 'Cantidad']
            df_display_top['Cantidad'] = df_display_top['Cantidad'].apply(lambda x: f"{int(x):,}")
            st.dataframe(df_display_top, use_container_width=True, hide_index=True)
    
    st.divider()
    
    # Exportación de datos
    st.subheader("📥 Exportar Datos")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("📊 Descargar Excel", use_container_width=True, type="primary"):
            output = BytesIO()
            with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                # Resumen general
                df_resumen = pd.DataFrame([{
                    'Total Registros': total_registros,
                    'Años': len(por_ano),
                    'Clases': len(por_clase),
                    'Categorías': len(distribucion_categorias)
                }])
                df_resumen.to_excel(writer, sheet_name='Resumen', index=False)
                
                # Por Año
                if por_ano:
                    pd.DataFrame(por_ano).to_excel(writer, sheet_name='Por Año', index=False)
                
                # Por Categoría
                if distribucion_categorias:
                    pd.DataFrame(distribucion_categorias).to_excel(writer, sheet_name='Por Categoría', index=False)
                
                # Por Clase
                if por_clase:
                    pd.DataFrame(por_clase).to_excel(writer, sheet_name='Por Clase', index=False)
                
                # Top Trámites
                if top_tramites:
                    pd.DataFrame(top_tramites).to_excel(writer, sheet_name='Top Trámites', index=False)
            
            st.download_button(
                label="⬇️ Descargar Excel",
                data=output.getvalue(),
                file_name=f"estadisticas_invima_{filtro_ano or 'todos'}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True
            )
    
    with col2:
        if st.button("📄 Descargar CSV", use_container_width=True):
            csv_parts = []
            
            # Resumen
            csv_parts.append(f"Total Registros,{total_registros}")
            csv_parts.append(f"Años,{len(por_ano)}")
            csv_parts.append(f"Clases,{len(por_clase)}")
            csv_parts.append(f"Categorías,{len(distribucion_categorias)}")
            csv_parts.append("\n")
            
            if por_ano:
                csv_parts.append("=== POR AÑO ===")
                csv_parts.append(pd.DataFrame(por_ano).to_csv(index=False))
            
            if distribucion_categorias:
                csv_parts.append("=== POR CATEGORÍA ===")
                csv_parts.append(pd.DataFrame(distribucion_categorias).to_csv(index=False))
            
            csv_data = "\n".join(csv_parts)
            
            st.download_button(
                label="⬇️ Descargar CSV",
                data=csv_data,
                file_name=f"estadisticas_invima_{filtro_ano or 'todos'}.csv",
                mime="text/csv",
                use_container_width=True
            )
    
    with col3:
        st.caption("💾 Exporta los datos para análisis externo o presentaciones")

else:
    st.error("❌ No se pudieron cargar las estadísticas")
    st.info("""
    **Verifica lo siguiente:**
    
    1. ✅ El backend de FastAPI debe estar corriendo en **http://localhost:8000**
    2. ✅ Puedes probar la API directamente en tu navegador: [http://localhost:8000/api/v1/dashboard/estadisticas-suit](http://localhost:8000/api/v1/dashboard/estadisticas-suit)
    3. ✅ Verifica que ambos servicios estén iniciados correctamente
    
    **Para iniciar los servicios:**
    
    **Terminal 1 (Backend FastAPI):**
    ```bash
    cd app
    uvicorn main:app --reload --port 8000
    ```
    
    **Terminal 2 (Frontend Streamlit):**
    ```bash
    cd streamlit_app
    streamlit run Home.py
    ```
    """)
    
    col1, col2 = st.columns([1, 3])
    with col1:
        if st.button("🔄 Reintentar", use_container_width=True):
            st.cache_data.clear()
            st.rerun()
    with col2:
        st.caption("Haz clic en 'Reintentar' después de verificar que los servicios estén corriendo")

# Información adicional
with st.expander("ℹ️ Acerca de estos datos"):
    st.markdown("""
    ### Fuente de Datos
    
    Los datos provienen del **Catálogo de Trámites del INVIMA** publicado en el portal de 
    Datos Abiertos de Colombia (Función Pública 2022).
    
    ### Actualización
    
    - **Frecuencia**: Los datos se consultan en tiempo real desde la API de Socrata
    - **Cache**: Se mantiene un caché de 5 minutos para optimizar el rendimiento
    - **Cobertura**: Registros de trámites del INVIMA en Bogotá D.C.
    
    ### Campos Analizados
    
    - **Año**: Año de registro del trámite
    - **Nombre del trámite**: Descripción completa del procedimiento
    - **Clase**: Clasificación del trámite
    - **Propósito**: Objetivo del trámite
    - **Categoría**: Clasificación automática basada en palabras clave
    
    ### Tecnologías
    
    - **Backend**: FastAPI + Socrata API
    - **Frontend**: Streamlit + Plotly
    - **Datos**: Portal Datos Abiertos Colombia
    """)

st.markdown("---")
st.markdown("*Dashboard INVIMA | Datos Abiertos Colombia | Actualizado 2025*")

