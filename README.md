# Dashboard INVIMA

Sistema de consulta de trámites del Instituto Nacional de Vigilancia de Medicamentos y Alimentos (INVIMA) utilizando datos abiertos del gobierno colombiano.

## 🏗️ Arquitectura

- **Backend**: FastAPI
- **Frontend**: Streamlit
- **Datos**: API Socrata (Datos Abiertos Colombia)
- **Containerización**: Docker + Docker Compose

## 📁 Estructura del Proyecto

```
invima_dashboard/
├── app/                          # Backend FastAPI
│   ├── main.py                  # Aplicación principal
│   ├── api/                     # Rutas de la API
│   │   ├── routes_tramites.py   # HU01: Búsqueda
│   │   ├── routes_dashboard.py  # HU02: Estadísticas
│   │   ├── routes_reportes.py   # HU05: Reportes
│   │   └── routes_public.py     # HU03/HU04: Público
│   ├── core/                    # Configuración
│   │   ├── config.py
│   │   └── utils.py
│   ├── models/                  # Modelos de datos
│   │   ├── tramites_model.py
│   │   └── reporte_model.py
│   └── services/                # Lógica de negocio
│       ├── socrata_client.py    # Cliente API Socrata
│       └── report_service.py
├── streamlit_app/               # Frontend Streamlit
│   ├── Home.py                  # Página principal
│   └── pages/
│       ├── 01_Busqueda_Tramites.py    # HU01
│       ├── 02_Estadisticas.py         # HU02
│       ├── 03_Tablero_Publico.py      # HU03
│       ├── 04_Datos_Abiertos.py       # HU04
│       └── 05_Reportar_Error.py       # HU05
├── Dockerfile.fastapi
├── Dockerfile.streamlit
├── docker-compose.yml
├── requirements.txt
└── .env
```

## 🚀 Instalación y Uso

### Opción 1: Con Docker (Recomendado)

1. **Clonar el repositorio**
```bash
cd dashboard-invima
```

2. **Configurar variables de entorno**
```bash
# Editar .env si es necesario (opcional)
```

3. **Levantar los servicios**
```powershell
docker-compose up --build
```

4. **Acceder a las aplicaciones**
- Frontend (Streamlit): http://localhost:8501
- Backend (FastAPI): http://localhost:8000
- Documentación API: http://localhost:8000/docs

### Opción 2: Sin Docker (Desarrollo Local)

1. **Crear entorno virtual**
```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

2. **Instalar dependencias**
```powershell
pip install -r requirements.txt
```

3. **Levantar Backend (Terminal 1)**
```powershell
cd app
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

4. **Levantar Frontend (Terminal 2)**
```powershell
cd streamlit_app
streamlit run Home.py --server.port 8501
```

## 📋 Historias de Usuario Implementadas

### HU01: Búsqueda de Trámites
Permite buscar trámites por radicado, estado o rango de fechas.
- **Ruta API**: `/api/v1/tramites/buscar`
- **Página**: `01_Busqueda_Tramites.py`

### HU02: Estadísticas del Dashboard
Visualización de métricas y tendencias con gráficos interactivos.
- **Ruta API**: `/api/v1/dashboard/estadisticas`
- **Página**: `02_Estadisticas.py`

### HU03: Tablero Público
Vista pública con resumen de trámites y últimas actualizaciones.
- **Ruta API**: `/api/v1/public/tablero`
- **Página**: `03_Tablero_Publico.py`

### HU04: Datos Abiertos
Descarga de datasets completos en formato JSON o CSV.
- **Ruta API**: `/api/v1/public/datos-abiertos`
- **Página**: `04_Datos_Abiertos.py`

### HU05: Reporte de Errores
Formulario para reportar inconsistencias en los datos.
- **Ruta API**: `/api/v1/reportes/crear`
- **Página**: `05_Reportar_Error.py`

## 🔧 Tecnologías Utilizadas

- **FastAPI**: Framework web moderno para Python
- **Streamlit**: Framework para crear aplicaciones de datos
- **sodapy**: Cliente oficial de Socrata API para Python
- **Pandas**: Análisis y manipulación de datos
- **Plotly**: Visualizaciones interactivas
- **Docker**: Containerización

## 🌐 API Endpoints

### Trámites
- `GET /api/v1/tramites/buscar` - Buscar trámites
- `GET /api/v1/tramites/detalle/{radicado}` - Detalle de trámite
- `GET /api/v1/tramites/campos` - Campos disponibles

### Dashboard
- `GET /api/v1/dashboard/estadisticas` - Estadísticas generales
- `GET /api/v1/dashboard/metricas` - Métricas del sistema

### Público
- `GET /api/v1/public/tablero` - Tablero público
- `GET /api/v1/public/datos-abiertos` - Descarga de datos

### Reportes
- `POST /api/v1/reportes/crear` - Crear reporte
- `GET /api/v1/reportes/listar` - Listar reportes

## 📊 Fuente de Datos

Los datos provienen del portal de **Datos Abiertos de Colombia** a través de la API Socrata usando el cliente oficial **sodapy**:
- **Dataset**: SUIT - INVIMA
- **Dataset ID**: 48fq-mxnm
- **Dominio**: www.datos.gov.co
- **Biblioteca**: sodapy (cliente oficial Python)

## 🛠️ Comandos Útiles

### Docker
```powershell
# Levantar servicios
docker-compose up -d

# Ver logs
docker-compose logs -f

# Detener servicios
docker-compose down

# Reconstruir contenedores
docker-compose up --build
```

### Desarrollo
```powershell
# Instalar dependencias
pip install -r requirements.txt

# Formatear código
black app/ streamlit_app/

# Linter
flake8 app/
```

## 📝 Variables de Entorno

Archivo `.env`:
```env
# Socrata API (usando sodapy)
SOCRATA_DOMAIN=www.datos.gov.co
SOCRATA_DATASET_ID=48fq-mxnm
SOCRATA_APP_TOKEN=  # Opcional, mejora límites de rate
SOCRATA_USERNAME=   # Opcional, para datasets privados
SOCRATA_PASSWORD=   # Opcional, para datasets privados

# FastAPI
FASTAPI_HOST=0.0.0.0
FASTAPI_PORT=8000
API_PREFIX=/api/v1
```

### Obtener App Token (Opcional pero Recomendado)

1. Visita https://www.datos.gov.co
2. Crea una cuenta gratuita
3. Ve a tu perfil → Developer Settings
4. Genera un Application Token
5. Agrega el token a tu archivo `.env`

**Beneficios del App Token:**
- Mayor límite de requests (sin token: 1000/día, con token: 100,000/día)
- Mayor velocidad de respuesta
- Prioridad en la cola de peticiones

## 🤝 Contribuir

1. Fork el proyecto
2. Crea una rama para tu feature (`git checkout -b feature/AmazingFeature`)
3. Commit tus cambios (`git commit -m 'Add some AmazingFeature'`)
4. Push a la rama (`git push origin feature/AmazingFeature`)
5. Abre un Pull Request

## 📄 Licencia

Este proyecto está bajo la Licencia MIT.

## 👥 Autores

Proyecto desarrollado para la materia de Metodologías Ágiles - ESPE 2025

## 📞 Soporte

Para reportar problemas o sugerencias, usa la página de "Reportar Error" en la aplicación o crea un issue en GitHub.
