# Ejemplos de Uso de la API

## Configuración Inicial

Base URL: `http://localhost:8000`

## 1. Health Check

Verifica que la API está funcionando:

```bash
curl http://localhost:8000/health
```

**Respuesta:**
```json
{
  "status": "healthy"
}
```

---

## 2. Buscar Trámites (HU01)

### Búsqueda Simple

```bash
curl "http://localhost:8000/api/v1/tramites/buscar?limit=10"
```

### Búsqueda por Radicado

```bash
curl "http://localhost:8000/api/v1/tramites/buscar?radicado=2023001234&limit=10"
```

### Búsqueda por Estado

```bash
curl "http://localhost:8000/api/v1/tramites/buscar?estado=APROBADO&limit=50"
```

### Búsqueda por Rango de Fechas

```bash
curl "http://localhost:8000/api/v1/tramites/buscar?fecha_inicio=2023-01-01&fecha_fin=2023-12-31&limit=100"
```

### Búsqueda Combinada con Paginación

```bash
curl "http://localhost:8000/api/v1/tramites/buscar?estado=APROBADO&fecha_inicio=2023-01-01&limit=50&offset=100"
```

**Respuesta:**
```json
{
  "total": 1234,
  "data": [
    {
      "numero_radicado": "2023001234",
      "nombre_tramite": "Registro Sanitario",
      "estado": "APROBADO",
      "fecha_radicacion": "2023-06-15"
    }
  ],
  "limit": 50,
  "offset": 100
}
```

---

## 3. Detalle de Trámite

```bash
curl "http://localhost:8000/api/v1/tramites/detalle/2023001234"
```

---

## 4. Obtener Campos Disponibles

```bash
curl "http://localhost:8000/api/v1/tramites/campos"
```

**Respuesta:**
```json
{
  "campos": [
    "numero_radicado",
    "nombre_tramite",
    "estado",
    "fecha_radicacion",
    "...otros campos..."
  ]
}
```

---

## 5. Estadísticas del Dashboard (HU02)

```bash
curl "http://localhost:8000/api/v1/dashboard/estadisticas"
```

**Respuesta:**
```json
{
  "total_tramites": 50000,
  "por_estado": [
    {"estado": "APROBADO", "cantidad": "25000"},
    {"estado": "EN REVISIÓN", "cantidad": "15000"}
  ],
  "por_mes": [
    {"mes": "2024-01", "cantidad": "2500"},
    {"mes": "2024-02", "cantidad": "2800"}
  ]
}
```

---

## 6. Métricas Generales

```bash
curl "http://localhost:8000/api/v1/dashboard/metricas"
```

---

## 7. Tablero Público (HU03)

```bash
curl "http://localhost:8000/api/v1/public/tablero"
```

**Respuesta:**
```json
{
  "estadisticas": {
    "total_tramites": 50000,
    "por_estado": [...],
    "por_mes": [...]
  },
  "ultimos_tramites": [
    {...},
    {...}
  ]
}
```

---

## 8. Descarga de Datos Abiertos (HU04)

### Descargar JSON

```bash
curl "http://localhost:8000/api/v1/public/datos-abiertos?formato=json&limit=1000" -o datos.json
```

### Descargar CSV

```bash
curl "http://localhost:8000/api/v1/public/datos-abiertos?formato=csv&limit=1000" -o datos.csv
```

---

## 9. Crear Reporte de Error (HU05)

```bash
curl -X POST "http://localhost:8000/api/v1/reportes/crear" \
  -H "Content-Type: application/json" \
  -d '{
    "nombre": "Juan Pérez",
    "email": "juan@example.com",
    "tipo_error": "Información Incorrecta",
    "descripcion": "El estado del trámite 2023001234 no coincide con la información oficial",
    "numero_radicado": "2023001234"
  }'
```

**Respuesta:**
```json
{
  "success": true,
  "message": "Reporte guardado exitosamente",
  "reporte_id": "REP_20241020_143022"
}
```

---

## 10. Listar Reportes

```bash
curl "http://localhost:8000/api/v1/reportes/listar?limit=20"
```

---

## Ejemplos con Python

### Búsqueda de Trámites

```python
import requests

url = "http://localhost:8000/api/v1/tramites/buscar"
params = {
    "estado": "APROBADO",
    "fecha_inicio": "2023-01-01",
    "fecha_fin": "2023-12-31",
    "limit": 100
}

response = requests.get(url, params=params)
data = response.json()

print(f"Total: {data['total']}")
for tramite in data['data'][:5]:
    print(f"- {tramite['numero_radicado']}: {tramite['estado']}")
```

### Crear Reporte

```python
import requests

url = "http://localhost:8000/api/v1/reportes/crear"
payload = {
    "nombre": "Ana García",
    "email": "ana@example.com",
    "tipo_error": "Dato Faltante",
    "descripcion": "Falta información de contacto en el trámite",
    "numero_radicado": "2023005678"
}

response = requests.post(url, json=payload)
resultado = response.json()

if resultado['success']:
    print(f"Reporte creado: {resultado['reporte_id']}")
```

### Descargar Datos en Pandas

```python
import requests
import pandas as pd

url = "http://localhost:8000/api/v1/public/datos-abiertos"
params = {"formato": "json", "limit": 5000}

response = requests.get(url, params=params)
data = response.json()

df = pd.DataFrame(data['datos'])
print(f"Dataset descargado: {len(df)} registros")
print(df.head())

# Análisis
print(df['estado'].value_counts())
```

---

## Ejemplos con JavaScript/Fetch

```javascript
// Buscar trámites
async function buscarTramites() {
  const response = await fetch(
    'http://localhost:8000/api/v1/tramites/buscar?limit=50'
  );
  const data = await response.json();
  console.log(`Total: ${data.total}`);
  return data;
}

// Obtener estadísticas
async function obtenerEstadisticas() {
  const response = await fetch(
    'http://localhost:8000/api/v1/dashboard/estadisticas'
  );
  const stats = await response.json();
  return stats;
}

// Crear reporte
async function crearReporte(reporte) {
  const response = await fetch(
    'http://localhost:8000/api/v1/reportes/crear',
    {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify(reporte)
    }
  );
  const resultado = await response.json();
  return resultado;
}
```

---

## Documentación Interactiva

Accede a la documentación Swagger en:

**http://localhost:8000/docs**

Desde ahí puedes:
- Ver todos los endpoints disponibles
- Probar las APIs directamente
- Ver los esquemas de request/response
- Descargar el OpenAPI JSON
