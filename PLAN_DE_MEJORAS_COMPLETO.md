# PLAN DE MEJORAS COMPLETO - LOKI MOOD TRACKER

**Fecha:** 2025-10-25
**Versión:** 1.0
**Evaluación General:** Backend 6.5/10 | Frontend 6.5/10

---

## RESUMEN EJECUTIVO

### Fortalezas del Proyecto
- Arquitectura backend bien estructurada (Routes, CRUD, Services, Models)
- Sistema innovador de niveles de confianza para personalización de tono
- Frontend moderno con Next.js 16 y React 19
- Integración multi-canal (Meta WhatsApp, Twilio)
- Análisis de patrones emocionales con correlaciones

### Debilidades Críticas Identificadas
1. **Seguridad:** CORS abierto, sin validación de firmas de webhook, JWT inseguro
2. **Testing:** Cobertura <1% en backend, 0% en frontend
3. **Autenticación:** Validación solo en cliente, tokens en URL
4. **Performance:** Sin caché, queries N+1 potenciales
5. **Base de datos:** Sin migraciones versionadas, transacciones implícitas

---

## ESTRUCTURA DEL PLAN

El plan está organizado en 4 niveles de prioridad:
- **CRÍTICA:** Debe implementarse inmediatamente (Semana 1-2)
- **ALTA:** Implementar en las próximas 2-4 semanas
- **MEDIA:** Implementar en 1-2 meses
- **BAJA:** Mejoras incrementales (2+ meses)

---

# MEJORAS BACKEND

## 🔴 PRIORIDAD CRÍTICA (Semana 1-2)

### 1. Seguridad: Configuración CORS Restrictiva

**Problema:** `allow_origins=["*"]` permite requests desde cualquier origen

**Solución:**
```python
# backend/app/main.py

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        settings.DASHBOARD_URL,  # https://loki-dashboard.vercel.app
        "http://localhost:3000",  # Desarrollo local
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["Authorization", "Content-Type"],
)
```

**Impacto:** Previene CSRF y accesos no autorizados
**Tiempo estimado:** 30 minutos
**Archivo:** `backend/app/main.py:35`

---

### 2. Seguridad: Validación de Firmas de Webhook

**Problema:** Webhooks de WhatsApp no validan firmas, permitiendo mensajes falsos

**Solución:**
```python
# backend/app/services/whatsapp_service.py

import hmac
import hashlib

def verify_webhook_signature(
    payload: str,
    signature: str,
    secret: str
) -> bool:
    """Valida firma X-Hub-Signature-256 de Meta"""
    expected_signature = "sha256=" + hmac.new(
        secret.encode(),
        payload.encode(),
        hashlib.sha256
    ).hexdigest()

    return hmac.compare_digest(expected_signature, signature)

# En route /whatsapp/webhook
@router.post("/webhook")
async def receive_webhook(request: Request):
    # Obtener firma del header
    signature = request.headers.get("X-Hub-Signature-256")
    if not signature:
        raise HTTPException(401, "Missing signature")

    # Leer body raw
    body = await request.body()

    # Validar firma
    if not verify_webhook_signature(
        body.decode(),
        signature,
        settings.WHATSAPP_VERIFY_TOKEN
    ):
        raise HTTPException(401, "Invalid signature")

    # Continuar con procesamiento...
```

**Impacto:** Previene spoofing de mensajes
**Tiempo estimado:** 2 horas
**Archivos:** `backend/app/services/whatsapp_service.py`, `backend/app/api/routes/whatsapp.py:42`

---

### 3. Seguridad: JWT Secret Key Segura

**Problema:** Secret key tiene valor default inseguro

**Solución:**
```python
# backend/app/core/config.py

class Settings(BaseSettings):
    SECRET_KEY: str = Field(..., min_length=32)  # Requerido, mínimo 32 chars

    @validator('SECRET_KEY')
    def validate_secret_key(cls, v):
        if v == "loki-super-secret-key-change-in-production-please":
            raise ValueError(
                "Debes cambiar SECRET_KEY en producción. "
                "Genera uno nuevo con: openssl rand -hex 32"
            )
        return v

# .env.example
# SECRET_KEY=  # Generar con: openssl rand -hex 32
```

**Impacto:** Previene ataques de fuerza bruta en tokens
**Tiempo estimado:** 15 minutos
**Archivo:** `backend/app/core/config.py:28`

---

### 4. Logging Centralizado

**Problema:** Uso de `print()` para debugging en producción

**Solución:**
```python
# backend/app/core/logger.py

import logging
import sys
from datetime import datetime

def setup_logger(name: str) -> logging.Logger:
    logger = logging.getLogger(name)

    # Handler para consola
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)

    # Handler para archivo
    file_handler = logging.FileHandler(
        f'logs/loki_{datetime.now().strftime("%Y%m%d")}.log'
    )
    file_handler.setLevel(logging.DEBUG)

    # Formato
    formatter = logging.Formatter(
        '%(asctime)s | %(name)s | %(levelname)s | %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    console_handler.setFormatter(formatter)
    file_handler.setFormatter(formatter)

    logger.addHandler(console_handler)
    logger.addHandler(file_handler)
    logger.setLevel(logging.DEBUG)

    return logger

# Uso en servicios
from app.core.logger import setup_logger

logger = setup_logger(__name__)

# Reemplazar todos los print() con:
logger.info("✅ Token generado para usuario %s", usuario_id)
logger.error("❌ Error en chat: %s", str(e))
logger.warning("⚠️ Nivel de confianza bajo")
```

**Impacto:** Mejor debugging, auditoría, monitoreo
**Tiempo estimado:** 3 horas (crear + refactor)
**Archivos:** Crear `backend/app/core/logger.py`, refactor en todos los servicios

---

### 5. Rate Limiting en Webhooks

**Problema:** Sin protección contra DDoS en endpoints públicos

**Solución:**
```python
# requirements.txt
slowapi==0.1.9

# backend/app/main.py
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# En routes
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)

@router.post("/webhook")
@limiter.limit("100/minute")  # Máximo 100 requests por minuto por IP
async def receive_webhook(request: Request):
    ...
```

**Impacto:** Previene DDoS y abuso
**Tiempo estimado:** 1 hora
**Archivos:** `backend/app/main.py:52`, `backend/app/api/routes/whatsapp.py:42`, `backend/app/api/routes/twilio.py:28`

---

## 🟠 PRIORIDAD ALTA (Semana 2-4)

### 6. Testing: Tests Unitarios Básicos

**Problema:** Cobertura <1%, sin tests de servicios críticos

**Solución:**
```python
# tests/test_auth_service.py
import pytest
from app.services.auth_service import AuthService

def test_generate_token_success():
    """Test que el token se genera correctamente"""
    auth = AuthService()
    token = auth.generate_dashboard_token(1, "+5491165992142")

    assert token is not None
    assert isinstance(token, str)
    assert len(token) > 50  # JWT es largo

def test_verify_token_valid():
    """Test que un token válido se verifica"""
    auth = AuthService()
    token = auth.generate_dashboard_token(1, "+5491165992142")

    data = auth.verify_token(token)

    assert data is not None
    assert data['usuario_id'] == 1
    assert data['telefono'] == "+5491165992142"
    assert data['type'] == 'dashboard_access'

def test_verify_token_expired():
    """Test que un token expirado falla"""
    auth = AuthService()
    expired_token = "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."  # Token viejo

    data = auth.verify_token(expired_token)

    assert data is None

# tests/test_trust_service.py
from app.services.trust_level_service import TrustLevelService

@pytest.mark.parametrize("interacciones,nivel_esperado", [
    (5, 1),    # Conociendo
    (15, 2),   # Estableciendo
    (40, 3),   # Construyendo
    (75, 4),   # Consolidado
    (120, 5),  # Íntimo
])
def test_calculate_trust_level(interacciones, nivel_esperado):
    """Test cálculo de niveles de confianza"""
    trust_service = TrustLevelService()
    nivel = trust_service.calculate_trust_level(interacciones)

    assert nivel == nivel_esperado

# tests/test_pattern_analysis.py
from app.services.pattern_analysis import PatternAnalysisService

def test_insufficient_data():
    """Test que retorna error con pocos datos"""
    # Mock database con solo 2 estados de ánimo
    result = analyze_user_patterns(db, usuario_id=1, days_lookback=30)

    assert result['has_enough_data'] is False
    assert result['data_points'] < 5
```

**Meta:** Lograr 40% de cobertura en 2 semanas

**Tiempo estimado:** 12 horas
**Archivos:** `tests/test_auth_service.py`, `tests/test_trust_service.py`, `tests/test_pattern_analysis.py`, `tests/test_crud_mood.py`

---

### 7. Base de Datos: Transacciones Explícitas

**Problema:** Operaciones críticas sin rollback en caso de error

**Solución:**
```python
# backend/app/api/routes/chat.py

@router.post("/api/v1/chat/")
async def chat_with_loki(chat_msg: ChatMessage, db: Session = Depends(get_db)):
    try:
        # Iniciar transacción explícita
        with db.begin_nested():
            # 1. Guardar conversación
            conversacion = ConversacionContexto(
                usuario_id=usuario.id,
                mensaje_usuario=chat_msg.mensaje,
                respuesta_loki=respuesta_texto,
                entidades_extraidas=json.dumps(entidades),
                categorias_detectadas=json.dumps(categorias)
            )
            db.add(conversacion)
            db.flush()  # Obtener ID sin commit

            # 2. Registrar mood si se detectó
            if contexto_extraido.get('mood_level'):
                mood = EstadoAnimo(
                    usuario_id=usuario.id,
                    nivel=contexto_extraido['mood_level'],
                    notas_texto=chat_msg.mensaje,
                    contexto_extraido=json.dumps(contexto_extraido)
                )
                db.add(mood)

            # 3. Registrar hábitos
            for habit_name in habits_mentioned:
                # ... crear/buscar hábito
                registro = RegistroHabito(...)
                db.add(registro)

            # Commit si todo salió bien
            db.commit()

    except Exception as e:
        db.rollback()
        logger.error(f"Error en chat, rollback: {e}")
        raise HTTPException(
            status_code=500,
            detail="Error procesando mensaje. Intenta de nuevo."
        )

    return {"respuesta": respuesta_texto, "contexto": contexto_extraido}
```

**Impacto:** Previene datos inconsistentes
**Tiempo estimado:** 4 horas
**Archivo:** `backend/app/api/routes/chat.py:48`

---

### 8. Validaciones de Entrada Robustas

**Problema:** Sin validación de longitud, sanitización limitada

**Solución:**
```python
# backend/app/schemas/mood.py

from pydantic import BaseModel, Field, validator

class ChatMessage(BaseModel):
    usuario_id: int = Field(..., gt=0, description="ID del usuario")
    mensaje: str = Field(
        ...,
        min_length=1,
        max_length=2000,
        description="Mensaje del usuario"
    )

    @validator('mensaje')
    def validate_mensaje(cls, v):
        # Sanitizar HTML
        v = v.replace('<', '&lt;').replace('>', '&gt;')

        # Validar que no sea solo espacios
        if not v.strip():
            raise ValueError('El mensaje no puede estar vacío')

        return v.strip()

class UsuarioCreate(BaseModel):
    nombre: str = Field(..., min_length=2, max_length=100)
    telefono: str = Field(..., regex=r'^\+?[1-9]\d{1,14}$')  # E.164 format

    @validator('telefono')
    def validate_telefono(cls, v):
        # Normalizar formato
        if not v.startswith('+'):
            v = '+' + v
        return v

class EstadoAnimoCreate(BaseModel):
    nivel: int = Field(..., ge=1, le=10, description="Nivel de ánimo 1-10")
    notas_texto: str = Field(default="", max_length=5000)

    @validator('notas_texto')
    def sanitize_notas(cls, v):
        # Limitar caracteres especiales
        import re
        v = re.sub(r'[^\w\s.,!?¿¡\-áéíóúÁÉÍÓÚñÑ]', '', v)
        return v[:5000]  # Hard limit
```

**Impacto:** Previene XSS, inyección SQL, datos malformados
**Tiempo estimado:** 3 horas
**Archivos:** `backend/app/schemas/mood.py`, `backend/app/schemas/__init__.py`

---

### 9. Índices de Base de Datos Optimizados

**Problema:** Falta de índices en foreign keys causa queries lentas

**Solución:**
```python
# backend/app/models/mood.py

from sqlalchemy import Index

class Habito(Base):
    __tablename__ = 'habitos'

    __table_args__ = (
        # Índice compuesto para búsquedas frecuentes
        Index('ix_usuario_nombre', 'usuario_id', 'nombre_habito'),
        Index('ix_usuario_activo', 'usuario_id', 'activo'),
    )

class RegistroHabito(Base):
    __tablename__ = 'registros_habitos'

    __table_args__ = (
        Index('ix_usuario_timestamp', 'usuario_id', 'timestamp'),
        Index('ix_habito_timestamp', 'habito_id', 'timestamp'),
    )

class ConversacionContexto(Base):
    __tablename__ = 'conversaciones_contexto'

    __table_args__ = (
        Index('ix_usuario_timestamp_desc', 'usuario_id', 'timestamp', postgresql_ops={'timestamp': 'DESC'}),
    )

# Migración para crear índices
# migrations/add_indexes.sql
CREATE INDEX CONCURRENTLY IF NOT EXISTS ix_usuario_nombre
    ON habitos(usuario_id, nombre_habito);

CREATE INDEX CONCURRENTLY IF NOT EXISTS ix_usuario_timestamp_desc
    ON conversaciones_contexto(usuario_id, timestamp DESC);
```

**Impacto:** Mejora velocidad de queries en 10-100x
**Tiempo estimado:** 2 horas
**Archivos:** `backend/app/models/mood.py`, crear `migrations/add_indexes.sql`

---

### 10. Sistema de Migraciones Versionadas

**Problema:** Creación automática de tablas puede sobrescribir datos

**Solución:**
```bash
# Inicializar Alembic
cd backend
alembic init alembic

# alembic/env.py
from app.models.mood import Base
target_metadata = Base.metadata

# Crear migración inicial
alembic revision --autogenerate -m "Initial schema"

# Aplicar migración
alembic upgrade head

# Para cambios futuros
alembic revision --autogenerate -m "Add trust level fields"
alembic upgrade head

# Rollback si es necesario
alembic downgrade -1
```

```python
# backend/app/main.py
# ELIMINAR esto:
# Base.metadata.create_all(bind=engine)

# En su lugar, confiar en migraciones de Alembic
```

**Impacto:** Control de versiones de BD, rollbacks seguros
**Tiempo estimado:** 4 horas
**Archivos:** Crear `alembic/`, modificar `backend/app/main.py:68`

---

## 🟡 PRIORIDAD MEDIA (1-2 meses)

### 11. Caché con Redis

**Problema:** Recalcula patrones y configuraciones en cada request

**Solución:**
```python
# requirements.txt
redis==5.0.0
hiredis==2.3.2

# backend/app/core/cache.py
import redis
import json
from functools import wraps

redis_client = redis.Redis(
    host=settings.REDIS_HOST,
    port=settings.REDIS_PORT,
    db=0,
    decode_responses=True
)

def cache(expire: int = 300):
    """Decorator para cachear resultados"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Generar cache key
            cache_key = f"{func.__name__}:{str(args)}:{str(kwargs)}"

            # Intentar obtener del cache
            cached = redis_client.get(cache_key)
            if cached:
                return json.loads(cached)

            # Si no está en cache, ejecutar función
            result = await func(*args, **kwargs)

            # Guardar en cache
            redis_client.setex(
                cache_key,
                expire,
                json.dumps(result)
            )

            return result
        return wrapper
    return decorator

# Uso
@cache(expire=600)  # 10 minutos
async def analyze_user_patterns(db, usuario_id: int, days_lookback: int):
    # ... análisis costoso
    return patterns

@cache(expire=3600)  # 1 hora
async def get_trust_level_info(nivel: int):
    # ... obtener info de nivel
    return info
```

**Impacto:** Reduce latencia en 80-90% para datos frecuentes
**Tiempo estimado:** 6 horas
**Archivos:** Crear `backend/app/core/cache.py`, agregar decoradores en servicios

---

### 12. Paginación Cursor-Based

**Problema:** Endpoints retornan todos los datos, potencial OOM

**Solución:**
```python
# backend/app/api/routes/mood.py

from typing import Optional
from pydantic import BaseModel

class PaginatedResponse(BaseModel):
    items: list
    next_cursor: Optional[str] = None
    has_more: bool

@router.get("/api/v1/usuarios/{usuario_id}/estados_animo/")
def read_estados_animo(
    usuario_id: int,
    limit: int = Query(50, ge=1, le=100),
    cursor: Optional[str] = None,
    db: Session = Depends(get_db)
) -> PaginatedResponse:
    """Obtener estados de ánimo con paginación cursor-based"""

    query = db.query(EstadoAnimo).filter(
        EstadoAnimo.usuario_id == usuario_id
    ).order_by(EstadoAnimo.timestamp.desc())

    # Si hay cursor, filtrar
    if cursor:
        cursor_timestamp = datetime.fromisoformat(cursor)
        query = query.filter(EstadoAnimo.timestamp < cursor_timestamp)

    # Obtener limit + 1 para saber si hay más
    items = query.limit(limit + 1).all()

    has_more = len(items) > limit
    if has_more:
        items = items[:limit]

    # Generar siguiente cursor
    next_cursor = None
    if has_more and items:
        next_cursor = items[-1].timestamp.isoformat()

    return PaginatedResponse(
        items=[serialize_mood(m) for m in items],
        next_cursor=next_cursor,
        has_more=has_more
    )
```

**Impacto:** Soporta millones de registros sin degradación
**Tiempo estimado:** 4 horas
**Archivos:** `backend/app/api/routes/mood.py:64`, `backend/app/api/routes/analytics.py:28`

---

### 13. Tests de Integración E2E

**Problema:** No hay tests de flujos completos

**Solución:**
```python
# tests/test_integration_chat_flow.py

import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_full_chat_flow():
    """Test flujo completo: crear usuario → chat → obtener mood"""

    # 1. Crear usuario
    response = client.post("/api/v1/usuarios/", json={
        "nombre": "Test User",
        "telefono": "+5491165992142"
    })
    assert response.status_code == 200
    usuario_id = response.json()['id']

    # 2. Enviar mensaje de chat
    response = client.post("/api/v1/chat/", json={
        "usuario_id": usuario_id,
        "mensaje": "Hoy me siento muy feliz, hice ejercicio"
    })
    assert response.status_code == 200
    respuesta = response.json()
    assert 'respuesta' in respuesta

    # 3. Verificar que se registró el mood
    response = client.get(f"/api/v1/usuarios/{usuario_id}/estados_animo/")
    assert response.status_code == 200
    moods = response.json()
    assert len(moods) > 0
    assert moods[0]['nivel'] >= 7  # Feliz debería ser alto

    # 4. Verificar que se registró el hábito
    response = client.get(f"/api/v1/usuarios/{usuario_id}/habitos/")
    assert response.status_code == 200
    habitos = response.json()
    assert any(h['nombre_habito'] == 'ejercicio' for h in habitos)

def test_trust_level_evolution():
    """Test que el nivel de confianza evoluciona"""
    # ... similar
```

**Tiempo estimado:** 8 horas
**Archivos:** Crear `tests/test_integration_*.py`

---

### 14. Monitoreo y Alertas con Sentry

**Solución:**
```python
# requirements.txt
sentry-sdk[fastapi]==1.40.0

# backend/app/main.py
import sentry_sdk
from sentry_sdk.integrations.fastapi import FastApiIntegration

sentry_sdk.init(
    dsn=settings.SENTRY_DSN,
    environment=settings.ENVIRONMENT,
    traces_sample_rate=0.1,  # 10% de requests
    profiles_sample_rate=0.1,
    integrations=[FastApiIntegration()],
    before_send=filter_sensitive_data,
)

def filter_sensitive_data(event, hint):
    """Filtrar datos sensibles de eventos"""
    if 'request' in event:
        # Remover tokens
        if 'headers' in event['request']:
            event['request']['headers'].pop('Authorization', None)

        # Remover datos de body sensibles
        if 'data' in event['request']:
            if isinstance(event['request']['data'], dict):
                event['request']['data'].pop('telefono', None)

    return event

# Capturar errores manualmente
try:
    result = risky_operation()
except Exception as e:
    sentry_sdk.capture_exception(e)
    raise
```

**Impacto:** Detección proactiva de errores en producción
**Tiempo estimado:** 2 horas
**Archivo:** `backend/app/main.py:28`

---

## 🟢 PRIORIDAD BAJA (2+ meses)

### 15. Documentación Automática con Swagger

**Solución:**
```python
# backend/app/main.py

app = FastAPI(
    title="Loki Mood Tracker API",
    description="API para asistente emocional conversacional",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_tags=[
        {
            "name": "auth",
            "description": "Autenticación y tokens"
        },
        {
            "name": "moods",
            "description": "Estados de ánimo"
        },
        {
            "name": "patterns",
            "description": "Análisis de patrones"
        }
    ]
)

# En routes
@router.post(
    "/api/v1/chat/",
    tags=["chat"],
    summary="Enviar mensaje a Loki",
    description="Procesa un mensaje del usuario y genera respuesta inteligente",
    response_description="Respuesta de Loki con contexto extraído"
)
async def chat_with_loki(
    chat_msg: ChatMessage,
    db: Session = Depends(get_db)
) -> ChatResponse:
    """
    Procesa mensaje del usuario:

    1. Actualiza nivel de confianza
    2. Genera respuesta adaptada
    3. Registra mood si se detecta
    4. Registra hábitos mencionados

    **Ejemplo:**
    ```json
    {
        "usuario_id": 1,
        "mensaje": "Hoy me siento bien, hice ejercicio"
    }
    ```
    """
    ...
```

**Tiempo estimado:** 4 horas

---

### 16. Background Tasks para Procesamiento Asíncrono

**Solución:**
```python
# requirements.txt
celery==5.3.4
flower==2.0.1

# backend/app/core/celery.py
from celery import Celery

celery_app = Celery(
    'loki',
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL
)

# Tareas en background
@celery_app.task
def generate_weekly_summary(usuario_id: int):
    """Genera resumen semanal asíncrono"""
    db = SessionLocal()
    try:
        # ... generar resumen
        summary = create_summary(db, usuario_id)

        # Enviar por WhatsApp
        send_whatsapp_message(user.telefono, summary)
    finally:
        db.close()

@celery_app.task
def recalculate_patterns(usuario_id: int):
    """Recalcula patrones en background"""
    # ... análisis costoso
```

**Tiempo estimado:** 8 horas

---

# MEJORAS FRONTEND

## 🔴 PRIORIDAD CRÍTICA (Semana 1-2)

### 17. Middleware de Autenticación

**Problema:** Validación de auth solo en cliente (insegura)

**Solución:**
```typescript
// middleware.ts
import { NextRequest, NextResponse } from 'next/server';

export async function middleware(request: NextRequest) {
  const pathname = request.nextUrl.pathname;

  // Rutas públicas
  if (pathname === '/' || pathname === '/auth') {
    return NextResponse.next();
  }

  // Rutas protegidas
  if (pathname.startsWith('/dashboard')) {
    const token = request.cookies.get('loki_token')?.value;

    if (!token) {
      // Redirigir a auth
      return NextResponse.redirect(new URL('/auth', request.url));
    }

    // Validar token en backend
    try {
      const apiUrl = process.env.NEXT_PUBLIC_API_URL;
      const response = await fetch(`${apiUrl}/api/v1/auth/verify-token`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ token })
      });

      if (!response.ok) {
        // Token inválido, redirigir
        const res = NextResponse.redirect(new URL('/auth', request.url));
        res.cookies.delete('loki_token');
        return res;
      }
    } catch (error) {
      return NextResponse.redirect(new URL('/auth', request.url));
    }
  }

  return NextResponse.next();
}

export const config = {
  matcher: ['/dashboard/:path*']
};
```

**Impacto:** Seguridad real en rutas protegidas
**Tiempo estimado:** 2 horas
**Archivo:** Crear `frontend/middleware.ts`

---

### 18. API Client Wrapper

**Problema:** Fetch duplicado, sin manejo centralizado de errores

**Solución:**
```typescript
// lib/api.ts
const API_URL = process.env.NEXT_PUBLIC_API_URL;

export class ApiError extends Error {
  constructor(
    message: string,
    public status: number,
    public data?: any
  ) {
    super(message);
    this.name = 'ApiError';
  }
}

export async function apiCall<T>(
  endpoint: string,
  options?: RequestInit
): Promise<T> {
  const token =
    typeof window !== 'undefined'
      ? localStorage.getItem('loki_token')
      : null;

  const response = await fetch(`${API_URL}${endpoint}`, {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      ...(token && { 'Authorization': `Bearer ${token}` }),
      ...options?.headers
    }
  });

  if (!response.ok) {
    if (response.status === 401) {
      // Token expirado
      if (typeof window !== 'undefined') {
        localStorage.removeItem('loki_token');
        window.location.href = '/auth';
      }
    }

    const errorData = await response.json().catch(() => ({}));
    throw new ApiError(
      errorData.detail || 'Error en la petición',
      response.status,
      errorData
    );
  }

  return response.json();
}

// Uso
import { apiCall } from '@/lib/api';

const userData = await apiCall<UserData>('/api/v1/auth/me');
const moods = await apiCall<MoodData[]>(`/api/v1/usuarios/${id}/estados_animo/`);
```

**Impacto:** Código DRY, manejo consistente de errores
**Tiempo estimado:** 1.5 horas
**Archivo:** Crear `frontend/lib/api.ts`, refactor en pages

---

### 19. Error Boundary Global

**Problema:** Errores no capturados rompen la app

**Solución:**
```typescript
// app/error.tsx
'use client';

import { useEffect } from 'react';
import * as Sentry from '@sentry/nextjs';

export default function Error({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  useEffect(() => {
    // Reportar a Sentry
    Sentry.captureException(error);
  }, [error]);

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50">
      <div className="max-w-md w-full text-center px-6">
        <div className="text-6xl mb-4">😞</div>
        <h2 className="text-2xl font-bold mb-2 text-gray-900">
          Algo salió mal
        </h2>
        <p className="text-gray-600 mb-6">
          Ocurrió un error inesperado. Nuestro equipo ha sido notificado.
        </p>
        <div className="space-y-3">
          <button
            onClick={reset}
            className="w-full px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 transition"
          >
            Intentar de nuevo
          </button>
          <a
            href="/"
            className="block w-full px-4 py-2 bg-gray-200 text-gray-800 rounded-lg hover:bg-gray-300 transition"
          >
            Volver al inicio
          </a>
        </div>
        {process.env.NODE_ENV === 'development' && (
          <details className="mt-6 text-left">
            <summary className="cursor-pointer text-sm text-gray-500">
              Detalles técnicos
            </summary>
            <pre className="mt-2 text-xs bg-gray-100 p-4 rounded overflow-auto">
              {error.message}
              {error.stack}
            </pre>
          </details>
        )}
      </div>
    </div>
  );
}

// app/global-error.tsx (para errores en root layout)
'use client';

export default function GlobalError({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  return (
    <html>
      <body>
        {/* Similar al error.tsx */}
      </body>
    </html>
  );
}
```

**Impacto:** UX mejorada, debugging más fácil
**Tiempo estimado:** 1 hora
**Archivos:** Crear `frontend/app/error.tsx`, `frontend/app/global-error.tsx`

---

### 20. Variables de Entorno Robustas

**Problema:** URL hardcodeada, sin validación

**Solución:**
```typescript
// lib/env.ts
import { z } from 'zod';

const envSchema = z.object({
  NEXT_PUBLIC_API_URL: z.string().url(),
  NEXT_PUBLIC_SENTRY_DSN: z.string().url().optional(),
  NEXT_PUBLIC_ENV: z.enum(['development', 'staging', 'production']),
});

// Validar en build time
const parsedEnv = envSchema.safeParse({
  NEXT_PUBLIC_API_URL: process.env.NEXT_PUBLIC_API_URL,
  NEXT_PUBLIC_SENTRY_DSN: process.env.NEXT_PUBLIC_SENTRY_DSN,
  NEXT_PUBLIC_ENV: process.env.NEXT_PUBLIC_ENV || 'development',
});

if (!parsedEnv.success) {
  console.error('❌ Variables de entorno inválidas:');
  console.error(parsedEnv.error.flatten().fieldErrors);
  throw new Error('Invalid environment variables');
}

export const env = parsedEnv.data;

// Uso
import { env } from '@/lib/env';

const API_URL = env.NEXT_PUBLIC_API_URL;
```

**.env.local (desarrollo):**
```
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_ENV=development
```

**.env.production:**
```
NEXT_PUBLIC_API_URL=https://api.moodtracker.com
NEXT_PUBLIC_ENV=production
NEXT_PUBLIC_SENTRY_DSN=https://...
```

**Impacto:** Detección temprana de configuraciones incorrectas
**Tiempo estimado:** 45 minutos
**Archivo:** Crear `frontend/lib/env.ts`

---

## 🟠 PRIORIDAD ALTA (Semana 2-4)

### 21. SWR para Data Fetching y Caché

**Problema:** Sin caché, refetch innecesarios

**Solución:**
```typescript
// package.json
{
  "dependencies": {
    "swr": "^2.2.0"
  }
}

// lib/hooks/useFetch.ts
import useSWR from 'swr';
import { apiCall } from '@/lib/api';

export function useFetch<T>(endpoint: string | null) {
  const { data, error, isLoading, mutate } = useSWR(
    endpoint,
    (url) => apiCall<T>(url),
    {
      revalidateOnFocus: false,
      revalidateOnReconnect: true,
      dedupingInterval: 60000,  // 1 minuto
      errorRetryCount: 3,
      onError: (error) => {
        console.error('SWR Error:', error);
      }
    }
  );

  return {
    data,
    error,
    isLoading,
    mutate,  // Para invalidar cache manualmente
  };
}

// Uso en dashboard
'use client';

import { useFetch } from '@/lib/hooks/useFetch';

export default function DashboardPage() {
  const { data: userData, isLoading, error } = useFetch<UserData>('/api/v1/auth/me');

  if (isLoading) return <LoadingSpinner />;
  if (error) return <ErrorMessage error={error} />;
  if (!userData) return null;

  return <DashboardContent user={userData} />;
}

// Pre-fetching para mejorar UX
import { preload } from 'swr';
import { apiCall } from '@/lib/api';

function PrefetchLink() {
  return (
    <Link
      href="/dashboard"
      onMouseEnter={() => {
        preload('/api/v1/auth/me', apiCall);
      }}
    >
      Dashboard
    </Link>
  );
}
```

**Impacto:** Reduce requests en 60-80%, mejor UX
**Tiempo estimado:** 3 horas
**Archivos:** Crear `frontend/lib/hooks/useFetch.ts`, refactor `frontend/app/dashboard/page.tsx`

---

### 22. Gestión de Estado con Zustand

**Problema:** localStorage directo, sin reactivity

**Solución:**
```typescript
// package.json
{
  "dependencies": {
    "zustand": "^4.4.0"
  }
}

// lib/store/auth.ts
import { create } from 'zustand';
import { persist } from 'zustand/middleware';

interface AuthState {
  token: string | null;
  user: UserData | null;
  isAuthenticated: boolean;

  // Actions
  setToken: (token: string) => void;
  setUser: (user: UserData) => void;
  logout: () => void;
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set) => ({
      token: null,
      user: null,
      isAuthenticated: false,

      setToken: (token) => set({ token, isAuthenticated: true }),

      setUser: (user) => set({ user }),

      logout: () => {
        set({ token: null, user: null, isAuthenticated: false });

        // Limpiar también localStorage
        if (typeof window !== 'undefined') {
          localStorage.removeItem('loki_token');
          localStorage.removeItem('loki_user');
        }
      },
    }),
    {
      name: 'loki-auth-storage',
      partialize: (state) => ({
        token: state.token,
        user: state.user
      }),
    }
  )
);

// Uso
import { useAuthStore } from '@/lib/store/auth';

function Header() {
  const { user, logout } = useAuthStore();

  return (
    <header>
      <p>Hola, {user?.nombre}</p>
      <button onClick={logout}>Cerrar sesión</button>
    </header>
  );
}

// En auth page
function AuthPage() {
  const setToken = useAuthStore((state) => state.setToken);
  const setUser = useAuthStore((state) => state.setUser);

  const verifyToken = async (token: string) => {
    const data = await apiCall('/api/v1/auth/verify-token', {
      method: 'POST',
      body: JSON.stringify({ token })
    });

    if (data.valid) {
      setToken(token);
      setUser({
        id: data.usuario_id,
        telefono: data.telefono
      });
      router.push('/dashboard');
    }
  };
}
```

**Impacto:** Estado reactivo, mejor DX
**Tiempo estimado:** 2 horas
**Archivos:** Crear `frontend/lib/store/auth.ts`, refactor auth flow

---

### 23. Testing con Vitest + Testing Library

**Problema:** 0% cobertura de tests

**Solución:**
```typescript
// package.json
{
  "devDependencies": {
    "vitest": "^1.0.0",
    "@vitejs/plugin-react": "^4.2.0",
    "@testing-library/react": "^15.0.0",
    "@testing-library/jest-dom": "^6.1.0",
    "@testing-library/user-event": "^14.5.0"
  },
  "scripts": {
    "test": "vitest",
    "test:ui": "vitest --ui",
    "test:coverage": "vitest --coverage"
  }
}

// vitest.config.ts
import { defineConfig } from 'vitest/config';
import react from '@vitejs/plugin-react';
import path from 'path';

export default defineConfig({
  plugins: [react()],
  test: {
    environment: 'jsdom',
    globals: true,
    setupFiles: ['./vitest.setup.ts'],
  },
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './'),
    },
  },
});

// vitest.setup.ts
import '@testing-library/jest-dom';

// __tests__/components/card.test.tsx
import { render, screen } from '@testing-library/react';
import { Card, CardTitle, CardContent } from '@/components/ui/card';

describe('Card Component', () => {
  it('renders card with title and content', () => {
    render(
      <Card>
        <CardTitle>Test Card</CardTitle>
        <CardContent>Card content</CardContent>
      </Card>
    );

    expect(screen.getByText('Test Card')).toBeInTheDocument();
    expect(screen.getByText('Card content')).toBeInTheDocument();
  });

  it('applies custom className', () => {
    const { container } = render(
      <Card className="custom-class">Content</Card>
    );

    expect(container.firstChild).toHaveClass('custom-class');
    expect(container.firstChild).toHaveClass('rounded-lg');
  });
});

// __tests__/app/auth.test.tsx
import { render, screen, waitFor } from '@testing-library/react';
import AuthPage from '@/app/auth/page';

vi.mock('next/navigation', () => ({
  useRouter: () => ({
    push: vi.fn(),
  }),
  useSearchParams: () => new URLSearchParams('token=test-token'),
}));

describe('Auth Page', () => {
  it('shows loading state initially', () => {
    render(<AuthPage />);
    expect(screen.getByText(/verificando/i)).toBeInTheDocument();
  });

  it('shows success on valid token', async () => {
    global.fetch = vi.fn(() =>
      Promise.resolve({
        ok: true,
        json: () => Promise.resolve({ valid: true, usuario_id: 1 })
      })
    );

    render(<AuthPage />);

    await waitFor(() => {
      expect(screen.getByText(/acceso verificado/i)).toBeInTheDocument();
    });
  });
});
```

**Meta:** 60% cobertura en 3 semanas

**Tiempo estimado:** 10 horas
**Archivos:** Configurar Vitest, escribir tests para componentes y pages

---

### 24. Accesibilidad (A11y) WCAG 2.1 AA

**Problema:** Sin ARIA labels, keyboard navigation limitada

**Solución:**
```typescript
// components/ui/card.tsx
const Card = React.forwardRef<
  HTMLDivElement,
  React.HTMLAttributes<HTMLDivElement>
>(({ className, ...props }, ref) => (
  <div
    ref={ref}
    role="article"
    aria-label={props['aria-label']}
    className={cn(
      "rounded-lg border bg-card text-card-foreground shadow-sm",
      className
    )}
    {...props}
  />
));

// app/dashboard/page.tsx
<Card aria-label="Estadísticas de ánimo promedio">
  <CardHeader className="pb-3">
    <CardDescription>Estado promedio</CardDescription>
    <CardTitle className="text-4xl" aria-live="polite">
      {averageMood.toFixed(1)}
    </CardTitle>
  </CardHeader>
</Card>

// Botón de logout con keyboard support
<button
  onClick={handleLogout}
  aria-label="Cerrar sesión de Loki"
  className="px-4 py-2 bg-red-500 text-white rounded-lg
             hover:bg-red-600 focus:outline-none focus:ring-2
             focus:ring-red-500 focus:ring-offset-2"
>
  Logout
</button>

// Skip link para navigation
<a
  href="#main-content"
  className="sr-only focus:not-sr-only focus:absolute focus:top-0
             focus:left-0 bg-purple-600 text-white px-4 py-2 z-50"
>
  Saltar al contenido principal
</a>

<main id="main-content">
  {/* Dashboard content */}
</main>

// Loading spinner con aria-live
<div
  role="status"
  aria-live="polite"
  aria-label="Cargando datos del usuario"
>
  <div className="animate-spin h-8 w-8 border-4 border-purple-600
                  border-t-transparent rounded-full"
       aria-hidden="true" />
  <span className="sr-only">Cargando...</span>
</div>
```

**Testing A11y:**
```typescript
// package.json
{
  "devDependencies": {
    "eslint-plugin-jsx-a11y": "^6.8.0",
    "axe-core": "^4.8.0",
    "@axe-core/react": "^4.8.0"
  }
}

// eslint.config.mjs
import jsxA11y from 'eslint-plugin-jsx-a11y';

export default [
  jsxA11y.flatConfigs.recommended,
  // ...
];

// __tests__/a11y.test.tsx
import { render } from '@testing-library/react';
import { axe, toHaveNoViolations } from 'jest-axe';

expect.extend(toHaveNoViolations);

test('Dashboard should not have a11y violations', async () => {
  const { container } = render(<DashboardPage />);
  const results = await axe(container);
  expect(results).toHaveNoViolations();
});
```

**Impacto:** Cumplimiento legal, mejor UX para todos
**Tiempo estimado:** 6 horas
**Archivos:** Todos los componentes y pages

---

## 🟡 PRIORIDAD MEDIA (1-2 meses)

### 25. Optimización de Imágenes

**Solución:**
```typescript
// app/layout.tsx
import Image from 'next/image';

export default function RootLayout({ children }) {
  return (
    <html lang="es">
      <body>
        <header>
          <Image
            src="/logo.png"
            alt="Loki Logo"
            width={120}
            height={40}
            priority  // Para logo en header
          />
        </header>
        {children}
      </body>
    </html>
  );
}

// next.config.ts
const nextConfig = {
  images: {
    formats: ['image/avif', 'image/webp'],
    deviceSizes: [640, 750, 828, 1080, 1200, 1920, 2048, 3840],
    imageSizes: [16, 32, 48, 64, 96, 128, 256, 384],
  },
};
```

**Tiempo estimado:** 1 hora

---

### 26. React Hook Form para Formularios

**Solución:**
```typescript
// package.json
{
  "dependencies": {
    "react-hook-form": "^7.51.0",
    "@hookform/resolvers": "^3.3.0",
    "zod": "^3.22.0"
  }
}

// components/forms/MoodForm.tsx
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';

const moodSchema = z.object({
  nivel: z.number().min(1).max(10),
  notas: z.string().max(500).optional(),
});

type MoodFormData = z.infer<typeof moodSchema>;

export function MoodForm({ onSubmit }: { onSubmit: (data: MoodFormData) => void }) {
  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting }
  } = useForm<MoodFormData>({
    resolver: zodResolver(moodSchema),
    defaultValues: {
      nivel: 5,
      notas: '',
    }
  });

  return (
    <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
      <div>
        <label htmlFor="nivel" className="block text-sm font-medium">
          ¿Cómo te sientes? (1-10)
        </label>
        <input
          id="nivel"
          type="range"
          min="1"
          max="10"
          {...register('nivel', { valueAsNumber: true })}
          className="w-full"
        />
        {errors.nivel && (
          <p className="text-red-500 text-sm mt-1">{errors.nivel.message}</p>
        )}
      </div>

      <div>
        <label htmlFor="notas" className="block text-sm font-medium">
          Notas (opcional)
        </label>
        <textarea
          id="notas"
          {...register('notas')}
          className="w-full border rounded px-3 py-2"
          rows={3}
        />
        {errors.notas && (
          <p className="text-red-500 text-sm mt-1">{errors.notas.message}</p>
        )}
      </div>

      <button
        type="submit"
        disabled={isSubmitting}
        className="w-full bg-purple-600 text-white py-2 rounded-lg
                   disabled:opacity-50 disabled:cursor-not-allowed"
      >
        {isSubmitting ? 'Guardando...' : 'Guardar'}
      </button>
    </form>
  );
}
```

**Tiempo estimado:** 4 horas

---

### 27. Monitoreo con Sentry

**Solución:**
```bash
npm install @sentry/nextjs --save
npx @sentry/wizard@latest -i nextjs
```

```typescript
// sentry.client.config.ts
import * as Sentry from "@sentry/nextjs";

Sentry.init({
  dsn: process.env.NEXT_PUBLIC_SENTRY_DSN,
  environment: process.env.NEXT_PUBLIC_ENV,
  tracesSampleRate: 0.1,
  replaysSessionSampleRate: 0.1,
  replaysOnErrorSampleRate: 1.0,

  integrations: [
    new Sentry.BrowserTracing(),
    new Sentry.Replay({
      maskAllText: true,
      blockAllMedia: true,
    }),
  ],

  beforeSend(event, hint) {
    // Filtrar eventos sensibles
    if (event.request) {
      delete event.request.cookies;
    }
    return event;
  },
});

// Uso manual
try {
  await riskyOperation();
} catch (error) {
  Sentry.captureException(error, {
    tags: {
      section: 'dashboard',
    },
    extra: {
      userId: user.id,
    },
  });
}
```

**Tiempo estimado:** 2 horas

---

### 28. Internacionalización (i18n)

**Solución:**
```typescript
// package.json
{
  "dependencies": {
    "next-intl": "^3.0.0"
  }
}

// messages/es.json
{
  "common": {
    "loading": "Cargando...",
    "error": "Ocurrió un error"
  },
  "dashboard": {
    "welcome": "Hola, {name}",
    "averageMood": "Estado promedio",
    "lastDays": "Últimos {days} días"
  }
}

// messages/en.json
{
  "common": {
    "loading": "Loading...",
    "error": "An error occurred"
  },
  "dashboard": {
    "welcome": "Hello, {name}",
    "averageMood": "Average mood",
    "lastDays": "Last {days} days"
  }
}

// app/[locale]/layout.tsx
import { NextIntlClientProvider } from 'next-intl';
import { notFound } from 'next/navigation';

export default async function LocaleLayout({
  children,
  params: { locale }
}: {
  children: React.ReactNode;
  params: { locale: string };
}) {
  let messages;
  try {
    messages = (await import(`@/messages/${locale}.json`)).default;
  } catch (error) {
    notFound();
  }

  return (
    <html lang={locale}>
      <body>
        <NextIntlClientProvider locale={locale} messages={messages}>
          {children}
        </NextIntlClientProvider>
      </body>
    </html>
  );
}

// Uso
import { useTranslations } from 'next-intl';

function Dashboard({ user }) {
  const t = useTranslations('dashboard');

  return (
    <h1>{t('welcome', { name: user.nombre })}</h1>
  );
}
```

**Tiempo estimado:** 8 horas

---

## 🟢 PRIORIDAD BAJA (2+ meses)

### 29. PWA para Soporte Offline

**Solución:**
```bash
npm install next-pwa --save-dev
```

```typescript
// next.config.ts
import withPWA from 'next-pwa';

const nextConfig = withPWA({
  dest: 'public',
  register: true,
  skipWaiting: true,
  disable: process.env.NODE_ENV === 'development',
})({
  // ... resto de config
});
```

```json
// public/manifest.json
{
  "name": "Loki Mood Tracker",
  "short_name": "Loki",
  "description": "Asistente emocional conversacional",
  "start_url": "/",
  "display": "standalone",
  "background_color": "#ffffff",
  "theme_color": "#8b5cf6",
  "icons": [
    {
      "src": "/icon-192.png",
      "sizes": "192x192",
      "type": "image/png"
    },
    {
      "src": "/icon-512.png",
      "sizes": "512x512",
      "type": "image/png"
    }
  ]
}
```

**Tiempo estimado:** 6 horas

---

### 30. Storybook para Documentación de Componentes

**Solución:**
```bash
npx storybook@latest init
```

```typescript
// stories/Card.stories.tsx
import type { Meta, StoryObj } from '@storybook/react';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card';

const meta: Meta<typeof Card> = {
  title: 'UI/Card',
  component: Card,
  tags: ['autodocs'],
};

export default meta;
type Story = StoryObj<typeof Card>;

export const Default: Story = {
  render: () => (
    <Card>
      <CardHeader>
        <CardTitle>Card Title</CardTitle>
      </CardHeader>
      <CardContent>
        Card content goes here
      </CardContent>
    </Card>
  ),
};

export const WithCustomClass: Story = {
  render: () => (
    <Card className="border-purple-500">
      <CardContent>Custom border color</CardContent>
    </Card>
  ),
};
```

**Tiempo estimado:** 6 horas

---

# PLAN DE IMPLEMENTACIÓN

## Semana 1-2: Seguridad Crítica

**Backend:**
- [ ] CORS restrictivo
- [ ] Validación firmas webhook
- [ ] Secret key segura
- [ ] Logging centralizado
- [ ] Rate limiting

**Frontend:**
- [ ] Middleware de auth
- [ ] API client wrapper
- [ ] Error boundaries
- [ ] Variables de entorno robustas

**Tiempo total:** 15-20 horas

---

## Semana 3-4: Testing y Validaciones

**Backend:**
- [ ] Tests unitarios (auth, trust, pattern)
- [ ] Transacciones explícitas
- [ ] Validaciones de entrada
- [ ] Índices de BD
- [ ] Sistema de migraciones

**Frontend:**
- [ ] SWR para caché
- [ ] Zustand para estado
- [ ] Vitest + Testing Library
- [ ] Tests de componentes básicos

**Tiempo total:** 30-35 horas

---

## Mes 2: Optimización

**Backend:**
- [ ] Caché con Redis
- [ ] Paginación cursor-based
- [ ] Tests E2E
- [ ] Monitoreo con Sentry

**Frontend:**
- [ ] Accesibilidad WCAG 2.1
- [ ] Optimización de imágenes
- [ ] React Hook Form
- [ ] Sentry frontend

**Tiempo total:** 30-35 horas

---

## Mes 3+: Features Avanzadas

**Backend:**
- [ ] Documentación Swagger
- [ ] Background tasks con Celery
- [ ] Métricas y analytics
- [ ] Optimizaciones query

**Frontend:**
- [ ] i18n
- [ ] PWA
- [ ] Storybook
- [ ] Performance optimization

**Tiempo total:** 40-50 horas

---

# MÉTRICAS DE ÉXITO

## Backend

| Métrica | Estado Actual | Meta Mes 1 | Meta Mes 3 |
|---------|---------------|------------|------------|
| Cobertura Tests | <1% | 40% | 70% |
| Vulnerabilidades | 7 críticas | 0 críticas | 0 |
| Response Time (p95) | ~500ms | ~300ms | ~150ms |
| Uptime | N/A | 99.5% | 99.9% |
| MTTR | N/A | <1h | <15min |

## Frontend

| Métrica | Estado Actual | Meta Mes 1 | Meta Mes 3 |
|---------|---------------|------------|------------|
| Cobertura Tests | 0% | 50% | 70% |
| Lighthouse Score | ~70 | 85 | 95 |
| Core Web Vitals | Parcial | Pass | Pass |
| A11y Score | ~60 | 85 | 95 |
| Bundle Size | ~200KB | ~150KB | ~120KB |

---

# RECURSOS NECESARIOS

## Herramientas y Servicios

1. **Redis** (caché) - $0 (desarrollo) / $10-30/mes (producción)
2. **Sentry** (monitoring) - $0 (tier gratuito) / $26/mes (growth)
3. **GitHub Actions** (CI/CD) - Incluido en GitHub
4. **Railway/Vercel** (hosting) - $0 (desarrollo) / $20-50/mes
5. **Testing tools** - Gratuito (open source)

**Costo mensual estimado:** $50-110 para producción

## Tiempo de Desarrollo

- **1 desarrollador full-time:** 3 meses
- **1 desarrollador part-time (50%):** 6 meses
- **2 desarrolladores full-time:** 1.5 meses

---

# CONCLUSIÓN

Este plan de mejoras transformará Loki de un MVP funcional a una aplicación robusta, segura y lista para producción. Las mejoras críticas de seguridad deben implementarse **antes** de cualquier lanzamiento público.

**Prioridades absolutas:**
1. Seguridad (CORS, webhooks, JWT)
2. Testing (backend + frontend)
3. Autenticación segura
4. Logging y monitoreo

Con estas mejoras implementadas, el proyecto estará listo para escalar y manejar usuarios reales de forma segura y confiable.
