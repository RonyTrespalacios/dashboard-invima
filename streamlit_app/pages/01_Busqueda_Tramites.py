"""
HU-INVIMA-001: Búsqueda y consulta de trámites INVIMA en el SUIT
"""
import streamlit as st
import requests
import pandas as pd
import os
from typing import Dict, List

st.set_page_config(page_title="Búsqueda de Trámites INVIMA - SUIT", page_icon="🔍", layout="wide")

FASTAPI_URL = os.getenv("FASTAPI_URL", "http://localhost:8000")
API_ENDPOINT = f"{FASTAPI_URL}/api/v1/tramites/suit"

CATEGORY_OPTIONS: Dict[str, str] = {
    "medicamentos": "Medicamentos",
    "alimentos": "Alimentos",
    "cosmeticos": "Cosméticos",
    "dispositivos_medicos": "Dispositivos médicos",
    "certificaciones": "Certificaciones o inspecciones"
}

RESULT_STATE_KEY = "tramites_suit_result"
SELECT_STATE_KEY = "tramites_suit_selected_index"

st.title("🔍 Búsqueda de trámites del INVIMA en el SUIT")
st.markdown(
    "Consulta los trámites disponibles para el INVIMA, sus propósitos y los pasos necesarios según el SUIT."
)

with st.form("form_busqueda_suit"):
    texto = st.text_input(
        "Buscar por nombre del trámite, propósito o palabra clave",
        placeholder="Ej: registro sanitario, certificación BPM, autorización",
        key="tramites_suit_texto"
    )
    col_filtros = st.columns([2, 1])
    with col_filtros[0]:
        categorias_seleccionadas = st.multiselect(
            "Filtrar por tipo de trámite",
            options=list(CATEGORY_OPTIONS.values()),
            key="tramites_suit_categorias"
        )
    with col_filtros[1]:
        limite = st.slider("Cantidad de resultados", min_value=5, max_value=50, value=20, step=5)
    submitted = st.form_submit_button("🔍 Buscar trámites", use_container_width=True)

def mostrar_resultados(payload: Dict):
    tramites = payload.get("tramites", [])
    total = payload.get("total", 0)

    if not tramites:
        st.warning("No se encontraron trámites con los criterios seleccionados.")
        return

    st.success(f"✅ Se encontraron {total} trámites disponibles para el INVIMA.")

    resumen_df = pd.DataFrame(
        [
            {
                "Trámite": item.get("nombre_tramite") or item.get("nombre_comun") or "Trámite sin nombre",
                "Nombre común": item.get("nombre_comun"),
                "Resultado": item.get("nombre_resultado"),
                "Clase": item.get("clase"),
                "Fecha actualización": item.get("fecha_actualizacion"),
                "Categorías": ", ".join(item.get("categorias", []))
            }
            for item in tramites
        ]
    )
    with st.expander("📋 Ver tabla resumen de trámites"):
        st.dataframe(resumen_df, use_container_width=True, hide_index=True)

    col_lista, col_detalle = st.columns([1.2, 2.8], gap="large")
    opciones = list(range(len(tramites)))

    def _format_option(idx: int) -> str:
        item = tramites[idx]
        nombre = item.get("nombre_tramite") or item.get("nombre_comun") or "Trámite sin nombre"
        resultado = item.get("nombre_resultado")
        if resultado:
            return f"{nombre} · {resultado}"
        return nombre

    selected_index = st.session_state.get(SELECT_STATE_KEY, 0)
    if selected_index >= len(opciones):
        selected_index = 0
    st.session_state[SELECT_STATE_KEY] = selected_index
    seleccion = col_lista.radio(
        "Trámites encontrados",
        options=opciones,
        format_func=_format_option,
        label_visibility="collapsed",
        index=selected_index
    )
    selected_index = opciones.index(seleccion)
    st.session_state[SELECT_STATE_KEY] = selected_index

    tramite = tramites[selected_index]
    nombre_tramite = tramite.get("nombre_tramite") or "Trámite sin nombre"

    col_detalle.subheader(nombre_tramite)
    col_detalle.markdown(f"**Nombre común:** {tramite.get('nombre_comun') or 'Sin información'}")
    col_detalle.markdown(f"**Propósito:** {tramite.get('proposito') or 'Sin información'}")
    col_detalle.markdown(f"**Resultado esperado:** {tramite.get('nombre_resultado') or 'Sin información'}")
    col_detalle.markdown(f"**Clase del trámite:** {tramite.get('clase') or 'Sin especificar'}")
    col_detalle.markdown(f"**Entidad responsable:** {tramite.get('entidad')}")

    fecha = tramite.get("fecha_actualizacion")
    if fecha:
        col_detalle.markdown(f"**Fecha de actualización:** {fecha}")

    categorias = tramite.get("categorias", [])
    if categorias:
        chips = " · ".join(categorias)
        col_detalle.markdown(f"**Categorías sugeridas:** {chips}")

    pasos = tramite.get("pasos", [])
    requisitos = []
    for paso in pasos:
        documento_nombre = paso.get("documento_nombre")
        if documento_nombre:
            documento_tipo = paso.get("documento_tipo")
            if documento_tipo:
                requisitos.append(f"{documento_nombre} ({documento_tipo})")
            else:
                requisitos.append(documento_nombre)

    if requisitos:
        col_detalle.markdown("**Requisitos documentales identificados:**")
        for req in requisitos:
            col_detalle.markdown(f"- {req}")

    with col_detalle.expander("🧭 Pasos del trámite", expanded=True):
        if not pasos:
            st.info("Este trámite no tiene pasos asociados en el dataset.")
        else:
            for paso in pasos:
                orden = paso.get("orden_paso") or "-"
                tipo_accion = paso.get("tipo_accion_condicion") or "Acción"
                descripcion = paso.get("descripcion_paso") or "Sin descripción"
                st.markdown(f"**Paso {orden} · {tipo_accion}**")
                st.markdown(descripcion)
                if paso.get("descripcion_del_pago"):
                    st.markdown(f"💰 *Pago:* {paso['descripcion_del_pago']}")
                st.markdown("---")

            st.caption("Los datos provienen del SUIT (Función Pública) y se limitan a la información disponible públicamente.")

if submitted:
    with st.spinner("Consultando trámites del SUIT..."):
        try:
            params: Dict[str, List[str] | str | int] = {"limit": limite, "offset": 0}
            if texto:
                params["texto"] = texto
            if categorias_seleccionadas:
                categorias_slug = [
                    slug for slug, label in CATEGORY_OPTIONS.items() if label in categorias_seleccionadas
                ]
                if categorias_slug:
                    params["categorias"] = categorias_slug

            response = requests.get(API_ENDPOINT, params=params, timeout=30)
            response.raise_for_status()
            payload = response.json()

            st.session_state[RESULT_STATE_KEY] = payload
            st.session_state[SELECT_STATE_KEY] = 0
            mostrar_resultados(payload)
        except requests.exceptions.RequestException as exc:
            st.error(f"❌ Error al conectar con la API: {exc}")
        except Exception as exc:  # pylint: disable=broad-except
            st.error(f"❌ Ocurrió un error al procesar la información: {exc}")
else:
    if RESULT_STATE_KEY in st.session_state:
        mostrar_resultados(st.session_state[RESULT_STATE_KEY])
    else:
        st.info("Ingresa una palabra clave o selecciona un filtro para iniciar la búsqueda.")
