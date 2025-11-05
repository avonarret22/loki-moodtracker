# 🔧 Guía de Migración a Google Gemini

## ✅ Cambios Completados

### 1. Código Actualizado
- ✅ `ai_service.py`: Soporte para Google Gemini + Claude (fallback)
- ✅ `config.py`: Agregado campo `GOOGLE_API_KEY`
- ✅ `requirements.txt`: Agregado `google-generativeai>=0.8.0`
- ✅ `.env.example`: Actualizado con `GOOGLE_API_KEY`

### 2. Prioridad de APIs
El sistema ahora prioriza en este orden:
1. **Google Gemini** (gratis, rápido) ← NUEVO
2. **Claude** (si Gemini falla o no está configurado)
3. **Reglas** (fallback si nada funciona)

---

## 🚀 Pasos para Activar Gemini

### Paso 1: Obtener API Key de Google AI Studio

1. Ve a: https://aistudio.google.com/app/apikey
2. Haz clic en **"Create API Key"**
3. Selecciona tu proyecto o crea uno nuevo
4. **Copia la API key** generada (empieza con `AIza...`)

### Paso 2: Configurar el archivo `.env`

1. En `backend/` crea un archivo `.env` (si no existe)
2. Agrega esta línea con tu API key:

```bash
# Copia del .env.example y personaliza:

# AI APIs - Solo necesitas Gemini ahora
GOOGLE_API_KEY=AIzaSyXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX  # <-- TU KEY AQUÍ
ANTHROPIC_API_KEY=  # Opcional, solo como fallback
OPENAI_API_KEY=     # No usado actualmente

# El resto de configuraciones (Twilio, DB, etc.)
# ... cópialas de .env.example si es necesario
```

### Paso 3: Probar la Integración

Ejecuta el script de prueba:

```bash
cd backend
python scripts/test_gemini.py
```

**Salida esperada:**
```
🧪 PRUEBA DE INTEGRACIÓN CON GOOGLE GEMINI
============================================================

🤖 Proveedor de IA: gemini

✅ Google Gemini está configurado

📤 Mensaje de prueba: 'Hola, soy Diego'

📥 Respuesta recibida:
   Hola Diego! ¿Cómo estás?

✅ Nombre detectado: Diego

============================================================
✅ PRUEBA EXITOSA - Gemini funcionando correctamente
============================================================
```

---

## 📊 Comparación de Costos

### Google Gemini (gemini-1.5-flash)
- **Tier Gratuito:** ✅ Muy generoso
  - 15 requests/minuto
  - 1 millón requests/día
  - 1,500 requests gratis por día
- **Costo después:** ~$0.075 por 1M tokens
- **Velocidad:** Muy rápida

### Claude (claude-3-haiku)
- **Tier Gratuito:** ❌ Solo $5 USD de crédito inicial
- **Costo:** $0.25 por 1M tokens input / $1.25 por 1M tokens output
- **Velocidad:** Rápida

**Conclusión:** Gemini es la mejor opción para uso personal (100% gratis para tus necesidades).

---

## 🔄 Despliegue en Render

Una vez que pruebes localmente y funcione:

1. **Agregar la variable de entorno en Render:**
   - Ve a tu servicio en Render
   - Settings → Environment
   - Agregar: `GOOGLE_API_KEY = tu_key_aqui`

2. **Hacer commit y push:**
```bash
git add .
git commit -m "feat: Migración a Google Gemini API"
git push origin main
```

3. **Render automáticamente:**
   - Detectará los cambios
   - Instalará `google-generativeai`
   - Reiniciará el servicio
   - ✅ Loki funcionará con Gemini gratis!

---

## 🆘 Troubleshooting

### Error: "Module 'google.generativeai' not found"
```bash
pip install google-generativeai
```

### Error: "Invalid API key"
- Verifica que la key empiece con `AIza`
- Verifica que no tenga espacios al inicio/final
- Genera una nueva key en https://aistudio.google.com/app/apikey

### Gemini responde en inglés
- El prompt del sistema ya está en español
- Si persiste, ajustaremos el prompt

---

## 📝 Siguiente: Después de Probar

Una vez que funcione localmente:
1. ✅ Commit de los cambios
2. ✅ Push a GitHub
3. ✅ Configurar variable en Render
4. ✅ Probar en WhatsApp
5. 🎉 Disfrutar Loki gratis!

---

**¿Dudas?** Ejecuta `python scripts/test_gemini.py` y comparte el output.
