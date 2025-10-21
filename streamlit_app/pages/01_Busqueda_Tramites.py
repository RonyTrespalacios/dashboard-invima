"""
HU01: Búsqueda de Trámites
"""
import streamlit as st
import requests
import pandas as pd
import os

st.set_page_config(page_title="Búsqueda de Trámites", page_icon="🔍", layout="wide")

FASTAPI_URL = os.getenv("FASTAPI_URL", "http://localhost:8000")
API_ENDPOINT = f"{FASTAPI_URL}/api/v1/tramites/buscar"

st.title("🔍 Búsqueda de Trámites")
st.markdown("Busca trámites del INVIMA por diferentes criterios")

# Formulario de búsqueda
with st.form("form_busqueda"):
    col1, col2 = st.columns(2)
    
    with col1:
        radicado = st.text_input("Número de Radicado", placeholder="Ej: 20230001234")
        estado = st.text_input("Estado", placeholder="Ej: APROBADO, EN REVISIÓN")
    
    with col2:
        fecha_inicio = st.date_input("Fecha Inicio")
        fecha_fin = st.date_input("Fecha Fin")
    
    col_limit, col_offset = st.columns(2)
    with col_limit:
        limit = st.number_input("Límite de resultados", min_value=1, max_value=1000, value=100)
    with col_offset:
        offset = st.number_input("Offset", min_value=0, value=0, step=100)
    
    submitted = st.form_submit_button("🔍 Buscar", use_container_width=True)

# Ejecutar búsqueda
if submitted:
    with st.spinner("Buscando trámites..."):
        try:
            params = {
                "limit": limit,
                "offset": offset
            }
            
            if radicado:
                params["radicado"] = radicado
            if estado:
                params["estado"] = estado
            if fecha_inicio:
                params["fecha_inicio"] = str(fecha_inicio)
            if fecha_fin:
                params["fecha_fin"] = str(fecha_fin)
            
            response = requests.get(API_ENDPOINT, params=params)
            response.raise_for_status()
            
            data = response.json()
            
            # Mostrar resultados
            st.success(f"✅ Se encontraron {data['total']} trámites")
            
            if data['data']:
                # Convertir a DataFrame
                df = pd.DataFrame(data['data'])
                
                # Mostrar tabla
                st.dataframe(
                    df,
                    use_container_width=True,
                    hide_index=True
                )
                
                # Opción de descarga
                csv = df.to_csv(index=False).encode('utf-8')
                st.download_button(
                    label="📥 Descargar CSV",
                    data=csv,
                    file_name="tramites_invima.csv",
                    mime="text/csv"
                )
            else:
                st.warning("No se encontraron resultados para los criterios especificados")
                
        except requests.exceptions.RequestException as e:
            st.error(f"❌ Error al conectar con la API: {str(e)}")
        except Exception as e:
            st.error(f"❌ Error: {str(e)}")

# Información adicional
with st.expander("ℹ️ Información sobre la búsqueda"):
    st.markdown("""
    ### Criterios de Búsqueda
    
    - **Número de Radicado**: Busca trámites que contengan el texto ingresado
    - **Estado**: Filtra por el estado exacto del trámite
    - **Fechas**: Filtra trámites entre las fechas especificadas
    - **Límite**: Cantidad máxima de resultados a mostrar
    - **Offset**: Cantidad de resultados a omitir (para paginación)
    
    ### Notas
    - Los campos son opcionales, puedes buscar por uno o varios criterios
    - La búsqueda se realiza sobre los datos abiertos del INVIMA
    - Los resultados se ordenan por fecha de radicación (más recientes primero)
    """)
