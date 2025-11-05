# 🔄 Guía para Reiniciar Conversación con Loki

## Opciones Disponibles

### 1. 🌊 Reset Suave (Recomendado)
Borra **solo** el historial de conversaciones.

**Mantiene:**
- ✅ Estados de ánimo registrados
- ✅ Hábitos y registros
- ✅ Nivel de confianza
- ✅ Perfil de usuario
- ✅ Memorias emocionales
- ✅ Temas pendientes

**Ideal para:** Empezar una nueva conversación sin perder tu progreso.

### 2. 🔥 Reset Completo
Borra **TODO** excepto tu cuenta de usuario.

**Elimina:**
- ❌ Historial de conversaciones
- ❌ Estados de ánimo
- ❌ Hábitos y registros
- ❌ Nivel de confianza (vuelve a 1)
- ❌ Perfil completo
- ❌ Memorias emocionales
- ❌ Temas pendientes

**Ideal para:** Empezar completamente de cero con Loki.

---

## 🛠️ Métodos de Uso

### Opción A: API Endpoint (Desde código/Postman)

```bash
# Reset Suave
DELETE http://localhost:8000/chat/reset/1?tipo_reset=suave

# Reset Completo
DELETE http://localhost:8000/chat/reset/1?tipo_reset=completo
```

**Usando curl:**
```bash
# Reset Suave
curl -X DELETE "http://localhost:8000/chat/reset/1?tipo_reset=suave"

# Reset Completo
curl -X DELETE "http://localhost:8000/chat/reset/1?tipo_reset=completo"
```

**Usando Python requests:**
```python
import requests

# Reemplaza con tu usuario_id
usuario_id = 1

# Reset Suave
response = requests.delete(
    f"http://localhost:8000/chat/reset/{usuario_id}",
    params={"tipo_reset": "suave"}
)
print(response.json())

# Reset Completo
response = requests.delete(
    f"http://localhost:8000/chat/reset/{usuario_id}",
    params={"tipo_reset": "completo"}
)
print(response.json())
```

---

### Opción B: Script de Línea de Comandos (Más Fácil)

```bash
# Navega al directorio backend
cd backend

# Reset Suave (default)
python scripts/reset_conversation.py 1

# Reset Suave (explícito)
python scripts/reset_conversation.py 1 --tipo=suave

# Reset Completo (con confirmación)
python scripts/reset_conversation.py 1 --tipo=completo
```

**Nota:** Reemplaza `1` con tu `usuario_id` real.

---

### Opción C: WhatsApp (Comando de texto)

Actualmente no está implementado como comando de WhatsApp, pero puedes agregarlo si quieres.

---

## 📋 Ejemplo de Uso Completo

### Escenario 1: Solo quiero limpiar el historial
```bash
cd backend
python scripts/reset_conversation.py 1 --tipo=suave
```

**Output esperado:**
```
============================================================
🔄 Reiniciando conversación de: Diego (ID: 1)
📋 Tipo de reset: SUAVE
============================================================

✅ Reset suave completado: Historial de conversaciones borrado.

✅ Reset completado exitosamente para Diego!
```

### Escenario 2: Quiero empezar de cero
```bash
cd backend
python scripts/reset_conversation.py 1 --tipo=completo
```

**Output esperado:**
```
============================================================
🔄 Reiniciando conversación de: Diego (ID: 1)
📋 Tipo de reset: COMPLETO
============================================================

⚠️  ADVERTENCIA: Esto borrará TODO (ánimo, hábitos, perfil). ¿Continuar? (s/n): s
✅ Reset completo realizado: TODO ha sido reiniciado.

✅ Reset completado exitosamente para Diego!
```

---

## 🔍 Verificar Qué Se Borró

Después del reset, puedes verificar con:

```bash
# Ver historial de conversaciones
curl http://localhost:8000/chat/history/1

# Ver estados de ánimo
curl http://localhost:8000/mood/estados/1

# Ver hábitos
curl http://localhost:8000/habits/1
```

---

## ⚠️ Precauciones

1. **No hay vuelta atrás**: Una vez que ejecutes el reset, no puedes recuperar los datos borrados.
2. **Backup recomendado**: Si tienes datos importantes, considera hacer un backup de la base de datos primero.
3. **Usuario ID correcto**: Asegúrate de usar el `usuario_id` correcto (el tuyo suele ser `1` si eres el primer usuario).

---

## 🆘 Troubleshooting

### "Usuario no encontrado"
- Verifica que el `usuario_id` sea correcto
- Lista todos los usuarios: `curl http://localhost:8000/usuarios/`

### "Error al reiniciar conversación"
- Asegúrate de que el backend esté corriendo
- Verifica la conexión a la base de datos
- Revisa los logs del servidor para más detalles

### El script no se ejecuta
- Asegúrate de estar en el directorio `backend`
- Verifica que el entorno virtual esté activado
- Instala dependencias: `pip install -r requirements.txt`

---

## 📚 Recursos Adicionales

- **Documentación de la API**: `http://localhost:8000/docs`
- **Logs del servidor**: Revisa la consola donde corre FastAPI
- **Base de datos**: `backend/database/lokimood.db` (SQLite)
