# 🎭 Loki MoodTracker - Frontend

Frontend web básico para chatear con Loki, tu compañero de bienestar emocional.

## 🚀 Cómo usar

### 1. Asegúrate de que el backend esté corriendo

En una terminal, desde la carpeta `backend`:

```powershell
cd C:\Users\Diego\Desktop\programacion\experimentos\moodtracker\backend
python -m uvicorn app.main:app --reload
```

Deberías ver:
```
INFO:     Uvicorn running on http://127.0.0.1:8000
```

### 2. Abrir el frontend

Simplemente abre el archivo `index.html` en tu navegador:

**Opción 1: Doble click**
- Navega a la carpeta `frontend`
- Haz doble click en `index.html`

**Opción 2: Desde VS Code**
- Click derecho en `index.html`
- Selecciona "Open with Live Server" (si tienes la extensión instalada)
- O "Reveal in File Explorer" y luego abre el archivo

### 3. ¡Empieza a chatear con Loki! 🎭

El frontend se conectará automáticamente al backend y podrás:

- 💬 Chatear con Loki en tiempo real
- 📊 Ver tus estadísticas (conversaciones, estados de ánimo)
- ✅ Ver los hábitos que Loki ha detectado
- 📜 Consultar tu historial completo
- 😊 Ver todos tus estados de ánimo registrados

## 🎨 Características

- **Interfaz moderna y responsive** - Funciona en desktop y móvil
- **Detección automática de hábitos** - Loki identifica ejercicio, sueño, meditación, etc.
- **Registro de estados de ánimo** - Menciona un número del 1-10
- **Historial completo** - Todas tus conversaciones guardadas
- **Estadísticas en tiempo real** - Ve tu progreso

## 💡 Ejemplos de mensajes

Prueba enviar mensajes como:

- "Hola Loki, hoy me siento genial, un 9 de 10. Hice ejercicio y dormí 8 horas"
- "Me siento un poco mal hoy, nivel 4. No he hecho ejercicio esta semana"
- "Hoy medité 20 minutos y leí un libro, me siento en 7"
- "Estoy estresado por el trabajo, nivel 3"

## 🛠️ Archivos

- `index.html` - Estructura de la página
- `styles.css` - Estilos y diseño
- `app.js` - Lógica de la aplicación y comunicación con la API

## 🔧 Solución de problemas

### "No se pudo conectar con el servidor"

Asegúrate de que:
1. El backend esté corriendo en `http://localhost:8000`
2. No haya errores en la consola del backend
3. El puerto 8000 no esté siendo usado por otra aplicación

### La página se ve mal

- Asegúrate de que los 3 archivos (`index.html`, `styles.css`, `app.js`) estén en la misma carpeta
- Refresca la página (Ctrl+F5 o Cmd+Shift+R)

### No aparecen mis datos

- Abre la consola del navegador (F12) y mira si hay errores
- Verifica que el backend esté respondiendo en `http://localhost:8000/api/v1/usuarios/`

## 🎯 Próximos pasos (mejoras futuras)

- Stack avanzado: Next.js + TypeScript + Chakra UI + Chart.js/D3
- Autenticación delegada (Auth0/Cognito)
- Gráficos de progreso emocional
- Notificaciones y recordatorios
- Exportar datos
- Modo oscuro
- PWA para usar como app móvil

---

¡Disfruta chateando con Loki! 🎭✨
