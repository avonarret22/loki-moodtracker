# 📘 GUÍA DE IMPLEMENTACIÓN - Mejoras de Inteligencia Loki

## 🎯 Objetivo

Esta guía te ayudará a implementar y activar todas las nuevas características de inteligencia de Loki que han sido desarrolladas.

---

## 📦 REQUISITOS PREVIOS

- Python 3.9+
- FastAPI 0.110.0+
- SQLAlchemy 2.0.29+
- PostgreSQL o SQLite (según tu configuración)

---

## 1️⃣ INSTALACIÓN DE DEPENDENCIAS

### Paso 1: Actualizar requirements.txt

Las siguientes librerías han sido agregadas:
- `spacy==3.7.2` - NLP avanzado
- `textblob==0.17.1` - Análisis de sentimiento

### Paso 2: Instalar dependencias

```bash
cd backend/
pip install -r requirements.txt
```

### Paso 3: Descargar modelos de Spacy (Opcional, para futuro)

```bash
python -m spacy download es_core_news_sm
```

---

## 2️⃣ MIGRACIONES DE BASE DE DATOS

Necesitas crear e implementar migraciones para las nuevas tablas.

### Paso 1: Crear migración automática

```bash
cd backend/
alembic revision --autogenerate -m "Add new tables for Loki intelligence enhancement"
```

Esto generará un archivo en `backend/alembic/versions/` con las nuevas tablas:
- `resumenes_conversacion`
- `perfil_usuario`
- `feedback_respuestas`
- `respuestas_exitosas`

### Paso 2: Revisar la migración (IMPORTANTE)

Abre el archivo generado y verifica que las columnas y relaciones sean correctas.

### Paso 3: Aplicar migraciones

```bash
alembic upgrade head
```

### Verificar

```bash
# Para SQLite:
sqlite3 database.db ".tables"

# Para PostgreSQL:
psql -d your_db -c "\dt"
```

Deberías ver las 4 nuevas tablas listadas.

---

## 3️⃣ CONFIGURACIÓN DE SERVICIOS

### Integración automática

Los servicios se integran automáticamente en el flujo actual:

1. **ai_service.py** - Ahora usa:
   - `nlp_service` para análisis avanzado
   - `memory_service` para contexto histórico
   - `personality_service` (cuando sea necesario)

2. **Endpoints existentes** - Todos funcionan igual pero con mejoras transparentes

3. **Nuevos endpoints** - Disponibles automáticamente:
   - `/api/v1/recommendations/*`
   - `/api/v1/feedback/*`

---

## 4️⃣ USANDO LAS NUEVAS CARACTERÍSTICAS

### A. NLP Avanzado

**Dentro de tu código:**

```python
from app.services.nlp_service import nlp_service

# Análisis completo de un mensaje
analysis = nlp_service.analyze_complete_context(
    "Me siento muy ansioso y triste con el trabajo",
    conversation_history=["mensaje1", "mensaje2"]
)

print(analysis)
# {
#   'sentiment': {
#       'primary_emotions': [
#           {'emotion': 'ansiedad', 'intensity': 0.6, 'confidence': 0.8},
#           {'emotion': 'tristeza', 'intensity': -0.8, 'confidence': 0.7}
#       ],
#       'overall_sentiment': -0.7,
#       'dominant_emotion': 'ansiedad'
#   },
#   'entities': {...},
#   'values': {...}
# }
```

### B. Memoria Conversacional

**Para obtener contexto histórico:**

```python
from app.services.memory_service import memory_service

# Obtener resúmenes de conversaciones pasadas
context = memory_service.get_long_term_context(db, usuario_id=1, num_summaries=3)
print(context)
# Retorna markdown con resúmenes de los últimos períodos
```

### C. Análisis Emocional Avanzado

**Para analizar ciclos emocionales:**

```python
from app.services.emotion_analysis_service import emotion_service

# Detectar ciclos (diarios, semanales, mensuales)
cycles = emotion_service.detect_emotional_cycles(db, usuario_id=1, days_lookback=30)
print(cycles)
# {
#   'daily_pattern': {...},
#   'weekly_pattern': {...},
#   'predominant_cycle': 'weekly',
#   'next_low_mood_prediction': datetime
# }
```

### D. Personalidad Adaptativa

**Para obtener adaptación personalizada:**

```python
from app.services.personality_adaptation_service import personality_service

# Detectar preferencias del usuario
prefs = personality_service.detect_user_conversation_preferences(conversation_texts)
print(prefs)
# {
#   'formality_level': 'casual',
#   'directness': 'balanced',
#   'preferred_role': 'amigo'
# }

# Obtener enhancement personalizado para el prompt
enhancement = personality_service.generate_adapted_system_prompt_enhancement(
    db, usuario_id=1, usuario_nombre="Diego", current_mood=7
)
```

### E. Recomendaciones Proactivas

**Vía API (más común):**

```bash
# Obtener todas las recomendaciones
curl http://localhost:8000/api/v1/recommendations/1

# Obtener desafíos
curl http://localhost:8000/api/v1/recommendations/1/challenges?difficulty=moderate

# Obtener micro-hábitos
curl http://localhost:8000/api/v1/recommendations/1/micro-habits

# Obtener próxima acción recomendada
curl http://localhost:8000/api/v1/recommendations/1/next-action
```

**Desde código:**

```python
from app.services.recommendation_service import recommendation_service

# Sugerir actividades preventivas
activities = recommendation_service.suggest_preventive_activities(db, usuario_id=1)

# Generar desafíos
challenges = recommendation_service.generate_personalized_challenges(
    db, usuario_id=1, difficulty='moderate'
)

# Sugerir micro-hábitos
micro = recommendation_service.suggest_micro_habits(current_mood=4)
```

### F. Feedback y Aprendizaje

**Registrar feedback (vía API):**

```bash
curl -X POST http://localhost:8000/api/v1/feedback/submit \
  -H "Content-Type: application/json" \
  -d '{
    "usuario_id": 1,
    "mensaje_usuario": "¿Cómo manejo la ansiedad?",
    "respuesta_loki": "La ansiedad es normal...",
    "utilidad_rating": 5,
    "ayudo": true,
    "notas": "Muy útil, gracias!"
  }'
```

**Obtener respuestas exitosas:**

```bash
curl http://localhost:8000/api/v1/feedback/1/respuestas-exitosas
```

---

## 5️⃣ TESTING

### Crear archivo de test

```python
# backend/tests/test_new_services.py

import pytest
from app.services.nlp_service import nlp_service
from app.services.emotion_analysis_service import emotion_service

def test_sentiment_analysis():
    text = "Me siento muy triste y solo"
    analysis = nlp_service.analyze_sentiment_detailed(text)

    assert analysis['dominant_emotion'] == 'tristeza'
    assert analysis['overall_sentiment'] < 0
    assert 'soledad' in [e['emotion'] for e in analysis.get('secondary_emotions', [])]

def test_emotion_cycles(db, usuario_id):
    cycles = emotion_service.detect_emotional_cycles(db, usuario_id)
    assert 'daily_pattern' in cycles or 'error' in cycles

def test_language_patterns():
    texts = ["Me encanta hablar contigo", "Tu respuesta me ayudó mucho"]
    patterns = nlp_service.extract_language_patterns(texts)

    assert 'vocabulary_level' in patterns
    assert 'favorite_expressions' in patterns
```

### Ejecutar tests

```bash
pytest backend/tests/test_new_services.py -v
```

---

## 6️⃣ INTEGRACIÓN CON WHATSAPP (Futuro)

### Actualizar webhook de WhatsApp

Cuando integres las nuevas características con WhatsApp:

```python
# En backend/app/api/routes/whatsapp.py

async def handle_whatsapp_message(webhook_data):
    # ... código existente ...

    # Obtener recomendaciones para el usuario
    recommendations = recommendation_service.get_next_recommended_action(
        db, usuario_id, current_mood
    )

    # Enviar recomendación vía WhatsApp API
    if recommendations:
        send_whatsapp_message(usuario.telefono, recommendations['acción'])
```

---

## 7️⃣ MONITOREO Y DEBUGGING

### Logs útiles

Los servicios incluyen prints de debug. Para ver más detalle:

```python
import logging
logging.basicConfig(level=logging.DEBUG)

# Ahora verás todos los logs de los servicios
```

### Verificar que todo funciona

```bash
# 1. Iniciar servidor
uvicorn main:app --reload

# 2. Crear usuario
curl -X POST http://localhost:8000/api/v1/usuarios/ \
  -d '{"nombre": "Test", "telefono": "123456789"}'

# 3. Enviar mensaje
curl -X POST http://localhost:8000/api/v1/chat/ \
  -d '{"usuario_id": 1, "mensaje": "Hola, me siento triste"}'

# 4. Ver recomendaciones
curl http://localhost:8000/api/v1/recommendations/1

# 5. Verificar análisis
curl http://localhost:8000/api/v1/recommendations/1/emotional-cycles
```

---

## 8️⃣ TROUBLESHOOTING

### Error: "Module not found: spacy"

```bash
pip install spacy==3.7.2
```

### Error: "tabla resumenes_conversacion no existe"

Necesitas ejecutar las migraciones:

```bash
cd backend/
alembic upgrade head
```

### Error: "ForeignKey constraint failed"

Verifica que las migraciones se ejecutaron correctamente:

```bash
# SQLite
sqlite3 database.db ".schema resumenes_conversacion"

# PostgreSQL
psql -d your_db -c "\d resumenes_conversacion"
```

### Las respuestas no son personalizadas

Asegúrate que:
1. ✅ Las migraciones se ejecutaron
2. ✅ El usuario tiene conversaciones previas (>3)
3. ✅ Los servicios están integrados en `ai_service.py`
4. ✅ Se pasan `db_session` y `usuario_id` a `generate_response()`

---

## 9️⃣ PASOS SIGUIENTES RECOMENDADOS

### Corto plazo (1-2 semanas):
- [ ] Implementar migraciones de BD
- [ ] Probar servicios de NLP
- [ ] Validar recomendaciones con usuarios reales
- [ ] Registrar feedback de los usuarios

### Mediano plazo (1-2 meses):
- [ ] Entrenar modelo sentimiento más avanzado
- [ ] Integrar recomendaciones en WhatsApp
- [ ] Crear dashboard de estadísticas
- [ ] Analizar patrones de feedback

### Largo plazo (3+ meses):
- [ ] Implementar embeddings para búsqueda de similitud
- [ ] API de detección de crisis/riesgo
- [ ] Análisis predictivo de ánimo
- [ ] Personalización más profunda con learning

---

## 🔟 RECURSOS ÚTILES

### Documentación
- 📘 [MEJORAS_INTELIGENCIA_LOKI.md](MEJORAS_INTELIGENCIA_LOKI.md) - Guía completa
- 📗 Docstrings en cada servicio
- 📙 FastAPI docs en `/docs`

### Código de ejemplo
```python
# Ver cómo se usan en ai_service.py
# Ver endpoints en routes/recommendations.py y routes/feedback.py
```

### Referencias externas
- Spacy: https://spacy.io/
- FastAPI: https://fastapi.tiangolo.com/
- SQLAlchemy: https://www.sqlalchemy.org/

---

## ✅ CHECKLIST DE IMPLEMENTACIÓN

- [ ] Instalar dependencias nuevas
- [ ] Crear migraciones de BD
- [ ] Aplicar migraciones
- [ ] Verificar nuevas tablas en BD
- [ ] Probar servicios de NLP
- [ ] Probar endpoints de recomendaciones
- [ ] Registrar feedback
- [ ] Verificar que personalización funciona
- [ ] Documentar en equipo
- [ ] Desplegar a producción

---

## 🎉 ¡LISTO!

Cuando hayas completado todos los pasos, Loki tendrá:
- ✅ Inteligencia emocional 10x mejorada
- ✅ Memoria a largo plazo
- ✅ Personalidad adaptativa
- ✅ Recomendaciones proactivas
- ✅ Capacidad de aprendizaje continuo

**¡Felicidades! Ahora tienes un Loki mucho más inteligente y útil.**

---

**Última actualización:** 2024
**Versión:** 2.0 - Intelligence Enhanced
