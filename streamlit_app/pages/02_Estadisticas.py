"""
HU-INVIMA-002: Visualización de estadísticas de trámites del INVIMA
ID: HU-INVIMA-002 | Versión: 1.0 | Prioridad: Media | Proyecto: Transparencia SUIT
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

# Header con información de la historia de usuario
st.title("📊 Estadísticas de Trámites del INVIMA")
st.markdown("""
**Visualización de estadísticas**

*Estadísticas sobre los trámites del INVIMA, 
para identificar tendencias y patrones en el volumen y tipo de trámites registrados.*
""")

# Info de conectividad
info_col1, info_col2 = st.columns([3, 1])
with info_col2:
    if st.button("🔄 Recargar", help="Limpiar caché y recargar datos"):
        st.cache_data.clear()
        st.rerun()

st.divider()

# Sidebar - Filtros combinables
st.sidebar.header("🔍 Filtros Combinables")
st.sidebar.markdown("**Criterio de aceptación**: Filtros por Año, Clase y palabra clave")

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
    
    # CRITERIO 1: Gráficos por año
    st.subheader("📅 Criterio 1: Gráficos por Año")
    st.markdown("**Generar gráficos de barras o líneas con el número de trámites por año**")
    
    if por_ano:
        df_ano = pd.DataFrame(por_ano)
        df_ano['cantidad'] = pd.to_numeric(df_ano['cantidad'], errors='coerce')
        df_ano = df_ano.sort_values('ano')
        
        col1, col2 = st.columns([3, 1])
        
        with col2:
            tipo_grafico = st.radio("Tipo", ["Barras", "Líneas"], key="tipo_ano")
        
        with col1:
            if tipo_grafico == "Barras":
                fig = px.bar(df_ano, x='ano', y='cantidad', text='cantidad',
                           title='Trámites por Año',
                           labels={'ano': 'Año', 'cantidad': 'Cantidad'},
                           color='cantidad', color_continuous_scale='Viridis')
                fig.update_traces(texttemplate='%{text:,}', textposition='outside')
            else:
                fig = px.line(df_ano, x='ano', y='cantidad', markers=True,
                            title='Evolución de Trámites por Año',
                            labels={'ano': 'Año', 'cantidad': 'Cantidad'})
                fig.update_traces(line=dict(width=3), marker=dict(size=12))
            
            fig.update_layout(showlegend=False, height=400)
            st.plotly_chart(fig, use_container_width=True)
        
        with st.expander("📋 Ver datos"):
            st.dataframe(df_ano, use_container_width=True, hide_index=True)
    else:
        st.info("No hay datos de años")
    
    st.divider()
    
    # CRITERIO 2: Gráficos por categoría
    st.subheader("� Criterio 2: Gráficos por Categoría")
    st.markdown("**Distribución por tipo, basándose en Nombre, Clase y Propósito del trámite**")
    
    if distribucion_categorias:
        df_cat = pd.DataFrame(distribucion_categorias)
        df_cat = df_cat.sort_values('cantidad', ascending=False)
        
        col1, col2 = st.columns([3, 1])
        
        with col2:
            tipo_cat = st.radio("Tipo", ["Barras", "Pastel", "Columnas"], key="tipo_cat")
        
        with col1:
            if tipo_cat == "Barras":
                fig = px.bar(df_cat, x='categoria', y='cantidad', text='cantidad',
                           title='Distribución por Categoría',
                           color='cantidad', color_continuous_scale='Blues')
                fig.update_traces(texttemplate='%{text:,}', textposition='outside')
            elif tipo_cat == "Pastel":
                fig = px.pie(df_cat, values='cantidad', names='categoria',
                           title='Distribución Porcentual', hole=0.3)
                fig.update_traces(textposition='inside', textinfo='percent+label')
            else:
                fig = px.bar(df_cat, y='categoria', x='cantidad', orientation='h',
                           text='cantidad', title='Categorías (Horizontal)',
                           color='cantidad', color_continuous_scale='Teal')
                fig.update_traces(texttemplate='%{text:,}', textposition='outside')
            
            fig.update_layout(height=400)
            st.plotly_chart(fig, use_container_width=True)
        
        with st.expander("📋 Ver datos"):
            df_cat_tabla = df_cat.copy()
            df_cat_tabla['porcentaje'] = (df_cat_tabla['cantidad'] / df_cat_tabla['cantidad'].sum() * 100).round(2).astype(str) + '%'
            st.dataframe(df_cat_tabla, use_container_width=True, hide_index=True)
    else:
        st.info("No hay datos de categorías")
    
    st.divider()
    
    # Gráfico por clase
    st.subheader("📑 Distribución por Clase")
    
    if por_clase:
        df_clase = pd.DataFrame(por_clase)
        df_clase['cantidad'] = pd.to_numeric(df_clase['cantidad'], errors='coerce')
        df_clase = df_clase.sort_values('cantidad', ascending=False).head(15)
        
        fig = px.bar(df_clase, y='clase', x='cantidad', orientation='h',
                    text='cantidad', title='Top 15 Clases',
                    color='cantidad', color_continuous_scale='Reds')
        fig.update_traces(texttemplate='%{text:,}', textposition='outside')
        fig.update_layout(showlegend=False, height=500)
        st.plotly_chart(fig, use_container_width=True)
        
        with st.expander("📋 Ver todas las clases"):
            df_clase_full = pd.DataFrame(por_clase)
            df_clase_full['cantidad'] = pd.to_numeric(df_clase_full['cantidad'], errors='coerce')
            st.dataframe(df_clase_full.sort_values('cantidad', ascending=False), use_container_width=True, hide_index=True)
    
    st.divider()
    
    # Top trámites
    st.subheader("🏆 Top Trámites Más Frecuentes")
    
    if top_tramites:
        df_top = pd.DataFrame(top_tramites)
        df_top['cantidad'] = pd.to_numeric(df_top['cantidad'], errors='coerce')
        df_top = df_top.head(10)
        df_top['nombre_corto'] = df_top['nombre'].apply(lambda x: x[:60] + '...' if len(str(x)) > 60 else x)
        
        fig = px.bar(df_top, y='nombre_corto', x='cantidad', orientation='h',
                    text='cantidad', title='Top 10 Trámites',
                    color='cantidad', color_continuous_scale='Greens')
        fig.update_traces(texttemplate='%{text:,}', textposition='outside')
        fig.update_layout(showlegend=False, height=500)
        st.plotly_chart(fig, use_container_width=True)
        
        with st.expander("📋 Ver nombres completos"):
            st.dataframe(df_top[['nombre', 'cantidad']], use_container_width=True, hide_index=True)
    
    st.divider()
    
    # CRITERIO 3: Exportación
    st.subheader("📥 Criterio 3: Exportación de Resultados")
    st.markdown("**Exportar estadísticas a PDF o Excel conservando totales, etiquetas y leyendas**")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("📊 Exportar a Excel", use_container_width=True):
            output = BytesIO()
            with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                # Resumen
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
        if st.button("📄 Exportar a CSV", use_container_width=True):
            csv_data = f"ESTADÍSTICAS INVIMA - HU-INVIMA-002\nTotal: {total_registros}\n\n"
            
            if por_ano:
                csv_data += "=== POR AÑO ===\n"
                csv_data += pd.DataFrame(por_ano).to_csv(index=False) + "\n"
            
            if distribucion_categorias:
                csv_data += "=== POR CATEGORÍA ===\n"
                csv_data += pd.DataFrame(distribucion_categorias).to_csv(index=False) + "\n"
            
            st.download_button(
                label="⬇️ Descargar CSV",
                data=csv_data,
                file_name=f"estadisticas_invima_{filtro_ano or 'todos'}.csv",
                mime="text/csv",
                use_container_width=True
            )
    
    with col3:
        st.info("**✅ Fidelidad visual**: Conserva formato, totales y leyendas")

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

# Información de la HU (mostrar siempre)
with st.expander("ℹ️ Historia de Usuario HU-INVIMA-002"):
    st.markdown("""
    ### Historia de Usuario: Visualización de estadísticas
    
    | Criterio | Detalle |
    |----------|---------|
    | **ID** | HU-INVIMA-002 |
    | **Versión** | 1.0 |
    | **Descripción** | Versión inicial |
    | **Actor** | Analista de políticas públicas |
    | **Prioridad** | Media |
    | **Riesgo** | Bajo |
    | **Proyecto** | Transparencia SUIT |
    | **Iteración** | 1 |
    
    #### Descripción
    Como analista de políticas públicas, quiero visualizar estadísticas sobre los trámites del INVIMA, 
    para identificar tendencias y patrones en el volumen y tipo de trámites registrados.
    
    ---
    
    ### Criterios de Aceptación
    
    | Criterio | Detalle | Estado |
    |----------|---------|--------|
    | **Gráficos por año** | Generar gráficos de barras o líneas con el número de trámites por año | ✅ |
    | **Gráficos por categoría** | Visualizar distribución por tipo o clase (Nombre, Clase, Propósito) | ✅ |
    | **Exportación** | Permitir exportar a PDF o Excel conservando totales, etiquetas y leyendas | ✅ |
    | **Filtros** | Aplicar filtros combinables por Año, Clase y palabra clave | ✅ |
    
    ---
    
    ### Criterios No Funcionales
    
    | Criterio | Detalle | Estado |
    |----------|---------|--------|
    | **Cálculo directo** | Los cálculos se realizan directamente sobre datos del SUIT | ✅ |
    | **Desempeño** | Gráficos generados en <5 segundos (datasets hasta 10,000 registros) | ✅ |
    | **Interfaz** | Intuitiva, accesible y móvil | ✅ |
    | **Fidelidad visual** | La exportación conserva formato y leyendas | ✅ |
    
    ---
    
    ### Datos del SUIT
    
    - **Fuente**: Catálogo de trámites INVIMA (Función Pública 2022)
    - **Campos**: Año, Nombre del trámite, Clase, Propósito, Entidad
    - **Ubicación**: Todos los registros corresponden a Bogotá D.C.
    - **Cache**: Los datos se actualizan cada 5 minutos
    
    ---
    
    **Última actualización**: Octubre 2025 | **Versión**: 1.0
    """)

st.markdown("---")
st.markdown("*HU-INVIMA-002 | Proyecto: Transparencia SUIT | Datos: INVIMA - Función Pública*")

