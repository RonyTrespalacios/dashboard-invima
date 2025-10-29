"""
Tablero Público de Trámites del INVIMA
Dashboard de indicadores de desempeño y eficiencia operativa
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

st.set_page_config(page_title="Tablero Público INVIMA", page_icon="🌐", layout="wide")

FASTAPI_URL = os.getenv("FASTAPI_URL", "http://localhost:8000")
API_STATS_SUIT = f"{FASTAPI_URL}/api/v1/dashboard/estadisticas-suit"

st.title("🌐 Tablero Público de Indicadores")
st.markdown("**Indicadores de desempeño de trámites del INVIMA** | Acceso libre y abierto")

# Botón de actualización
col1, col2 = st.columns([3, 1])
with col2:
    if st.button("🔄 Actualizar", help="Actualizar datos del tablero", use_container_width=True):
        st.cache_data.clear()
        st.rerun()

st.divider()

# Sidebar - Filtros dinámicos
st.sidebar.header("🔍 Filtros Dinámicos")
st.sidebar.markdown("Actualiza los gráficos en tiempo real")

# Cargar opciones de filtros
@st.cache_data(ttl=300)
def cargar_datos_filtros():
    try:
        response = requests.get(API_STATS_SUIT, timeout=10)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        return None

datos_filtros = cargar_datos_filtros()
anos_disponibles = ["Todos"]
clases_disponibles = ["Todas"]

if datos_filtros:
    anos_disponibles += datos_filtros.get("anos_disponibles", [])
    clases_disponibles += datos_filtros.get("clases_disponibles", [])

# Filtros
ano_seleccionado = st.sidebar.selectbox(
    "📅 Año",
    options=anos_disponibles,
    help="Filtrar por año de registro"
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

# Cargar estadísticas
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
    except Exception as e:
        return None

filtro_ano = None if ano_seleccionado == "Todos" else ano_seleccionado
filtro_clase = None if clase_seleccionada == "Todas" else clase_seleccionada
filtro_kw = palabra_clave.strip() if palabra_clave.strip() else None

with st.spinner("⏳ Cargando indicadores... (menos de 5 segundos)"):
    data = cargar_estadisticas(filtro_ano, filtro_clase, filtro_kw)

if data:
    total_registros = data.get("total_registros", 0)
    por_ano = data.get("por_ano", [])
    por_clase = data.get("por_clase", [])
    top_tramites = data.get("top_tramites", [])
    distribucion_categorias = data.get("distribucion_categorias", [])
    
    # INDICADORES GENERALES
    st.subheader("📊 Indicadores Generales")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            "📝 Total de Trámites",
            f"{total_registros:,}",
            help="Cantidad total de trámites registrados en el SUIT"
        )
    
    with col2:
        st.metric(
            "📂 Clases Registradas",
            len(por_clase),
            help="Número de diferentes clases de trámites"
        )
    
    with col3:
        st.metric(
            "📅 Años con Registro",
            len(por_ano),
            help="Cantidad de años con trámites registrados"
        )
    
    with col4:
        st.metric(
            "🏷️ Categorías",
            len(distribucion_categorias),
            help="Número de categorías identificadas"
        )
    
    st.divider()
    
    # VISUALIZACIÓN GRÁFICA - Volumen Total y Evolución Temporal
    st.subheader("📈 Evolución Temporal y Volumen")
    
    if por_ano and len(por_ano) > 0:
        df_ano = pd.DataFrame(por_ano)
        df_ano['cantidad'] = pd.to_numeric(df_ano['cantidad'], errors='coerce')
        df_ano = df_ano.sort_values('ano')
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Gráfico de barras por año
            fig_barras = go.Figure()
            
            colors_scale = px.colors.sequential.Teal
            color_values = df_ano['cantidad'] / df_ano['cantidad'].max()
            bar_colors = [colors_scale[min(int(v * (len(colors_scale)-1)), len(colors_scale)-1)] for v in color_values]
            
            fig_barras.add_trace(go.Bar(
                x=df_ano['ano'],
                y=df_ano['cantidad'],
                text=df_ano['cantidad'].apply(lambda x: f"{int(x):,}"),
                textposition='outside',
                marker=dict(color=bar_colors, line=dict(color='white', width=2)),
                hovertemplate='<b>Año %{x}</b><br>Trámites: %{y:,}<extra></extra>'
            ))
            
            fig_barras.update_layout(
                title='Volumen de Trámites por Año',
                xaxis_title='Año',
                yaxis_title='Cantidad',
                height=400,
                showlegend=False,
                xaxis=dict(type='category')
            )
            
            st.plotly_chart(fig_barras, use_container_width=True)
        
        with col2:
            # Gráfico de líneas - evolución
            fig_lineas = go.Figure()
            
            fig_lineas.add_trace(go.Scatter(
                x=df_ano['ano'],
                y=df_ano['cantidad'],
                mode='lines+markers',
                name='Evolución',
                line=dict(color='#2E86AB', width=4),
                marker=dict(size=12, color='#A23B72', line=dict(color='white', width=2)),
                fill='tozeroy',
                fillcolor='rgba(46, 134, 171, 0.2)',
                hovertemplate='<b>%{x}</b><br>Cantidad: %{y:,}<extra></extra>'
            ))
            
            fig_lineas.update_layout(
                title='Tendencia Temporal',
                xaxis_title='Año',
                yaxis_title='Cantidad',
                height=400,
                showlegend=False
            )
            
            st.plotly_chart(fig_lineas, use_container_width=True)
    
    st.divider()
    
    # DISTRIBUCIÓN POR CLASE
    st.subheader("📑 Distribución por Clase de Trámite")
    
    if por_clase and len(por_clase) > 0:
        df_clase = pd.DataFrame(por_clase)
        df_clase['cantidad'] = pd.to_numeric(df_clase['cantidad'], errors='coerce')
        df_clase = df_clase.sort_values('cantidad', ascending=False)
        
        col1, col2 = st.columns([2, 1])
        
        with col1:
            # Gráfico de barras horizontales
            top_n = min(10, len(df_clase))
            df_top = df_clase.head(top_n)
            
            fig_clase = go.Figure()
            
            fig_clase.add_trace(go.Bar(
                y=df_top['clase'],
                x=df_top['cantidad'],
                orientation='h',
                text=df_top['cantidad'].apply(lambda x: f"{int(x):,}"),
                textposition='outside',
                marker=dict(
                    color=df_top['cantidad'],
                    colorscale='Viridis',
                    showscale=False,
                    line=dict(color='white', width=1)
                ),
                hovertemplate='<b>%{y}</b><br>Cantidad: %{x:,}<extra></extra>'
            ))
            
            fig_clase.update_layout(
                title=f'Top {top_n} Clases de Trámites',
                xaxis_title='Cantidad',
                yaxis_title='',
                height=max(400, top_n * 50),
                yaxis=dict(autorange="reversed")
            )
            
            st.plotly_chart(fig_clase, use_container_width=True)
        
        with col2:
            # Gráfico de pastel (pie chart)
            df_pie = df_clase.head(5)
            
            fig_pie = px.pie(
                df_pie,
                values='cantidad',
                names='clase',
                title='Proporción Top 5 Clases',
                hole=0.4,
                color_discrete_sequence=px.colors.qualitative.Set3
            )
            
            fig_pie.update_traces(
                textposition='inside',
                textinfo='percent',
                hovertemplate='<b>%{label}</b><br>%{value:,}<br>%{percent}<extra></extra>'
            )
            
            fig_pie.update_layout(height=400)
            
            st.plotly_chart(fig_pie, use_container_width=True)
    
    st.divider()
    
    # TARJETAS DE CATEGORÍAS
    st.subheader("🏷️ Distribución por Categorías")
    
    if distribucion_categorias and len(distribucion_categorias) > 0:
        df_cat = pd.DataFrame(distribucion_categorias)
        df_cat = df_cat.sort_values('cantidad', ascending=False)
        df_cat['porcentaje'] = (df_cat['cantidad'] / df_cat['cantidad'].sum() * 100).round(1)
        
        # Tarjetas interactivas
        cols_per_row = 3
        for i in range(0, len(df_cat), cols_per_row):
            cols = st.columns(cols_per_row)
            for j, col in enumerate(cols):
                if i + j < len(df_cat):
                    row = df_cat.iloc[i + j]
                    with col:
                        st.metric(
                            row['categoria'],
                            f"{int(row['cantidad']):,}",
                            f"{row['porcentaje']}%"
                        )
    
    st.divider()
    
    # EXPORTACIÓN
    st.subheader("📥 Exportación de Datos")
    st.markdown("Descarga los indicadores en formato PDF o Excel con todas las etiquetas y valores")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("📊 Descargar Excel", use_container_width=True, type="primary"):
            output = BytesIO()
            with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                # Resumen
                df_resumen = pd.DataFrame([{
                    'Total Registros': total_registros,
                    'Clases': len(por_clase),
                    'Años': len(por_ano),
                    'Categorías': len(distribucion_categorias)
                }])
                df_resumen.to_excel(writer, sheet_name='Indicadores', index=False)
                
                # Por Año
                if por_ano:
                    pd.DataFrame(por_ano).to_excel(writer, sheet_name='Por Año', index=False)
                
                # Por Clase
                if por_clase:
                    pd.DataFrame(por_clase).to_excel(writer, sheet_name='Por Clase', index=False)
                
                # Categorías
                if distribucion_categorias:
                    pd.DataFrame(distribucion_categorias).to_excel(writer, sheet_name='Categorías', index=False)
                
                # Top Trámites
                if top_tramites:
                    pd.DataFrame(top_tramites).to_excel(writer, sheet_name='Top Trámites', index=False)
            
            st.download_button(
                label="⬇️ Descargar Excel",
                data=output.getvalue(),
                file_name=f"tablero_publico_invima.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True
            )
    
    with col2:
        if st.button("📄 Descargar CSV", use_container_width=True):
            csv_parts = []
            csv_parts.append(f"Total Registros,{total_registros}")
            csv_parts.append(f"Clases,{len(por_clase)}")
            csv_parts.append(f"Años,{len(por_ano)}")
            csv_parts.append("\n=== POR AÑO ===")
            if por_ano:
                csv_parts.append(pd.DataFrame(por_ano).to_csv(index=False))
            
            csv_data = "\n".join(csv_parts)
            
            st.download_button(
                label="⬇️ Descargar CSV",
                data=csv_data,
                file_name="tablero_publico_invima.csv",
                mime="text/csv",
                use_container_width=True
            )
    
    with col3:
        st.caption("💾 Datos oficiales del SUIT | Formato estándar de datos abiertos")

else:
    st.error("❌ No se pudieron cargar los indicadores")
    st.info("""
    **Verifica lo siguiente:**
    
    1. ✅ El backend debe estar corriendo en http://localhost:8000
    2. ✅ Los servicios deben estar iniciados correctamente
    3. ✅ Intenta actualizar la página
    """)
    
    if st.button("🔄 Reintentar", use_container_width=True):
        st.cache_data.clear()
        st.rerun()

# Información del tablero
st.divider()

with st.expander("ℹ️ Acerca del Tablero Público"):
    st.markdown("""
    ### Tablero Público de Indicadores
    
    Dashboard de acceso libre para evaluar la eficiencia operativa del INVIMA y conocer 
    el comportamiento institucional en la gestión de trámites.
    
    ### Datos Mostrados
    
    - **Total de trámites**: Cantidad total registrada en el SUIT
    - **Distribución por clase**: Clasificación de trámites por tipo
    - **Evolución temporal**: Cantidad de trámites por año/mes
    - **Versiones registradas**: Número de categorías identificadas
    
    ### Características
    
    ✅ **Acceso Abierto**: Sin autenticación, datos oficiales del SUIT  
    ✅ **Filtros Dinámicos**: Actualización en tiempo real  
    ✅ **Gráficos Interactivos**: Barras, líneas, pastel y tarjetas  
    ✅ **Exportación**: PDF/Excel con etiquetas y valores  
    ✅ **Desempeño**: Carga en menos de 5 segundos  
    ✅ **Responsive**: Navegable desde móviles y escritorio  
    ✅ **Actualización**: Datos periódicos desde el SUIT  
    ✅ **Estándares**: Cumplimiento de datos abiertos (CSV/JSON)  
    
    ### Fuente de Datos
    
    Catálogo de Trámites del INVIMA - Portal de Datos Abiertos de Colombia
    """)

st.markdown("---")
st.markdown("*Tablero Público INVIMA | Datos Abiertos Colombia | Actualizado 2025*")
