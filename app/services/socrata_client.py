"""
Cliente para Socrata API
Consume datos del INVIMA vía Socrata Open Data API usando sodapy
"""
from sodapy import Socrata
from typing import Dict, List, Optional
from app.core.config import settings
import asyncio
from functools import wraps
import unicodedata
from datetime import datetime

def async_wrap(func):
    """Wrapper para convertir funciones síncronas en asíncronas"""
    @wraps(func)
    async def run(*args, **kwargs):
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, lambda: func(*args, **kwargs))
    return run

class SocrataClient:
    INVIMA_ENTITY_NAME = "INSTITUTO NACIONAL DE VIGILANCIA DE MEDICAMENTOS Y ALIMENTOS"
    CATEGORY_KEYWORDS = {
        "medicamentos": ["medicament", "farmac", "biologic", "terapeut", "suero", "vigilancia sanitaria", "intrahospitalario"],
        "alimentos": ["alimento", "nutric", "comest", "bebida", "alimenticio"],
        "cosmeticos": ["cosmet", "higiene personal", "aseo personal", "perfume", "maquill", "aseo cosm"],
        "dispositivos_medicos": ["dispositivo", "equipo medico", "instrumental", "in vitro", "reactivo de diagnostico", "implant"],
        "certificaciones": ["certific", "inspecc", "auditor", "bpm", "verific", "licencia", "concepto sanitario"]
    }
    CATEGORY_LABELS = {
        "medicamentos": "Medicamentos",
        "alimentos": "Alimentos",
        "cosmeticos": "Cosméticos",
        "dispositivos_medicos": "Dispositivos médicos",
        "certificaciones": "Certificaciones o inspecciones"
    }

    def __init__(self):
        # Inicializar cliente Socrata
        # Si hay app_token, username y password, usar autenticación
        if settings.SOCRATA_APP_TOKEN:
            self.client = Socrata(
                settings.SOCRATA_DOMAIN,
                settings.SOCRATA_APP_TOKEN,
                username=settings.SOCRATA_USERNAME if settings.SOCRATA_USERNAME else None,
                password=settings.SOCRATA_PASSWORD if settings.SOCRATA_PASSWORD else None
            )
        else:
            # Cliente sin autenticación (solo datos públicos)
            self.client = Socrata(settings.SOCRATA_DOMAIN, None)
        
        self.dataset_id = settings.SOCRATA_DATASET_ID
    
    def __del__(self):
        """Cerrar cliente al destruir el objeto"""
        if hasattr(self, 'client'):
            self.client.close()
    
    @staticmethod
    def _clean_value(value: Optional[str]) -> Optional[str]:
        """
        Normaliza valores provenientes del dataset reemplazando cadenas 'NULL' por None
        y eliminando espacios extra.
        """
        if value is None:
            return None
        if isinstance(value, str):
            normalized = value.strip()
            if normalized.upper() == "NULL" or normalized == "":
                return None
            return normalized
        return value

    @staticmethod
    def _normalize_text(value: Optional[str]) -> str:
        """
        Convierte una cadena a minúsculas sin tildes para facilitar búsquedas.
        """
        if not value:
            return ""
        normalized = unicodedata.normalize("NFD", value)
        without_accents = "".join(
            char for char in normalized if unicodedata.category(char) != "Mn"
        )
        return without_accents.lower()

    def _format_date(self, value: Optional[str]) -> Optional[str]:
        """
        Convierte la fecha recibida del dataset a formato ISO (YYYY-MM-DD) cuando es posible.
        """
        clean_value = self._clean_value(value)
        if not clean_value:
            return None
        for fmt in ("%d/%m/%Y", "%Y-%m-%d", "%Y-%m-%dT%H:%M:%S.%f", "%Y-%m-%dT%H:%M:%S"):
            try:
                return datetime.strptime(clean_value, fmt).date().isoformat()
            except ValueError:
                continue
        return clean_value

    def _normalize_category(self, raw_category: str) -> Optional[str]:
        """
        Mapea la categoría recibida hacia el identificador interno soportado.
        """
        slug = self._normalize_text(raw_category).replace(" ", "_")
        if slug in self.CATEGORY_KEYWORDS:
            return slug
        # También aceptar nombres de catálogo con artículos omitidos
        for key, label in self.CATEGORY_LABELS.items():
            label_slug = self._normalize_text(label).replace(" ", "_")
            if slug == label_slug:
                return key
        return None

    def _detect_categories(self, *texts: Optional[str]) -> List[str]:
        """
        Detecta categorías sugeridas a partir del contenido textual del trámite.
        """
        combined = " ".join(self._normalize_text(text) for text in texts if text)
        detected = []
        for key, keywords in self.CATEGORY_KEYWORDS.items():
            if any(keyword in combined for keyword in keywords):
                detected.append(self.CATEGORY_LABELS[key])
        return detected

    @staticmethod
    def _safe_int(value: Optional[str]) -> int:
        """
        Intenta convertir un valor a entero para ordenar pasos secuenciales.
        """
        if value is None:
            return 0
        try:
            return int(float(value))
        except (ValueError, TypeError):
            return 0

    def _build_where_clause(
        self,
        texto: Optional[str],
        categorias: Optional[List[str]]
    ) -> str:
        """
        Construye la cláusula where en función de los filtros aplicados.
        """
        where_clauses = [f"nombre_de_la_entidad = '{self.INVIMA_ENTITY_NAME}'"]

        if texto:
            sanitized = texto.replace("'", "''")
            like_pattern = f"%{sanitized.upper()}%"
            search_fields = [
                "nombre_del_tr_mite_u_otro",
                "nombre_com_n",
                "prop_sito_del_tr_mite_u_otro",
                "nombre_resultado"
            ]
            text_clause = " OR ".join(
                f"upper({field}) like '{like_pattern}'"
                for field in search_fields
            )
            where_clauses.append(f"({text_clause})")

        if categorias:
            category_conditions: List[str] = []
            for categoria in categorias:
                normalized = self._normalize_category(categoria)
                if not normalized:
                    continue
                keywords = self.CATEGORY_KEYWORDS.get(normalized, [])
                for keyword in keywords:
                    pattern = f"%{keyword.upper()}%"
                    category_conditions.extend([
                        f"upper(nombre_del_tr_mite_u_otro) like '{pattern}'",
                        f"upper(nombre_com_n) like '{pattern}'"
                    ])
            if category_conditions:
                where_clauses.append("(" + " OR ".join(category_conditions) + ")")

        where = " AND ".join(where_clauses)
        return where
    
    async def query(
        self,
        select: Optional[str] = None,
        where: Optional[str] = None,
        group: Optional[str] = None,
        order: Optional[str] = None,
        limit: int = 1000,
        offset: int = 0,
        **kwargs
    ) -> List[Dict]:
        """
        Ejecuta una consulta a la API de Socrata usando SoQL
        """
        # Construir parámetros de consulta
        query_params = {
            "$limit": limit,
            "$offset": offset
        }
        
        if select:
            query_params["$select"] = select
        if where:
            query_params["$where"] = where
        if group:
            query_params["$group"] = group
        if order:
            query_params["$order"] = order
        
        # Agregar otros parámetros adicionales
        query_params.update(kwargs)
        
        # Ejecutar consulta de forma asíncrona
        loop = asyncio.get_event_loop()
        results = await loop.run_in_executor(
            None,
            lambda: self.client.get(self.dataset_id, **query_params)
        )
        
        return results
    
    async def buscar_tramites(
        self,
        radicado: Optional[str] = None,
        estado: Optional[str] = None,
        fecha_inicio: Optional[str] = None,
        fecha_fin: Optional[str] = None,
        limit: int = 100,
        offset: int = 0
    ) -> Dict:
        """
        HU01: Buscar trámites por radicado, estado o fecha
        """
        where_clauses = []
        
        if radicado:
            # Búsqueda con LIKE para coincidencias parciales
            where_clauses.append(f"numero_radicado like '%{radicado}%'")
        if estado:
            where_clauses.append(f"estado = '{estado}'")
        if fecha_inicio and fecha_fin:
            where_clauses.append(f"fecha_radicacion between '{fecha_inicio}T00:00:00' and '{fecha_fin}T23:59:59'")
        
        where = " AND ".join(where_clauses) if where_clauses else None
        
        try:
            # Obtener total de registros
            count_query = "count(*) as total"
            count_data = await self.query(
                select=count_query,
                where=where,
                limit=1
            )
            total = int(count_data[0].get("total", 0)) if count_data else 0
        except Exception:
            # Si falla el conteo, intentar sin él
            total = 0
        
        # Obtener datos
        data = await self.query(
            where=where,
            order="fecha_radicacion DESC",
            limit=limit,
            offset=offset
        )
        
        # Si no pudimos obtener el total antes, usar el tamaño de los datos
        if total == 0 and data:
            total = len(data)
        
        return {
            "total": total,
            "data": data,
            "limit": limit,
            "offset": offset
        }

    async def buscar_tramites_suit(
        self,
        texto: Optional[str] = None,
        categorias: Optional[List[str]] = None,
        limit: int = 20,
        offset: int = 0
    ) -> Dict:
        """
        HU-INVIMA-001: Búsqueda de trámites del INVIMA disponibles en el SUIT.
        Retorna los trámites agrupados por número único junto con sus pasos asociados.
        """
        where = self._build_where_clause(texto=texto, categorias=categorias)

        # Obtener total de trámites únicos que cumplen la condición
        total = 0
        try:
            total_data = await self.query(
                select="count(distinct n_mero_unico) as total",
                where=where,
                limit=1
            )
            if total_data:
                total = int(total_data[0].get("total", 0))
        except Exception:
            total = 0

        select_fields = (
            "n_mero_unico, "
            "max(nombre_del_tr_mite_u_otro) as nombre_tramite, "
            "max(nombre_com_n) as nombre_comun, "
            "max(prop_sito_del_tr_mite_u_otro) as proposito, "
            "max(nombre_resultado) as resultado, "
            "max(clase) as clase_tramite, "
            "max(fecha_de_actualizaci_n) as fecha_actualizacion"
        )

        tramites_data = await self.query(
            select=select_fields,
            where=where,
            group="n_mero_unico",
            order="nombre_tramite ASC",
            limit=limit,
            offset=offset
        )

        numero_unicos = [
            tramite.get("n_mero_unico")
            for tramite in tramites_data
            if tramite.get("n_mero_unico")
        ]

        pasos_map: Dict[str, List[Dict]] = {}
        if numero_unicos:
            sanitized_ids: List[str] = []
            for numero in numero_unicos:
                sanitized = str(numero).replace("'", "''")
                sanitized_ids.append(f"'{sanitized}'")
            ids_clause = ", ".join(sanitized_ids)
            pasos_where = f"{where} AND n_mero_unico in ({ids_clause})"
            pasos_data = await self.query(
                select=(
                    "n_mero_unico, "
                    "orden_paso, "
                    "descripcion_paso, "
                    "orden_condicion, "
                    "tipo_accion_condicion, "
                    "documento_nombre, "
                    "documento_tipo, "
                    "descripcion_del_pago"
                ),
                where=pasos_where,
                order="n_mero_unico, orden_paso, orden_condicion",
                limit=len(numero_unicos) * 50
            )

            for paso in pasos_data:
                numero = paso.get("n_mero_unico")
                if not numero:
                    continue
                pasos_map.setdefault(numero, []).append(paso)

        tramites = []
        for tramite in tramites_data:
            numero = tramite.get("n_mero_unico")
            nombre_tramite = self._clean_value(tramite.get("nombre_tramite"))
            nombre_comun = self._clean_value(tramite.get("nombre_comun"))
            proposito = self._clean_value(tramite.get("proposito"))
            nombre_resultado = self._clean_value(tramite.get("resultado"))
            clase = self._clean_value(tramite.get("clase_tramite"))

            pasos = []
            for paso in sorted(
                pasos_map.get(numero, []),
                key=lambda registro: (
                    self._safe_int(registro.get("orden_paso")),
                    self._safe_int(registro.get("orden_condicion"))
                )
            ):
                pasos.append({
                    "orden_paso": self._clean_value(paso.get("orden_paso")),
                    "descripcion_paso": self._clean_value(paso.get("descripcion_paso")),
                    "orden_condicion": self._clean_value(paso.get("orden_condicion")),
                    "tipo_accion_condicion": self._clean_value(paso.get("tipo_accion_condicion")),
                    "documento_nombre": self._clean_value(paso.get("documento_nombre")),
                    "documento_tipo": self._clean_value(paso.get("documento_tipo")),
                    "descripcion_del_pago": self._clean_value(paso.get("descripcion_del_pago"))
                })

            categorias_detectadas = self._detect_categories(nombre_tramite, nombre_comun, proposito)

            tramites.append({
                "numero_unico": numero,
                "nombre_tramite": nombre_tramite,
                "nombre_comun": nombre_comun,
                "proposito": proposito,
                "nombre_resultado": nombre_resultado,
                "clase": clase,
                "entidad": self.INVIMA_ENTITY_NAME,
                "fecha_actualizacion": self._format_date(tramite.get("fecha_actualizacion")),
                "categorias": categorias_detectadas,
                "pasos": pasos
            })

        return {
            "total": total,
            "limit": limit,
            "offset": offset,
            "tramites": tramites
        }
    
    async def obtener_estadisticas(self) -> Dict:
        """
        HU02: Estadísticas generales del dashboard
        """
        try:
            # Total de trámites
            total_data = await self.query(
                select="count(*) as total",
                limit=1
            )
            total_tramites = int(total_data[0].get("total", 0)) if total_data else 0
        except Exception:
            total_tramites = 0
        
        try:
            # Trámites por estado
            por_estado = await self.query(
                select="estado, count(*) as cantidad",
                group="estado",
                order="cantidad DESC",
                limit=20
            )
        except Exception:
            por_estado = []
        
        try:
            # Trámites por mes (últimos 12 meses)
            # Usar date_trunc_ym para agrupar por año-mes
            por_mes = await self.query(
                select="date_trunc_ym(fecha_radicacion) as mes, count(*) as cantidad",
                group="mes",
                order="mes DESC",
                limit=12
            )
        except Exception:
            por_mes = []
        
        return {
            "total_tramites": total_tramites,
            "por_estado": por_estado,
            "por_mes": por_mes
        }
    
    async def obtener_datos_publicos(
        self,
        formato: str = "json",
        limit: int = 1000
    ) -> List[Dict]:
        """
        HU04: Descarga de datos abiertos
        """
        return await self.query(
            limit=limit,
            order="fecha_radicacion DESC"
        )
    
    async def obtener_campos(self) -> List[str]:
        """
        Obtiene la lista de campos disponibles
        """
        data = await self.query(limit=1)
        if data and len(data) > 0:
            return list(data[0].keys())
        return []
    
    async def get_metadata(self) -> Dict:
        """
        Obtiene metadatos del dataset
        """
        loop = asyncio.get_event_loop()
        metadata = await loop.run_in_executor(
            None,
            lambda: self.client.get_metadata(self.dataset_id)
        )
        return metadata

# Instancia singleton
socrata_client = SocrataClient()
