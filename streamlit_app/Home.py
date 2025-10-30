"""
Streamlit Home Page
Dashboard INVIMA - Página Principal
"""
import streamlit as st
import os

# Configuración de la página
st.set_page_config(
    page_title="Dashboard INVIMA",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="expanded"
)

# URL de la API
FASTAPI_URL = os.getenv("FASTAPI_URL", "http://localhost:8000")

# Título principal
st.title("🏥 Dashboard INVIMA")
st.markdown("### Sistema de Consulta de Trámites del INVIMA")

# Descripción
st.markdown("""
Bienvenido al sistema de consulta de trámites del Instituto Nacional de Vigilancia 
de Medicamentos y Alimentos (INVIMA).

Este dashboard permite:
- 🔍 **Buscar trámites** por radicado, estado o fecha
- 📊 **Visualizar estadísticas** generales y tendencias
- 🌐 **Consultar tablero público** con información actualizada
- 📥 **Descargar datos abiertos** en formato JSON o CSV
- 📝 **Reportar errores** o inconsistencias encontradas
- 📊 **Visualizar reportes** con datos anónimos para administración

#### Fuente de Datos
Los datos son consultados en tiempo real desde el portal de Datos Abiertos del 
gobierno colombiano vía [Socrata API](https://www.datos.gov.co/).

---

### 🚀 Comenzar

Utiliza el menú lateral para navegar entre las diferentes secciones.
""")

# Información adicional en columnas
col1, col2, col3 = st.columns(3)

with col1:
    st.info("**API Backend**\n\nFastAPI + Socrata")

with col2:
    st.info("**Frontend**\n\nStreamlit")

with col3:
    st.info("**Datos**\n\nDatos Abiertos CO")

# Footer
st.markdown("---")
st.markdown("*Dashboard desarrollado con FastAPI + Streamlit | 2025*")
