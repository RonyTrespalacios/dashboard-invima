"""
HU05: Reportar Errores o Inconsistencias
"""
import streamlit as st
import requests
import os
from datetime import datetime

st.set_page_config(page_title="Reportar Error", page_icon="📝", layout="wide")

FASTAPI_URL = os.getenv("FASTAPI_URL", "http://localhost:8000")
API_REPORTES = f"{FASTAPI_URL}/api/v1/reportes/crear"

st.title("📝 Reportar Error o Inconsistencia")
st.markdown("Ayúdanos a mejorar la calidad de los datos reportando errores o inconsistencias")

# Información
st.info("""
🔍 **¿Encontraste un error?**

Si detectaste alguna inconsistencia en los datos, información incorrecta o 
cualquier problema con el sistema, por favor repórtalo usando este formulario.
""")

st.divider()

# Formulario de reporte
st.subheader("📋 Formulario de Reporte")

with st.form("form_reporte"):
    # Datos del reportante
    col1, col2 = st.columns(2)
    
    with col1:
        nombre = st.text_input(
            "Nombre Completo (Opcional)",
            placeholder="Ej: Juan Pérez",
            help="Tu nombre completo (opcional)",
            key="nombre_input"
        )
    
    with col2:
        email = st.text_input(
            "Correo Electrónico (Opcional)",
            placeholder="ejemplo@email.com",
            help="Email para contactarte si es necesario (opcional)",
            key="email_input"
        )
    
    # Tipo de error
    tipo_error = st.selectbox(
        "Tipo de Error *",
        options=[
            "",
            "Información Incorrecta",
            "Dato Faltante",
            "Error de Sistema",
            "Inconsistencia en Datos",
            "Problema de Visualización",
            "Otro"
        ],
        help="Selecciona el tipo de error encontrado",
        key="tipo_error_input"
    )
    
    # Número de radicado (opcional)
    numero_radicado = st.text_input(
        "Número de Radicado (Opcional)",
        placeholder="Ej: 20230001234",
        help="Si el error está relacionado con un trámite específico, indica su número de radicado",
        key="numero_radicado_input"
    )
    
    # Descripción
    descripcion = st.text_area(
        "Descripción del Error *",
        placeholder="Describe detalladamente el error encontrado...",
        help="Proporciona todos los detalles posibles sobre el error",
        height=150,
        key="descripcion_input"
    )
    
    st.markdown("---")
    st.caption("Los campos marcados con * son obligatorios")
    
    # Botón de envío
    submitted = st.form_submit_button(
        "📨 Enviar Reporte",
        use_container_width=True,
        type="primary"
    )

# Procesar envío
if submitted:
    # Validaciones
    errores = []
    
    # Validar nombre solo si se proporciona
    if nombre and len(nombre) < 2:
        errores.append("El nombre debe tener al menos 2 caracteres")
    
    # Validar email solo si se proporciona
    if email and ("@" not in email or "." not in email):
        errores.append("Ingresa un correo electrónico válido")
    
    if not tipo_error:
        errores.append("Selecciona un tipo de error")
    
    if not descripcion or len(descripcion) < 10:
        errores.append("La descripción debe tener al menos 10 caracteres")
    
    if len(descripcion) > 1000:
        errores.append("La descripción no debe exceder 1000 caracteres")
    
    # Mostrar errores o enviar
    if errores:
        st.error("⚠️ Por favor corrige los siguientes errores:")
        for error in errores:
            st.error(f"- {error}")
    else:
        with st.spinner("Enviando reporte..."):
            try:
                payload = {
                    "nombre": nombre,
                    "email": email,
                    "tipo_error": tipo_error,
                    "descripcion": descripcion,
                    "numero_radicado": numero_radicado if numero_radicado else None
                }
                
                response = requests.post(API_REPORTES, json=payload)
                response.raise_for_status()
                
                resultado = response.json()
                
                if resultado.get("success"):
                    st.success("✅ ¡Reporte enviado exitosamente!")
                    st.info(f"📋 ID del Reporte: **{resultado.get('reporte_id')}**")
                    st.balloons()
                    
                    # Mostrar resumen
                    with st.expander("📄 Resumen del Reporte"):
                        st.write(f"**Nombre:** {nombre if nombre else 'No proporcionado'}")
                        st.write(f"**Email:** {email if email else 'No proporcionado'}")
                        st.write(f"**Tipo:** {tipo_error}")
                        if numero_radicado:
                            st.write(f"**Radicado:** {numero_radicado}")
                        st.write(f"**Descripción:** {descripcion}")
                        st.write(f"**Fecha:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
                    
                    st.info("""
                    📬 **¿Qué sigue?**
                    
                    - Tu reporte ha sido registrado con éxito
                    - El equipo revisará la información proporcionada
                    - Si es necesario, te contactaremos al correo indicado
                    - Guarda el ID del reporte para futuras referencias
                    """)
                    
                    # Limpiar el formulario
                    st.rerun()
                else:
                    st.error(f"❌ Error: {resultado.get('message')}")
                    
            except requests.exceptions.RequestException as e:
                st.error(f"❌ Error de conexión: {str(e)}")
            except Exception as e:
                st.error(f"❌ Error inesperado: {str(e)}")

st.divider()

# Información adicional
with st.expander("ℹ️ Información sobre Reportes"):
    st.markdown("""
    ### ¿Qué tipo de errores puedo reportar?
    
    - **Información Incorrecta**: Datos que no corresponden con la realidad
    - **Dato Faltante**: Información que debería estar pero no aparece
    - **Error de Sistema**: Problemas técnicos con la aplicación
    - **Inconsistencia en Datos**: Datos contradictorios o ilógicos
    - **Problema de Visualización**: Gráficos o tablas que no se muestran correctamente
    
    ### ¿Qué información debo proporcionar?
    
    - Descripción clara y detallada del problema
    - Pasos para reproducir el error (si aplica)
    - Número de radicado si está relacionado con un trámite específico
    - Cualquier otro detalle relevante
    
    ### ¿Qué pasa con mi reporte?
    
    1. Tu reporte es registrado en el sistema
    2. El equipo técnico lo revisa
    3. Se toman las acciones correctivas necesarias
    4. Si es necesario, te contactamos para más información
    
    ### Privacidad
    
    Tus datos personales solo se usan para gestionar tu reporte y no 
    se compartirán con terceros.
    """)

# Tips
st.success("""
💡 **Tips para un buen reporte**

- Sé específico y detallado
- Incluye ejemplos cuando sea posible
- Proporciona el número de radicado si aplica
- Usa un correo válido para que podamos contactarte
""")
