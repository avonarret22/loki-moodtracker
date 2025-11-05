# 🎭 Sistema de Obtención del Nombre del Usuario

## ✨ Nueva Funcionalidad: Loki Pregunta tu Nombre

### 📋 Descripción
Implementado un flujo natural donde Loki pregunta el nombre del usuario en la primera interacción si no está registrado. Esto hace que la experiencia sea más personal y orgánica desde el inicio.

### 🔄 Flujo de Interacción

#### **Primera Interacción (Sin nombre):**
```
Usuario: "Hola"
Loki: "Hola! Soy Loki 🐺 ¿Cómo te llamas?"
```

#### **Segunda Interacción (Detecta el nombre):**
```
Usuario: "Diego"
Loki: "Encantado, Diego! ¿Cómo estás hoy?"
```

#### **A partir de ahí:**
Loki usa el nombre en todas las conversaciones y en los prompts del sistema.

---

## 🛠️ Cambios Técnicos

### 1. **Modelo de Datos**
- ✅ Campo `nombre` ahora es **opcional (nullable)** en `Usuario`
- ✅ Schema `UsuarioCreate` acepta `nombre` como `Optional[str]`
- ✅ Migración `make_nombre_nullable` para actualizar la BD

### 2. **Servicio de IA (`ai_service.py`)**
Nuevos métodos agregados:

#### `_is_asking_for_name(usuario_nombre: Optional[str]) -> bool`
Determina si debemos preguntar el nombre.

#### `_extract_name_from_message(mensaje: str) -> Optional[str]`
Extrae el nombre del mensaje del usuario con patrones inteligentes:
- "Me llamo Diego" → Diego
- "Soy María José" → María José
- "Diego" (solo) → Diego
- "Llámame Carlos" → Carlos

**Filtrado de palabras comunes:**
- Excluye: hola, hi, bien, gracias, etc.
- Solo acepta nombres válidos (2-30 caracteres, solo letras)

#### `_generate_ask_name_response() -> str`
Genera saludos naturales variados:
- "Hola! Soy Loki 🐺 ¿Cómo te llamas?"
- "Hey! Soy Loki. ¿Cómo prefieres que te llame?"
- Y más variantes...

#### `_generate_greeting_with_name(nombre: str) -> str`
Genera saludos personalizados después de conocer el nombre:
- "Encantado, Diego! ¿Cómo estás hoy?"
- "Genial conocerte, María. ¿Cómo te sientes?"
- Y más variantes...

### 3. **Modificación de `generate_response()`**
Ahora incluye lógica de 3 fases:

**Fase 1:** Sin nombre y sin contexto → Pide el nombre
```python
return {
    'respuesta': "Hola! Soy Loki 🐺 ¿Cómo te llamas?",
    'esperando_nombre': True
}
```

**Fase 2:** Sin nombre pero con contexto → Extrae y guarda el nombre
```python
nombre_detectado = self._extract_name_from_message(mensaje_usuario)
if nombre_detectado:
    # Guardar en BD
    usuario.nombre = nombre_detectado
    return {
        'respuesta': f"Encantado, {nombre_detectado}! ¿Cómo estás?",
        'nombre_detectado': nombre_detectado
    }
```

**Fase 3:** Con nombre → Flujo normal de conversación

### 4. **Tests Completos (`test_name_acquisition.py`)**
✅ **16 tests implementados**, todos pasan:
- Test de detección de necesidad de nombre
- Test de extracción de nombres (múltiples patrones)
- Test de filtrado de palabras comunes
- Test de validación de nombres inválidos
- Test de generación de respuestas
- Test del flujo completo end-to-end

---

## 📊 Cobertura de Tests

```
tests/test_name_acquisition.py::TestNameAcquisitionFlow
  ✅ test_is_asking_for_name_with_none
  ✅ test_is_asking_for_name_with_empty_string
  ✅ test_is_asking_for_name_with_valid_name
  ✅ test_extract_name_from_message_simple_name
  ✅ test_extract_name_from_message_with_me_llamo
  ✅ test_extract_name_from_message_with_soy
  ✅ test_extract_name_from_message_with_mi_nombre_es
  ✅ test_extract_name_from_message_with_llamame
  ✅ test_extract_name_from_message_invalid_names
  ✅ test_extract_name_from_message_non_name_responses
  ✅ test_generate_ask_name_response
  ✅ test_generate_greeting_with_name
  ✅ test_generate_response_asks_for_name_first_time
  ✅ test_generate_response_extracts_name_second_time
  ✅ test_generate_response_asks_again_if_invalid_name
  ✅ test_generate_response_normal_flow_with_name

16 passed, 1 warning in 1.25s
```

---

## 🎯 Beneficios

### Para el Usuario:
- ✨ Experiencia más **personal** desde el primer mensaje
- 🤝 Loki se presenta y pregunta tu nombre **naturalmente**
- 💬 No necesitas llenar formularios de registro
- 🎭 La conversación fluye de forma **orgánica**

### Para el Sistema:
- 🔒 **Validación automática** de nombres (evita nombres inválidos)
- 🧠 **Detección inteligente** de múltiples formatos de presentación
- 🛡️ **Filtrado robusto** de palabras comunes que no son nombres
- 📝 **Persistencia automática** en la base de datos
- 🔄 **Retrocompatibilidad** con usuarios existentes que ya tienen nombre

---

## 🚀 Próximos Pasos

Esta mejora es parte del **Improvement #1: Personalización y Memoria Emocional**.

Pendientes (del roadmap de 8 mejoras):
- ✅ 1. Memoria Emocional Mejorada (90% completo)
- ✅ 1.5. Obtención Natural del Nombre (100% completo - ESTE)
- ⏳ 2. Celebración de Progresos
- ⏳ 3. Proactividad Contextual
- ⏳ 4. Detección de Patrones Temporales
- ⏳ 5. Personalización del Tono
- ⏳ 6. Detección de Crisis
- ⏳ 7. Modo Check-in Inteligente
- ⏳ 8. Referencias Temporales

---

## 📝 Notas de Implementación

### Patrones de Extracción Soportados:
```python
✅ "Diego"                    → Diego
✅ "Me llamo Diego"           → Diego
✅ "Soy María José"           → María José
✅ "Mi nombre es Carlos"      → Carlos
✅ "Llámame Ana"              → Ana
✅ "Dime Juan"                → Juan
✅ "Puedes decirme Pedro"     → Pedro

❌ "hola"                     → None (palabra común)
❌ "X"                        → None (muy corto)
❌ "Diego123"                 → None (números)
❌ "Nombre muy largo que..."  → None (>30 caracteres)
```

### Capitalización Inteligente:
- `"diego"` → `"Diego"`
- `"maría josé"` → `"María José"`
- `"CARLOS"` → `"Carlos"`

### Base de Datos:
La migración se aplicará automáticamente en Railway al hacer deploy.
No afecta a usuarios existentes que ya tienen nombre.

---

**Fecha:** 5 de Noviembre, 2025  
**Versión:** 1.1.0  
**Estado:** ✅ Implementado y Testeado
