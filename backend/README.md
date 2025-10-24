# Loki MoodTracker API

API backend para Loki, el compañero de bienestar emocional basado en WhatsApp.

## 🚀 Características Implementadas

### Core Features
- ✅ **Gestión de Usuarios** - CRUD completo para usuarios
- ✅ **Registro de Estados de Ánimo** - Tracking de estados emocionales (escala 1-10)
- ✅ **Gestión de Hábitos** - Crear, actualizar y rastrear hábitos personalizados
- ✅ **Registros de Hábitos** - Tracking de cumplimiento de hábitos
- ✅ **Conversaciones Contextuales** - Historial completo de interacciones
- ✅ **Correlaciones** - Almacenamiento de correlaciones entre hábitos y estados de ánimo

### AI & WhatsApp Integration
- ✅ **Servicio de IA (Loki)** - Procesamiento de lenguaje natural con personalidad empática
- ✅ **Detección automática de:**
  - Niveles de ánimo en mensajes (1-10)
  - Hábitos mencionados (ejercicio, sueño, social, etc.)
  - Disparadores emocionales (estrés, ansiedad, alegría, etc.)
- ✅ **Webhook de WhatsApp** - Recepción y procesamiento de mensajes
- ✅ **Chat Simulator** - Endpoint para testing sin WhatsApp

## 📋 Requisitos

- Python 3.11+
- FastAPI
- SQLAlchemy
- SQLite (desarrollo) / PostgreSQL (producción)
- httpx (para llamadas a APIs externas)

## 🛠️ Instalación

1. Clonar el repositorio
2. Instalar dependencias:
```bash
cd backend
pip install -r requirements.txt
```

3. Configurar variables de entorno (opcional):
Crear archivo `.env` en `backend/`:
```env
DATABASE_URL=sqlite:///./moodtracker.db
ANTHROPIC_API_KEY=tu_api_key_aqui
OPENAI_API_KEY=tu_api_key_aqui
WHATSAPP_ACCESS_TOKEN=tu_token_aqui
WHATSAPP_VERIFY_TOKEN=tu_verify_token_aqui
```

4. Ejecutar la aplicación:
```bash
uvicorn app.main:app --reload
```

## 📖 Documentación de la API

Una vez que la aplicación esté corriendo, accede a:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## 🔄 Endpoints Principales

### Usuarios
- `POST /api/v1/usuarios/` - Crear nuevo usuario
- `GET /api/v1/usuarios/` - Listar usuarios
- `GET /api/v1/usuarios/{usuario_id}` - Obtener usuario específico

### Estados de Ánimo
- `POST /api/v1/usuarios/{usuario_id}/estados_animo/` - Registrar estado de ánimo
- `GET /api/v1/usuarios/{usuario_id}/estados_animo/` - Obtener historial

### Hábitos
- `POST /api/v1/usuarios/{usuario_id}/habitos/` - Crear hábito
- `GET /api/v1/usuarios/{usuario_id}/habitos/` - Listar hábitos
- `PUT /api/v1/habitos/{habito_id}` - Actualizar hábito
- `DELETE /api/v1/habitos/{habito_id}` - Eliminar hábito

### Registros de Hábitos
- `POST /api/v1/usuarios/{usuario_id}/registros_habitos/` - Registrar cumplimiento
- `GET /api/v1/usuarios/{usuario_id}/registros_habitos/` - Ver registros
- `GET /api/v1/habitos/{habito_id}/registros/` - Registros por hábito

### Chat con Loki (Testing)
- `POST /api/v1/chat/chat` - Enviar mensaje a Loki
- `GET /api/v1/chat/chat/history/{usuario_id}` - Ver historial de chat

### WhatsApp Webhook
- `GET /whatsapp/webhook` - Verificación del webhook
- `POST /whatsapp/webhook` - Recibir mensajes de WhatsApp

## 🧪 Ejemplo de Uso - Chat con Loki

### 1. Crear un usuario
```bash
curl -X POST "http://localhost:8000/api/v1/usuarios/" \
  -H "Content-Type: application/json" \
  -d '{
    "nombre": "Diego",
    "telefono": "+1234567890"
  }'
```

### 2. Chatear con Loki
```bash
curl -X POST "http://localhost:8000/api/v1/chat/chat" \
  -H "Content-Type: application/json" \
  -d '{
    "usuario_id": 1,
    "mensaje": "Hoy me siento 8/10, hice ejercicio y dormí bien"
  }'
```

Respuesta esperada:
```json
{
  "respuesta": "¡Qué bueno escuchar eso, Diego! ¿Qué crees que hizo que te sintieras así de bien hoy?",
  "contexto_extraido": {
    "mood_level": 8,
    "habits_mentioned": ["ejercicio", "sueño"],
    "emotional_triggers": [],
    "timestamp": "2025-10-23T..."
  },
  "mood_registrado": true,
  "habitos_detectados": ["ejercicio", "sueño"]
}
```

## 🤖 Personalidad de Loki

Loki ha sido diseñado con las siguientes características:

- **Empático pero no paternalista**: Escucha sin juzgar
- **Conversacional**: Respuestas naturales y cortas (2-3 oraciones)
- **Curioso**: Hace preguntas inteligentes para entender patrones
- **Adaptable**: Ajusta su tono según el estado emocional del usuario
- **Memory-aware**: Recuerda conversaciones anteriores para contexto

## 🔐 Seguridad (TODO)

- [ ] Implementar autenticación JWT
- [ ] Rate limiting para webhooks
- [ ] Validación de firmas de WhatsApp
- [ ] Encriptación de datos sensibles

## 📊 Próximas Funcionalidades

- [ ] Motor de análisis de correlaciones automático
- [ ] Integración completa con Claude API
- [ ] Sistema de recordatorios programados
- [ ] Dashboard web para visualización
- [ ] Exportación de datos en PDF/CSV
- [ ] Sistema de objetivos y logros

## 🐛 Debugging

Ver logs en tiempo real:
```bash
# Los logs se mostrarán en la consola donde ejecutaste uvicorn
```

## 📝 Notas de Desarrollo

- La base de datos SQLite se crea automáticamente en `backend/moodtracker.db`
- Las tablas se crean automáticamente al iniciar la aplicación
- El sistema de IA actualmente usa reglas básicas; se puede integrar Claude/GPT
- El webhook de WhatsApp requiere HTTPS en producción (usar ngrok para testing local)

## 🤝 Contribuir

Este es un proyecto en desarrollo activo. Las áreas que necesitan atención:

1. **Análisis de correlaciones**: Implementar algoritmos estadísticos
2. **Integración IA**: Conectar con Claude/GPT API
3. **Dashboard**: Crear interfaz web con React/Vue
4. **Testing**: Agregar pruebas unitarias y de integración

---

**Desarrollado con ❤️ para mejorar el bienestar emocional**
