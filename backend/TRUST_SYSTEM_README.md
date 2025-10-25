# Sistema de Niveles de Confianza - Loki

## Resumen

El sistema de niveles de confianza hace que Loki evolucione de **reservado a cercano** basándose en la cantidad de interacciones con cada usuario. Esto resuelve el problema de que Loki hablaba demasiado y sonaba muy cursi/terapéutico.

## Cambios Implementados

### 1. Base de Datos

**Nuevos campos en `usuarios`:**
- `nivel_confianza` (INTEGER, default 1): Nivel de confianza actual (1-5)
- `total_interacciones` (INTEGER, default 0): Contador de mensajes intercambiados

**Migración:**
```bash
python backend/migrations/run_migration.py
```

### 2. Niveles de Confianza

| Nivel | Nombre | Rango Mensajes | Características |
|-------|--------|----------------|-----------------|
| 1 | **Conociendo** | 1-10 | Reservado, educado, 1 oración máximo |
| 2 | **Estableciendo** | 11-30 | Más cercano, recuerda cosas, max 2 oraciones |
| 3 | **Construyendo** | 31-60 | Confidente, hace conexiones, max 2 oraciones |
| 4 | **Consolidado** | 61-100 | Amigo cercano, humor apropiado, 2-3 oraciones |
| 5 | **Íntimo** | 100+ | Directo, anticipa necesidades, variable |

### 3. Nuevo Servicio: `trust_level_service.py`

**Funciones principales:**
- `calculate_trust_level(total_interacciones)`: Calcula nivel basado en interacciones
- `update_trust_level(db, usuario_id)`: Incrementa contador y actualiza nivel
- `get_user_trust_info(db, usuario_id)`: Obtiene info completa del nivel
- `get_forbidden_phrases()`: Lista de frases cursis prohibidas
- `get_allowed_expressions_by_level(nivel)`: Expresiones apropiadas por nivel

### 4. Refactorización de Prompts

**Eliminado:**
- ❌ "Estoy aquí para ti"
- ❌ "Recuerda que puedes confiar en mí"
- ❌ "Tu bienestar es importante"
- ❌ "Soy tu espacio seguro"
- ❌ Todas las frases "terapéuticas" y cursis

**Nuevo enfoque por nivel:**

#### Nivel 1 - Conociendo (1-10 mensajes)
- Tono: reservado, educado, sin asumir
- Respuestas: 1 oración máximo
- Ejemplos: "¿Cómo estuvo tu día?", "Cuéntame más"

#### Nivel 2 - Estableciendo (11-30 mensajes)
- Tono: cercano, atento, menos formal
- Respuestas: Max 2 oraciones
- Ejemplos: "Ayer mencionaste X. ¿Sigue pasando?", "¿Esto te pasa seguido?"

#### Nivel 3 - Construyendo (31-60 mensajes)
- Tono: confidente, observador, sugerente
- Respuestas: Max 2 oraciones
- Ejemplos: "Noto que cuando X pasa, sueles sentir Y", "¿Ves alguna conexión?"

#### Nivel 4 - Consolidado (61-100 mensajes)
- Tono: amigo cercano, humor apropiado, honesto
- Respuestas: 2-3 oraciones (solo si es necesario)
- Ejemplos: "Esto no es típico en ti. ¿Qué cambió?", "Conociéndote, sospecho que hay más"

#### Nivel 5 - Íntimo (100+ mensajes)
- Tono: directo, auténtico, intuitivo
- Respuestas: Variable, usualmente breve
- Ejemplos: "Ya sabes qué hacer, ¿verdad?", "Seamos honestos"

### 5. Actualización de `ai_service.py`

**Nuevo método:**
```python
_get_trust_based_system_prompt(usuario_nombre, nivel_confianza, nivel_info)
```

Este método:
- Genera prompts específicos por nivel
- Incluye ejemplos de qué hacer y qué NO hacer
- Prohíbe explícitamente frases cursis
- Adapta longitud y tono según el nivel

**Método actualizado:**
```python
build_system_prompt(usuario_nombre, contexto_reciente, db_session, usuario_id)
```

Ahora:
- Obtiene el nivel de confianza del usuario
- Genera el prompt apropiado para ese nivel
- Ajusta la cantidad de contexto histórico según el nivel
- Solo usa memoria de largo plazo si nivel >= 3

### 6. Actualización de Endpoints

**`chat.py` y `whatsapp.py`:**
- Llaman a `trust_service.update_trust_level()` en cada mensaje
- Incrementa automáticamente el contador
- Actualiza el nivel si corresponde
- Imprime mensaje cuando hay cambio de nivel

## Flujo de Funcionamiento

1. **Usuario envía mensaje** → WhatsApp o Chat API
2. **Sistema incrementa contador** → `trust_service.update_trust_level()`
3. **Se calcula nivel de confianza** → Basado en `total_interacciones`
4. **Se genera prompt adaptado** → Según el nivel actual
5. **Claude recibe prompt** → Con instrucciones específicas del nivel
6. **Respuesta adaptada** → Longitud y tono apropiados

## Ejemplos de Evolución

### Interacción #3 (Nivel 1 - Conociendo)
**Usuario:** "Me siento mal"
**Loki:** "¿Qué pasó?"

### Interacción #15 (Nivel 2 - Estableciendo)
**Usuario:** "Me siento mal otra vez"
**Loki:** "Ayer mencionaste algo similar. ¿Es lo mismo?"

### Interacción #45 (Nivel 3 - Construyendo)
**Usuario:** "Me siento mal otra vez"
**Loki:** "Noto que esto pasa los lunes. ¿Tiene que ver con el trabajo?"

### Interacción #75 (Nivel 4 - Consolidado)
**Usuario:** "Me siento mal otra vez"
**Loki:** "Esto no es como tú. ¿Pasó algo diferente hoy?"

### Interacción #120 (Nivel 5 - Íntimo)
**Usuario:** "Me siento mal otra vez"
**Loki:** "Ya sabes qué lo causa. ¿Qué vas a hacer?"

## Frases Prohibidas (NUNCA usar)

```python
[
    "estoy aquí para ti",
    "recuerda que puedes confiar en mí",
    "siempre que me necesites",
    "tu bienestar es importante",
    "soy tu espacio seguro",
    "no estás solo/sola",
    "estaré aquí siempre",
    "puedes contar conmigo siempre",
    "mi propósito es ayudarte",
    "estoy para apoyarte",
    "esto es un espacio seguro",
    "tu salud mental importa",
    "quiero que sepas que",
    "es importante que recuerdes"
]
```

## Testing

Para probar el sistema:

```bash
# 1. Asegurarse de que la migración está ejecutada
python backend/migrations/run_migration.py

# 2. Crear un nuevo usuario (nivel 1)
# Enviar 1-10 mensajes → Respuestas muy cortas, reservado

# 3. Seguir conversando (nivel 2)
# Mensajes 11-30 → Empieza a recordar cosas

# 4. Continuar (nivel 3)
# Mensajes 31-60 → Hace conexiones, sugiere patterns

# 5. Seguir (nivel 4)
# Mensajes 61-100 → Más cercano, usa humor

# 6. Completar (nivel 5)
# Mensajes 100+ → Directo, honesto, anticipa
```

## Archivos Modificados

### Nuevos:
- `backend/app/services/trust_level_service.py`
- `backend/migrations/add_trust_level_fields.sql`
- `backend/migrations/run_migration.py`
- `backend/TRUST_SYSTEM_README.md`

### Modificados:
- `backend/app/models/mood.py` - Agregados campos nivel_confianza y total_interacciones
- `backend/app/services/ai_service.py` - Refactorización completa de prompts
- `backend/app/api/routes/chat.py` - Incremento de contador
- `backend/app/api/routes/whatsapp.py` - Incremento de contador
- `frontend/app/auth/page.tsx` - Fix de React hooks error
- `frontend/app/dashboard/page.tsx` - Actualización de clases Tailwind
- `frontend/app/page.tsx` - Actualización de clases Tailwind

## Beneficios

1. **Menos verbosidad**: Loki ya no habla tanto, especialmente al principio
2. **Más natural**: Se siente como una relación que crece orgánicamente
3. **Sin cursilería**: Eliminadas frases terapéuticas repetitivas
4. **Mejor engagement**: El usuario ve que Loki evoluciona con ellos
5. **Respuestas adaptadas**: Cada nivel tiene el tono y longitud apropiados

## Próximos Pasos Sugeridos

1. **Mensajes de transición**: Cuando sube de nivel, Loki podría mencionarlo sutilmente
2. **Dashboard**: Mostrar nivel de confianza en el frontend
3. **Analytics**: Trackear qué niveles tienen mejor engagement
4. **Ajuste fino**: Basado en feedback, ajustar umbrales de mensajes
5. **A/B Testing**: Comparar niveles contra sistema anterior

## Notas

- El contador se incrementa en **cada mensaje del usuario**, no en cada respuesta
- El nivel se actualiza **automáticamente** cuando se alcanza el umbral
- La transición es **gradual** y natural
- El sistema es **reversible**: si se necesita resetear, solo poner contador en 0
