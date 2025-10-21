"""
HU04: Descarga de Datos Abiertos
"""
import streamlit as st
import requests
import pandas as pd
import os

st.set_page_config(page_title="Datos Abiertos", page_icon="📥", layout="wide")

FASTAPI_URL = os.getenv("FASTAPI_URL", "http://localhost:8000")
API_DATOS = f"{FASTAPI_URL}/api/v1/public/datos-abiertos"

st.title("📥 Descarga de Datos Abiertos")
st.markdown("Descarga datasets completos en formato JSON o CSV")

# Información principal
st.info("""
🔓 **Datos Abiertos del INVIMA**

Accede a los datos públicos de trámites del INVIMA en formatos estándar 
para análisis, investigación o desarrollo de aplicaciones.
""")

# Configuración de descarga
st.subheader("⚙️ Configurar Descarga")

col1, col2 = st.columns(2)

with col1:
    formato = st.selectbox(
        "Formato de descarga",
        options=["json", "csv"],
        format_func=lambda x: "JSON (.json)" if x == "json" else "CSV (.csv)",
        help="Selecciona el formato del archivo a descargar"
    )

with col2:
    limit = st.number_input(
        "Cantidad de registros",
        min_value=100,
        max_value=10000,
        value=1000,
        step=100,
        help="Máximo de registros a descargar"
    )

st.divider()

# Previsualización
st.subheader("👀 Previsualización")

if st.button("🔍 Cargar Vista Previa (100 registros)", use_container_width=True):
    with st.spinner("Cargando previsualización..."):
        try:
            response = requests.get(
                API_DATOS,
                params={"formato": "json", "limit": 100}
            )
            response.raise_for_status()
            data = response.json()
            
            if data.get('datos'):
                df_preview = pd.DataFrame(data['datos'])
                
                st.success(f"✅ Se cargaron {len(df_preview)} registros de muestra")
                
                # Mostrar información del dataset
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Registros", len(df_preview))
                with col2:
                    st.metric("Columnas", len(df_preview.columns))
                with col3:
                    # Calcular tamaño aproximado
                    size_kb = df_preview.memory_usage(deep=True).sum() / 1024
                    st.metric("Tamaño Aprox.", f"{size_kb:.1f} KB")
                
                # Mostrar tabla
                st.dataframe(df_preview, use_container_width=True, hide_index=True)
                
                # Información de columnas
                with st.expander("📋 Información de Columnas"):
                    col_info = pd.DataFrame({
                        'Columna': df_preview.columns,
                        'Tipo': df_preview.dtypes.astype(str),
                        'No Nulos': df_preview.count(),
                        'Valores Únicos': df_preview.nunique()
                    })
                    st.dataframe(col_info, use_container_width=True)
            else:
                st.warning("No se encontraron datos")
                
        except Exception as e:
            st.error(f"❌ Error al cargar previsualización: {str(e)}")

st.divider()

# Descarga completa
st.subheader("💾 Descargar Dataset Completo")

st.warning(f"⚠️ Estás a punto de descargar hasta {limit:,} registros en formato {formato.upper()}")

if st.button("📥 DESCARGAR AHORA", type="primary", use_container_width=True):
    with st.spinner(f"Generando archivo {formato.upper()}..."):
        try:
            if formato == "csv":
                # Descargar CSV
                response = requests.get(
                    API_DATOS,
                    params={"formato": "csv", "limit": limit}
                )
                response.raise_for_status()
                
                st.download_button(
                    label="📥 Descargar archivo CSV",
                    data=response.content,
                    file_name=f"invima_datos_{limit}.csv",
                    mime="text/csv",
                    use_container_width=True
                )
                st.success("✅ ¡Archivo CSV listo para descargar!")
                
            else:
                # Descargar JSON
                response = requests.get(
                    API_DATOS,
                    params={"formato": "json", "limit": limit}
                )
                response.raise_for_status()
                data = response.json()
                
                import json
                json_str = json.dumps(data, indent=2, ensure_ascii=False)
                
                st.download_button(
                    label="📥 Descargar archivo JSON",
                    data=json_str,
                    file_name=f"invima_datos_{limit}.json",
                    mime="application/json",
                    use_container_width=True
                )
                st.success("✅ ¡Archivo JSON listo para descargar!")
                
        except Exception as e:
            st.error(f"❌ Error al generar descarga: {str(e)}")

st.divider()

# Información sobre datos abiertos
with st.expander("📖 Información sobre Datos Abiertos"):
    st.markdown("""
    ### ¿Qué son los Datos Abiertos?
    
    Los datos abiertos son datos públicos que pueden ser utilizados, reutilizados 
    y redistribuidos libremente por cualquier persona.
    
    ### Formatos Disponibles
    
    - **JSON**: Formato ideal para desarrollo de aplicaciones y APIs
    - **CSV**: Formato ideal para análisis en Excel, R, Python, etc.
    
    ### Casos de Uso
    
    - Análisis estadístico
    - Investigación académica
    - Desarrollo de aplicaciones
    - Visualización de datos
    - Machine Learning
    
    ### Licencia
    
    Los datos están bajo la política de datos abiertos del gobierno colombiano.
    Consulta los términos de uso en [datos.gov.co](https://www.datos.gov.co)
    
    ### Limitaciones
    
    - Máximo 10,000 registros por descarga
    - Los datos se actualizan periódicamente
    - Información de carácter público únicamente
    
    ### Fuente
    
    Portal de Datos Abiertos Colombia - INVIMA  
    API: Socrata Open Data
    """)

# Tips de uso
st.info("""
💡 **Tips de Uso**

- Para análisis en Excel: Descarga en formato **CSV**
- Para desarrollo de apps: Descarga en formato **JSON**
- Usa la previsualización para verificar los datos antes de descargar
- Si necesitas más de 10,000 registros, descarga en lotes
""")
