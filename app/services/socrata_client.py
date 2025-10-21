"""
Cliente para Socrata API
Consume datos del INVIMA vía Socrata Open Data API usando sodapy
"""
from sodapy import Socrata
from typing import Dict, List, Optional
from app.core.config import settings
import asyncio
from functools import wraps

def async_wrap(func):
    """Wrapper para convertir funciones síncronas en asíncronas"""
    @wraps(func)
    async def run(*args, **kwargs):
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, lambda: func(*args, **kwargs))
    return run

class SocrataClient:
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
