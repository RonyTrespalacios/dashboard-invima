# Guía de Despliegue - Dashboard INVIMA

## 📋 Tabla de Contenidos

1. [Despliegue Local con Docker](#despliegue-local-con-docker)
2. [Despliegue en Producción](#despliegue-en-producción)
3. [Variables de Entorno](#variables-de-entorno)
4. [Monitoreo y Logs](#monitoreo-y-logs)
5. [Troubleshooting](#troubleshooting)

---

## 🐳 Despliegue Local con Docker

### Prerrequisitos

- Docker Desktop instalado
- Docker Compose v2+
- Git (opcional)

### Pasos

1. **Navegar al directorio del proyecto**
```powershell
cd dashboard-invima
```

2. **Revisar configuración en `.env`**
```powershell
# Editar si es necesario
notepad .env
```

3. **Construir y levantar servicios**
```powershell
docker-compose up --build -d
```

4. **Verificar que los contenedores estén corriendo**
```powershell
docker-compose ps
```

Deberías ver:
```
NAME                STATUS      PORTS
invima_fastapi      running     0.0.0.0:8000->8000/tcp
invima_streamlit    running     0.0.0.0:8501->8501/tcp
```

5. **Acceder a las aplicaciones**
- Frontend: http://localhost:8501
- Backend: http://localhost:8000
- Docs API: http://localhost:8000/docs

### Comandos Útiles

```powershell
# Ver logs en tiempo real
docker-compose logs -f

# Ver logs de un servicio específico
docker-compose logs -f fastapi
docker-compose logs -f streamlit

# Detener servicios
docker-compose down

# Reiniciar servicios
docker-compose restart

# Reconstruir y reiniciar
docker-compose up --build -d
```

---

## 🌐 Despliegue en Producción

### Opción 1: Cloud con Docker (AWS, Azure, GCP)

#### AWS ECS (Elastic Container Service)

1. **Preparar imágenes Docker**
```bash
# Tag para ECR
docker tag dashboard-invima-fastapi:latest <aws-account>.dkr.ecr.<region>.amazonaws.com/invima-fastapi:latest
docker tag dashboard-invima-streamlit:latest <aws-account>.dkr.ecr.<region>.amazonaws.com/invima-streamlit:latest

# Push a ECR
docker push <aws-account>.dkr.ecr.<region>.amazonaws.com/invima-fastapi:latest
docker push <aws-account>.dkr.ecr.<region>.amazonaws.com/invima-streamlit:latest
```

2. **Crear task definition en ECS**
3. **Configurar Application Load Balancer**
4. **Configurar variables de entorno en ECS**

#### Azure Container Instances

```bash
# Crear grupo de recursos
az group create --name invima-rg --location eastus

# Crear registro de contenedores
az acr create --resource-group invima-rg --name invimaacr --sku Basic

# Hacer push de imágenes
az acr login --name invimaacr
docker tag dashboard-invima-fastapi invimaacr.azurecr.io/fastapi:latest
docker push invimaacr.azurecr.io/fastapi:latest

# Crear container instances
az container create \
  --resource-group invima-rg \
  --name invima-app \
  --image invimaacr.azurecr.io/fastapi:latest \
  --dns-name-label invima-dashboard \
  --ports 8000
```

### Opción 2: Heroku

1. **Instalar Heroku CLI**
2. **Login**
```bash
heroku login
```

3. **Crear apps**
```bash
heroku create invima-api
heroku create invima-dashboard
```

4. **Deploy backend**
```bash
cd app
git init
heroku git:remote -a invima-api
git add .
git commit -m "Deploy"
git push heroku main
```

5. **Configurar variables de entorno**
```bash
heroku config:set SOCRATA_API_ENDPOINT=https://www.datos.gov.co/api/v3/views/48fq-mxnm/query.json
```

### Opción 3: DigitalOcean App Platform

1. **Conectar repositorio de GitHub**
2. **Configurar build commands**
   - Backend: `pip install -r requirements.txt`
   - Frontend: `pip install -r requirements.txt`
3. **Configurar run commands**
   - Backend: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
   - Frontend: `streamlit run streamlit_app/Home.py --server.port $PORT`

---

## 🔐 Variables de Entorno

### Desarrollo Local

```env
SOCRATA_API_ENDPOINT=https://www.datos.gov.co/api/v3/views/48fq-mxnm/query.json
SOCRATA_DOMAIN=www.datos.gov.co
SOCRATA_APP_TOKEN=
FASTAPI_HOST=0.0.0.0
FASTAPI_PORT=8000
API_PREFIX=/api/v1
```

### Producción

Agregar además:

```env
# CORS
CORS_ORIGINS=["https://tu-dominio.com"]

# App Token de Socrata (Recomendado en producción)
SOCRATA_APP_TOKEN=<tu-token>

# Logging
LOG_LEVEL=INFO

# Performance
WORKERS=4
```

Para obtener un App Token de Socrata:
1. Visita https://datos.gov.co
2. Crea una cuenta
3. Genera un Application Token
4. Configura en `.env`

---

## 📊 Monitoreo y Logs

### Docker Logs

```powershell
# Logs de todos los servicios
docker-compose logs

# Logs con timestamp
docker-compose logs -t

# Seguir logs en tiempo real
docker-compose logs -f

# Últimas 100 líneas
docker-compose logs --tail=100
```

### Health Checks

Configura health checks en producción:

```yaml
# docker-compose.yml
services:
  fastapi:
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
```

### Monitoreo con Prometheus + Grafana (Opcional)

```yaml
# Agregar a docker-compose.yml
services:
  prometheus:
    image: prom/prometheus
    ports:
      - "9090:9090"
    volumes:
      - ./prometheus.yml:/etc/prometheus/prometheus.yml
  
  grafana:
    image: grafana/grafana
    ports:
      - "3000:3000"
```

---

## 🔧 Troubleshooting

### Problema: Contenedores no inician

**Síntoma:** `docker-compose up` falla

**Solución:**
```powershell
# Limpiar contenedores antiguos
docker-compose down -v

# Limpiar caché de build
docker system prune -a

# Reconstruir desde cero
docker-compose up --build --force-recreate
```

### Problema: Error de conexión a la API

**Síntoma:** "Error al conectar con la API"

**Solución:**
1. Verificar que el backend esté corriendo
```powershell
curl http://localhost:8000/health
```

2. Verificar variables de entorno
```powershell
docker-compose exec fastapi env | grep SOCRATA
```

3. Verificar logs
```powershell
docker-compose logs fastapi
```

### Problema: Puerto ocupado

**Síntoma:** "Port 8000 is already allocated"

**Solución:**
```powershell
# Ver qué proceso usa el puerto
netstat -ano | findstr :8000

# Matar el proceso (si es necesario)
taskkill /PID <PID> /F

# O cambiar el puerto en docker-compose.yml
```

### Problema: Streamlit no se conecta al backend

**Síntoma:** "Connection refused" en el frontend

**Solución:**
1. Verificar que ambos servicios estén en la misma red Docker
2. Usar el nombre del servicio en lugar de localhost:
```python
# En Streamlit
FASTAPI_URL = os.getenv("FASTAPI_URL", "http://fastapi:8000")
```

### Problema: Datos no se cargan

**Síntoma:** "No se encontraron datos"

**Solución:**
1. Probar la API de Socrata directamente:
```powershell
curl "https://www.datos.gov.co/api/v3/views/48fq-mxnm/query.json?$select=*&$limit=1"
```

2. Verificar el script de prueba:
```powershell
python test_api.py
```

---

## 📈 Optimizaciones de Producción

### 1. Usar Gunicorn con FastAPI

```dockerfile
# Dockerfile.fastapi
CMD ["gunicorn", "app.main:app", "-w", "4", "-k", "uvicorn.workers.UvicornWorker", "--bind", "0.0.0.0:8000"]
```

### 2. Implementar Cache con Redis

```yaml
services:
  redis:
    image: redis:alpine
    ports:
      - "6379:6379"
```

### 3. Rate Limiting

Agregar middleware de rate limiting en FastAPI

### 4. CDN para Assets

Servir archivos estáticos desde CDN (CloudFlare, AWS CloudFront)

### 5. HTTPS con Nginx

```yaml
services:
  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
      - ./ssl:/etc/nginx/ssl
```

---

## 🔒 Seguridad

### Checklist de Seguridad

- [ ] Variables sensibles en variables de entorno (no en código)
- [ ] HTTPS habilitado en producción
- [ ] CORS configurado correctamente
- [ ] Rate limiting implementado
- [ ] Validación de inputs
- [ ] Logs sin información sensible
- [ ] Actualizaciones de dependencias regulares
- [ ] Secrets management (AWS Secrets Manager, Azure Key Vault)

### Escaneo de Vulnerabilidades

```powershell
# Escanear dependencias Python
pip-audit

# Escanear imágenes Docker
docker scan dashboard-invima-fastapi:latest
```

---

## 📝 Checklist de Despliegue

### Pre-despliegue

- [ ] Tests unitarios pasan
- [ ] Variables de entorno configuradas
- [ ] Backups de datos (si aplica)
- [ ] Documentación actualizada

### Despliegue

- [ ] Build de imágenes exitoso
- [ ] Servicios levantados correctamente
- [ ] Health checks funcionando
- [ ] API responde correctamente
- [ ] Frontend carga sin errores

### Post-despliegue

- [ ] Verificar métricas
- [ ] Revisar logs
- [ ] Smoke tests
- [ ] Notificar a stakeholders

---

## 📞 Soporte

Para problemas o consultas:
- Documentación: `README.md`
- Ejemplos de API: `EJEMPLOS_API.md`
- Reportar bugs: Sistema de reportes en la app
