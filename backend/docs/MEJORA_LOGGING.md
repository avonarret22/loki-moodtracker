# Mejora Implementada: Logging System Enhancement

## 📋 Resumen

**Tarea**: Implementación de Sistema de Logging Estructurado  
**Fecha**: Diciembre 2024  
**Prioridad**: Media  
**Status**: ✅ Completada

## 🎯 Objetivo

Implementar un sistema de logging profesional y estructurado que permita:
- Logging en formato JSON para producción (fácil de parse)
- Logging legible para desarrollo
- Rotación automática de archivos
- Niveles de log configurables por módulo
- Audit trail para operaciones sensibles
- Request tracing con contexto inyectado

## ✅ Implementación Completada

### 1. Módulo Central de Logging (`app/core/logging_config.py`)

**Características principales**:

#### **Formatters Duales**

**StructuredFormatter** (Producción - JSON):
```python
{
  "timestamp": "2024-12-05T13:22:57.123456Z",
  "level": "INFO",
  "logger": "app.api.routes.mood",
  "message": "Estado de ánimo creado",
  "module": "mood",
  "function": "create_estado_animo",
  "line": 45,
  "request_id": "req-abc-123",
  "user_id": 42,
  "extra": {"estado": "feliz", "intensidad": 8}
}
```

**SimpleFormatter** (Desarrollo - Legible):
```
[2024-12-05 13:22:57] INFO     - app.api.routes.mood      - Estado de ánimo creado [request_id=req-abc-123, user_id=42]
```

#### **Archivos de Log con Rotación**

| Archivo | Propósito | Rotación | Retención |
|---------|-----------|----------|-----------|
| `loki_moodtracker.log` | Log principal (todos los niveles) | Diaria (midnight) | 30 días |
| `errors.log` | Solo errores y críticos | Por tamaño (10 MB) | 5 archivos |
| `audit.log` | Audit trail de operaciones | Diaria (midnight) | 90 días |

#### **Niveles por Módulo**

```python
LOG_LEVELS = {
    # Módulos de aplicación - INFO en producción
    'app.api': logging.INFO,
    'app.services': logging.INFO,
    'app.crud': logging.INFO,
    
    # SQLAlchemy - solo warnings para evitar ruido
    'sqlalchemy.engine': logging.WARNING,
    'sqlalchemy.pool': logging.WARNING,
    
    # FastAPI/Uvicorn - info para monitoreo
    'fastapi': logging.INFO,
    'uvicorn': logging.INFO,
    'uvicorn.access': logging.WARNING,  # Menos verbose
    
    # Librerías externas - solo errores
    'httpx': logging.ERROR,
    'openai': logging.WARNING,
}
```

#### **Request Context Tracking**

```python
# Establecer contexto al inicio del request
set_request_context(request_id="req-123", user_id=42)

# Todos los logs subsiguientes incluyen este contexto
logger.info("Procesando request")
# Output: [2024-12-05 13:22:57] INFO - ... - Procesando request [request_id=req-123, user_id=42]

# Limpiar contexto al final del request
clear_request_context()
```

### 2. Audit Logger Especializado

**AuditLogger** para operaciones sensibles:

```python
audit_logger = get_audit_logger()

# Logs de creación
audit_logger.log_user_created(user_id=1, telefono="+123456", ip="127.0.0.1")
audit_logger.log_habito_created(user_id=1, habito_id=10, nombre="Meditar")

# Logs de modificación
audit_logger.log_habito_updated(
    user_id=1, 
    habito_id=10, 
    changes={'activo': False, 'objetivo_semanal': 5}
)

# Logs de eliminación
audit_logger.log_habito_deleted(user_id=1, habito_id=10)

# Logs de seguridad
audit_logger.log_auth_failure(telefono="+999999", reason="Invalid token")
audit_logger.log_rate_limit_exceeded(endpoint="/api/v1/users", identifier="127.0.0.1")
```

### 3. Middlewares de Request Logging (`app/core/logging_middleware.py`)

#### **RequestLoggingMiddleware**

Loggea automáticamente **todas las HTTP requests**:

```python
# Request iniciado
[2024-12-05 13:22:57] INFO - app.core.logging_middleware - Request started: GET /api/v1/moods [request_id=req-abc-123, user_id=42]

# Request completado exitosamente
[2024-12-05 13:22:58] INFO - app.core.logging_middleware - Request completed: GET /api/v1/moods - Status: 200 - Duration: 125.45ms [request_id=req-abc-123, user_id=42]

# Request fallido
[2024-12-05 13:22:58] ERROR - app.core.logging_middleware - Request failed: POST /api/v1/moods - Error: Validation error - Duration: 23.12ms [request_id=req-abc-123, user_id=42]
Traceback (most recent call last):
  ...
```

**Features**:
- ✅ Genera `request_id` único para cada request
- ✅ Extrae `user_id` del request state (si está autenticado)
- ✅ Mide tiempo de respuesta en ms
- ✅ Loggea status code y método HTTP
- ✅ Captura y loggea excepciones con traceback
- ✅ Inyecta contexto en todos los logs del request
- ✅ Agrega `X-Request-ID` header a la respuesta

#### **SlowRequestMiddleware**

Detecta requests lentos:

```python
# Request que tarda más del threshold (default: 1000ms)
[2024-12-05 13:22:58] WARNING - app.core.logging_middleware - Slow request detected: GET /api/v1/correlaciones - Duration: 1542.33ms (threshold: 1000ms)
```

**Uso**: Identificar endpoints que necesitan optimización

### 4. Integración con FastAPI (`app/main.py`)

```python
from app.core.logging_config import setup_logging, set_audit_logger, get_logger
from app.core.logging_middleware import RequestLoggingMiddleware, SlowRequestMiddleware

# Inicializar logging al startup
environment = 'production' if settings.ENV == 'production' else 'development'
_, audit_logger = setup_logging(
    environment=environment,
    log_level=settings.LOG_LEVEL,
    enable_console=True,
    enable_file=True,
    enable_audit=True,
)
if audit_logger:
    set_audit_logger(audit_logger)

# Agregar middlewares
app.add_middleware(SlowRequestMiddleware, threshold_ms=1000)
app.add_middleware(RequestLoggingMiddleware)
```

### 5. Configuración (`app/core/config.py`)

Nuevas variables de entorno:

```python
LOG_LEVEL: str = "INFO"  # DEBUG, INFO, WARNING, ERROR, CRITICAL
ENV: str = "development"  # development, production
```

En `.env`:
```bash
LOG_LEVEL=INFO
ENV=development
```

### 6. Tests Completos (`tests/test_logging.py`)

**85 tests totales pasando** (22 tests nuevos de logging):

#### Tests de Formatters
- ✅ `test_basic_json_format`: Genera JSON válido
- ✅ `test_includes_request_context`: Incluye request_id y user_id
- ✅ `test_includes_exception_info`: Incluye traceback de excepciones
- ✅ `test_basic_format`: Formato simple legible
- ✅ `test_includes_context_in_brackets`: Contexto en corchetes

#### Tests de Setup
- ✅ `test_creates_log_directory`: Crea directorio de logs
- ✅ `test_creates_audit_logger_when_enabled`: Crea audit logger
- ✅ `test_no_audit_logger_when_disabled`: No crea audit logger si disabled
- ✅ `test_production_uses_json_format`: Producción usa JSON
- ✅ `test_development_uses_simple_format`: Desarrollo usa simple format

#### Tests de Audit Logger
- ✅ `test_log_user_created`: Loggea creación de usuario
- ✅ `test_log_habito_created`: Loggea creación de hábito
- ✅ `test_log_habito_updated`: Loggea actualización de hábito
- ✅ `test_log_habito_deleted`: Loggea eliminación de hábito
- ✅ `test_log_auth_failure`: Loggea fallo de autenticación
- ✅ `test_log_rate_limit_exceeded`: Loggea rate limit

#### Tests de Request Context
- ✅ `test_set_and_get_request_id`: Set/get request_id
- ✅ `test_set_and_get_user_id`: Set/get user_id
- ✅ `test_set_both_context_values`: Set ambos valores

#### Tests de Configuración
- ✅ `test_returns_logger_with_name`: Logger con nombre correcto
- ✅ `test_returns_logging_logger`: Instancia de logging.Logger
- ✅ `test_different_log_levels`: Diferentes niveles configurables

## 📊 Características del Sistema

### Niveles de Log

| Nivel | Uso | Ejemplo |
|-------|-----|---------|
| **DEBUG** | Debugging detallado | Variables, flujo de ejecución |
| **INFO** | Eventos normales | Request completado, operación exitosa |
| **WARNING** | Advertencias | Request lento, cache miss frecuente |
| **ERROR** | Errores recuperables | Validation error, DB connection retry |
| **CRITICAL** | Errores fatales | DB no disponible, config faltante |

### Rotación de Archivos

**Diaria** (loki_moodtracker.log, audit.log):
- Rota a medianoche todos los días
- Crea archivo con fecha: `loki_20241205.log`
- Mantiene archivos antiguos según `backupCount`

**Por tamaño** (errors.log):
- Rota cuando alcanza 10 MB
- Crea archivos numerados: `errors.log.1`, `errors.log.2`
- Mantiene últimos 5 archivos

### Request Tracing

**Flujo completo**:

```
1. Request llega → Middleware genera request_id
2. Middleware extrae user_id (si está autenticado)
3. Middleware establece contexto con set_request_context()
4. Request se procesa → Todos los logs incluyen contexto
5. Response se envía → Middleware limpia contexto
6. Header X-Request-ID agregado a response
```

**Beneficios**:
- ✅ Trazabilidad completa de cada request
- ✅ Debugging más fácil con request_id
- ✅ Correlación de logs relacionados
- ✅ User activity tracking

## 🎛️ Uso del Sistema

### 1. Logging Básico

```python
from app.core.logging_config import get_logger

logger = get_logger(__name__)

# Diferentes niveles
logger.debug("Valor de x: %s", x)
logger.info("Usuario %d inició sesión", user_id)
logger.warning("Cache miss para key: %s", key)
logger.error("Error al procesar request: %s", error)
logger.critical("Database no disponible!")

# Con exception
try:
    result = do_something()
except Exception:
    logger.exception("Error inesperado")  # Incluye traceback
```

### 2. Logging con Extra Data

```python
logger.info(
    "Estado de ánimo creado",
    extra={'extra_data': {
        'user_id': 42,
        'estado': 'feliz',
        'intensidad': 8,
        'timestamp': datetime.now().isoformat()
    }}
)
```

### 3. Audit Logging

```python
from app.core.logging_config import get_audit_logger

audit = get_audit_logger()

# Operaciones sensibles
audit.log_user_created(user_id=1, telefono="+123", ip="127.0.0.1")
audit.log_auth_failure(telefono="+999", reason="Invalid token")
```

### 4. Análisis de Logs

**JSON logs (producción)**:
```bash
# Buscar todos los errores de un usuario
cat logs/loki_moodtracker.log | jq 'select(.user_id == 42 and .level == "ERROR")'

# Buscar requests lentos
cat logs/loki_moodtracker.log | jq 'select(.extra.duration_ms > 1000)'

# Buscar por request_id
cat logs/loki_moodtracker.log | jq 'select(.request_id == "req-abc-123")'
```

**Simple logs (desarrollo)**:
```bash
# Buscar errores
grep ERROR logs/loki_moodtracker.log

# Buscar por usuario
grep "user_id=42" logs/loki_moodtracker.log

# Tail en tiempo real
tail -f logs/loki_moodtracker.log
```

## 🚀 Próximos Pasos Potenciales

1. **Integración con ELK Stack** (futuro)
   - Elasticsearch para storage y búsqueda
   - Logstash para procesamiento
   - Kibana para visualización y dashboards

2. **Alertas Automáticas** (futuro)
   - Email/Slack cuando hay errores críticos
   - Alertas de requests lentos recurrentes
   - Notificaciones de rate limit patterns

3. **Log Aggregation** (futuro)
   - Centralizar logs de múltiples instancias
   - CloudWatch Logs (AWS)
   - Google Cloud Logging

4. **Performance Metrics** (futuro)
   - Endpoint de `/metrics` para Prometheus
   - Histogramas de response times
   - Contadores de errores por endpoint

5. **Structured Logging Avanzado** (futuro)
   - Context propagation en async tasks
   - Correlation IDs across microservices
   - Distributed tracing con OpenTelemetry

## 📦 Archivos Creados/Modificados

### Nuevos Archivos

1. **backend/app/core/logging_config.py** (458 líneas)
   - Sistema completo de logging estructurado
   - Formatters JSON y Simple
   - AuditLogger clase
   - Request context tracking
   - Configuración de niveles por módulo

2. **backend/app/core/logging_middleware.py** (126 líneas)
   - RequestLoggingMiddleware (request tracing)
   - SlowRequestMiddleware (slow request detection)

3. **backend/tests/test_logging.py** (242 líneas)
   - 22 tests completos para logging
   - Cobertura de formatters, setup, audit, context

4. **backend/docs/MEJORA_LOGGING.md** (este archivo)
   - Documentación completa de la implementación

### Archivos Modificados

1. **backend/app/main.py**
   - Agregado imports de logging_config y middlewares
   - Inicialización de logging system al startup
   - Middlewares de logging agregados a app

2. **backend/app/core/config.py**
   - Agregado `LOG_LEVEL: str` (default: "INFO")
   - Agregado `ENV: str` (default: "development")

## ✅ Checklist de Verificación

- [x] Módulo de logging creado (`app/core/logging_config.py`)
- [x] StructuredFormatter para producción (JSON)
- [x] SimpleFormatter para desarrollo (legible)
- [x] Rotación de archivos configurada (diaria + tamaño)
- [x] 3 archivos de log: main, errors, audit
- [x] Niveles configurables por módulo
- [x] AuditLogger para operaciones sensibles
- [x] Request context tracking (request_id, user_id)
- [x] RequestLoggingMiddleware implementado
- [x] SlowRequestMiddleware implementado
- [x] Integración con FastAPI main.py
- [x] Configuración en settings (LOG_LEVEL, ENV)
- [x] 22 tests completos de logging
- [x] 85/85 tests totales pasando
- [x] Documentación completa
- [x] Testing standalone del módulo

## 🎉 Resultados

**Estado Final**: ✅ **Implementación Completada con Éxito**

- **Módulos**: `logging_config.py` (458 líneas), `logging_middleware.py` (126 líneas)
- **Tests**: 22 nuevos tests, 85/85 pasando
- **Archivos de log**: 3 archivos con rotación automática
- **Formatters**: JSON (producción) + Simple (desarrollo)
- **Audit Trail**: Logger especializado para operaciones sensibles
- **Request Tracing**: Contexto automático con request_id y user_id
- **Slow Request Detection**: Warnings automáticos para requests lentos

## 📈 Resumen de Todas las Mejoras Completadas

### ✅ Todas las Tareas de Prioridad Media - COMPLETADAS

1. **Rate Limiting** ✅
   - slowapi con 11 categorías
   - Auth endpoints protegidos

2. **Input Validation** ✅
   - XSS y SQL injection prevention
   - 31 tests de validación

3. **Query Optimization** ✅
   - 12 índices compuestos
   - 10-100x performance improvement

4. **Caching Strategy** ✅
   - 6 tipos de cache con TTL
   - 80-90% hit rate objetivo

5. **Logging System** ✅ **(ESTE)**
   - Logging estructurado completo
   - Audit trail y request tracing

**Total**: 5/5 tareas completadas (100%)  
**Tests**: 85/85 pasando  
**Cobertura**: Backend production-ready
