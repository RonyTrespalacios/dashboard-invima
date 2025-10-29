"""
HU05: Visualización de Reportes de Errores (Datos Anónimos)
Interfaz de administración para consultar reportes sin exponer datos personales
"""
import streamlit as st
import requests
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import os
from typing import Dict, List

st.set_page_config(page_title="Reportes de Errores", page_icon="📊", layout="wide")

FASTAPI_URL = os.getenv("FASTAPI_URL", "http://localhost:8000")
API_REPORTES = f"{FASTAPI_URL}/api/v1/reportes/listar"

st.title("📊 Reportes de Errores")
st.markdown("Visualización de reportes con datos anónimos para análisis y seguimiento")

# Controles
col1, col2 = st.columns([1, 4])
# with col1:
#     if st.button("🔄 Actualizar", type="primary", use_container_width=True):
#         st.rerun()

with col2:
    st.caption(f"⏰ Última actualización: {datetime.now().strftime('%H:%M:%S')}")

st.divider()

# Función para anonimizar datos
def anonimizar_datos(reportes: List[Dict]) -> List[Dict]:
    """
    Anonimiza los datos personales de los reportes manteniendo la información útil
    """
    reportes_anonimos = []
    
    for i, reporte in enumerate(reportes):
        # Generar identificador anónimo basado en el índice
        usuario_id = f"Usuario_{i+1:03d}"
        
        # Extraer dominio del email para análisis (sin exponer el email completo)
        email_dominio = "Desconocido"
        if reporte.get("email"):
            try:
                email_dominio = reporte["email"].split("@")[1] if "@" in reporte["email"] else "Desconocido"
            except:
                email_dominio = "Desconocido"
        
        reporte_anonimo = {
            "usuario_id": usuario_id,
            "email_dominio": email_dominio,
            "tipo_error": reporte.get("tipo_error", "No especificado"),
            "descripcion": reporte.get("descripcion", ""),
            "numero_radicado": reporte.get("numero_radicado"),
            "fecha_reporte": reporte.get("fecha_reporte", ""),
            "reporte_id": reporte.get("reporte_id", ""),
            "tiene_radicado": "Sí" if reporte.get("numero_radicado") else "No"
        }
        reportes_anonimos.append(reporte_anonimo)
    
    return reportes_anonimos

# Función para obtener estadísticas
def obtener_estadisticas(reportes: List[Dict]) -> Dict:
    """
    Calcula estadísticas de los reportes
    """
    if not reportes:
        return {
            "total_reportes": 0,
            "por_tipo": {},
            "por_dominio": {},
            "con_radicado": 0,
            "sin_radicado": 0,
            "ultimos_7_dias": 0,
            "ultimos_30_dias": 0
        }
    
    # Contadores
    por_tipo = {}
    por_dominio = {}
    con_radicado = 0
    sin_radicado = 0
    ultimos_7_dias = 0
    ultimos_30_dias = 0
    
    fecha_actual = datetime.now()
    fecha_7_dias = fecha_actual - timedelta(days=7)
    fecha_30_dias = fecha_actual - timedelta(days=30)
    
    for reporte in reportes:
        # Por tipo de error
        tipo = reporte.get("tipo_error", "No especificado")
        por_tipo[tipo] = por_tipo.get(tipo, 0) + 1
        
        # Por dominio de email
        dominio = reporte.get("email_dominio", "Desconocido")
        por_dominio[dominio] = por_dominio.get(dominio, 0) + 1
        
        # Con/sin radicado
        if reporte.get("numero_radicado"):
            con_radicado += 1
        else:
            sin_radicado += 1
        
        # Por fecha
        try:
            fecha_reporte = datetime.fromisoformat(reporte.get("fecha_reporte", "").replace("Z", "+00:00"))
            if fecha_reporte >= fecha_7_dias:
                ultimos_7_dias += 1
            if fecha_reporte >= fecha_30_dias:
                ultimos_30_dias += 1
        except:
            pass
    
    return {
        "total_reportes": len(reportes),
        "por_tipo": por_tipo,
        "por_dominio": por_dominio,
        "con_radicado": con_radicado,
        "sin_radicado": sin_radicado,
        "ultimos_7_dias": ultimos_7_dias,
        "ultimos_30_dias": ultimos_30_dias
    }

# Cargar datos sin caché
def cargar_reportes():
    """
    Carga los reportes desde la API sin caché
    """
    try:
        # Agregar parámetro timestamp para evitar caché del navegador
        import time
        url = f"{API_REPORTES}?_t={int(time.time())}"
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()
        return data.get("reportes", [])
    except Exception as e:
        st.error(f"Error al cargar reportes: {str(e)}")
        return []

# Cargar reportes
with st.spinner("Cargando reportes..."):
    reportes_raw = cargar_reportes()

if not reportes_raw:
    st.warning("No hay reportes disponibles")
    st.stop()

# Anonimizar datos
reportes_anonimos = anonimizar_datos(reportes_raw)
estadisticas = obtener_estadisticas(reportes_anonimos)

# Sidebar con filtros
st.sidebar.header("🔍 Filtros")

# Filtro por tipo de error
tipos_disponibles = ["Todos"] + list(set([r["tipo_error"] for r in reportes_anonimos]))
tipo_seleccionado = st.sidebar.selectbox("Tipo de Error", tipos_disponibles)

# Filtro por dominio de email
dominios_disponibles = ["Todos"] + list(set([r["email_dominio"] for r in reportes_anonimos]))
dominio_seleccionado = st.sidebar.selectbox("Dominio de Email", dominios_disponibles)

# Filtro por radicado
radicado_filtro = st.sidebar.selectbox("Con Radicado", ["Todos", "Sí", "No"])

# Aplicar filtros
reportes_filtrados = reportes_anonimos.copy()

if tipo_seleccionado != "Todos":
    reportes_filtrados = [r for r in reportes_filtrados if r["tipo_error"] == tipo_seleccionado]

if dominio_seleccionado != "Todos":
    reportes_filtrados = [r for r in reportes_filtrados if r["email_dominio"] == dominio_seleccionado]

if radicado_filtro != "Todos":
    valor_radicado = "Sí" if radicado_filtro == "Sí" else "No"
    reportes_filtrados = [r for r in reportes_filtrados if r["tiene_radicado"] == valor_radicado]

# Estadísticas principales
st.header("📈 Estadísticas Generales")

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric(
        label="Total Reportes",
        value=estadisticas["total_reportes"],
        delta=f"{estadisticas['ultimos_7_dias']} últimos 7 días"
    )

with col2:
    st.metric(
        label="Con Radicado",
        value=estadisticas["con_radicado"],
        delta=f"{estadisticas['con_radicado']/max(estadisticas['total_reportes'], 1)*100:.1f}%"
    )

with col3:
    st.metric(
        label="Últimos 7 días",
        value=estadisticas["ultimos_7_dias"],
        delta=f"{estadisticas['ultimos_30_dias']} últimos 30 días"
    )

with col4:
    st.metric(
        label="Reportes Filtrados",
        value=len(reportes_filtrados),
        delta=f"{len(reportes_filtrados)} de {len(reportes_anonimos)}"
    )

# Gráficos
st.header("📊 Visualizaciones")

col1, col2 = st.columns(2)

with col1:
    # Gráfico de tipos de error
    if estadisticas["por_tipo"]:
        fig_tipos = px.pie(
            values=list(estadisticas["por_tipo"].values()),
            names=list(estadisticas["por_tipo"].keys()),
            title="Distribución por Tipo de Error"
        )
        st.plotly_chart(fig_tipos, use_container_width=True)

with col2:
    # Gráfico de dominios de email
    if estadisticas["por_dominio"]:
        fig_dominios = px.bar(
            x=list(estadisticas["por_dominio"].keys()),
            y=list(estadisticas["por_dominio"].values()),
            title="Reportes por Dominio de Email",
            labels={"x": "Dominio", "y": "Cantidad"}
        )
        fig_dominios.update_layout(xaxis_tickangle=45)
        st.plotly_chart(fig_dominios, use_container_width=True)

# Tabla de reportes filtrados
st.header(f"📋 Reportes ({len(reportes_filtrados)} encontrados)")

if reportes_filtrados:
    # Crear DataFrame para la tabla
    df_reportes = pd.DataFrame(reportes_filtrados)
    
    # Reordenar columnas
    columnas_ordenadas = [
        "reporte_id", "usuario_id", "tipo_error", "email_dominio", 
        "tiene_radicado", "numero_radicado", "fecha_reporte", "descripcion"
    ]
    df_reportes = df_reportes[columnas_ordenadas]
    
    # Renombrar columnas para mejor visualización
    df_reportes.columns = [
        "ID Reporte", "Usuario", "Tipo Error", "Dominio Email",
        "Con Radicado", "Número Radicado", "Fecha", "Descripción"
    ]
    
    # Formatear fecha
    df_reportes["Fecha"] = pd.to_datetime(df_reportes["Fecha"]).dt.strftime("%Y-%m-%d %H:%M")
    
    # Mostrar tabla
    st.dataframe(
        df_reportes,
        use_container_width=True,
        hide_index=True,
        height=400
    )
    
    # Opciones de descarga
    st.subheader("💾 Exportar Datos")
    
    col1, col2 = st.columns(2)
    
    with col1:
        csv_data = df_reportes.to_csv(index=False)
        st.download_button(
            label="📥 Descargar CSV",
            data=csv_data,
            file_name=f"reportes_anonimos_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
            mime="text/csv"
        )
    
    with col2:
        json_data = df_reportes.to_json(orient="records", indent=2)
        st.download_button(
            label="📥 Descargar JSON",
            data=json_data,
            file_name=f"reportes_anonimos_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
            mime="application/json"
        )

else:
    st.info("No hay reportes que coincidan con los filtros seleccionados")

# Información sobre privacidad
st.sidebar.markdown("---")
st.sidebar.info("""
🔒 **Privacidad**

Los datos mostrados están anonimizados:
- Nombres reemplazados por IDs
- Emails mostrados solo por dominio
- Información personal protegida
""")

# Footer
st.markdown("---")
st.caption("📊 Vista de administración - Datos anonimizados para protección de privacidad")
