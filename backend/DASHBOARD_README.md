# 📊 Dashboard Loki v2.0 - Documentación

## 🎯 Descripción General

El Dashboard v2.0 es una interfaz web mejorada que muestra análisis completos del estado emocional del usuario, integrando todas las mejoras de personalidad de Loki.

## ✨ Características Principales

### 1. **Resumen General** 📊
Muestra 6 métricas clave en cards con gradientes:

- **Ánimo Promedio**: Promedio histórico sobre 10
- **Tendencia**: Análisis de últimos 7 días (↗️ Mejorando / → Estable / ↘️ Descendiendo)
- **Registros**: Total de entradas de ánimo
- **Memorias**: Momentos emocionalmente significativos guardados
- **Temas Pendientes**: Items en seguimiento activo
- **Hábitos**: Hábitos activos registrados

### 2. **Gráfica de Evolución** 📈
- Gráfica interactiva con **Chart.js 4.4.0**
- Muestra últimos 30 días
- Promedio diario de estado de ánimo
- Tooltips informativos
- Diseño responsive

### 3. **Insights Personalizados** 💡
Combina múltiples fuentes de análisis:

#### a) **Progreso Detectado** 🎉
- Integra `progress_tracker_service`
- Muestra mejoras de ánimo detectadas
- Rachas positivas
- Superación de dificultades

#### b) **Patrones Detectados** 🔍
- Integra `pattern_service`
- Correlaciones hábitos-ánimo
- Patrones temporales
- Máximo 3 insights prioritarios

#### c) **Estabilidad Emocional** 📊
- Calcula desviación estándar del ánimo
- Clasifica en 3 niveles:
  * **Muy estable** (σ < 2): Verde
  * **Normal** (2 ≤ σ < 3): Azul
  * **Variable** (σ ≥ 3): Naranja

### 4. **Memorias Emocionales** 💭
- Integra `emotional_memory_service`
- Muestra últimas 5 memorias significativas
- Información mostrada:
  * Tema principal
  * Sentimiento asociado
  * Intensidad emocional (/10)
  * Contexto (primeros 150 chars)
- Diseño con gradiente amarillo-naranja

### 5. **Temas en Seguimiento** 🎯
- Integra `pending_topics_service`
- Muestra hasta 5 temas pendientes activos
- Información por tema:
  * Descripción del tema
  * Días desde mención
  * Categoría (trabajo, salud, relaciones, personal, tareas)
  * Prioridad con color coding:
    - 🔴 **Alta** (≥7): Rojo
    - 🟡 **Media** (4-6): Naranja
    - 🟢 **Baja** (<4): Verde

### 6. **Últimos Registros** 📝
- Últimos 10 estados de ánimo
- Fecha y hora precisas
- Puntuación sobre 10
- Notas asociadas
- Orden cronológico inverso (más reciente primero)

### 7. **Hábitos** 💪
- Lista todos los hábitos registrados
- Estado visual (🟢 Activo / ⚫ Inactivo)
- Categoría del hábito
- Objetivo semanal

## 🎨 Diseño

### Paleta de Colores
```css
Primario: #667eea → #764ba2 (gradient)
Secundario: #f093fb → #f5576c (gradient)
Acentos memorias: #ffeaa7 → #fdcb6e (gradient)
Backgrounds: #f7fafc (light gray)
Texto: #2d3748 (dark gray)
Subtexto: #718096 (medium gray)
```

### Componentes Visuales

#### Stats Cards
- Gradiente purple
- Texto blanco
- Valores grandes (2.5rem)
- Labels pequeños uppercase

#### Insight Boxes
- Border izquierdo colorido (4px)
- Background suave según tipo
- Título bold
- Texto explicativo

#### Chart Container
- Altura fija: 300px
- Responsive
- Fondo blanco
- Bordes redondeados

### Responsive Design
```css
Desktop (>768px): Grid 2 columnas
Mobile (≤768px): Stack vertical
```

## 🔌 Integraciones

### Servicios Backend
```python
# Análisis de patrones
pattern_service.analyze_user_patterns(db, usuario_id, days_lookback=30)

# Memoria emocional
emotional_memory_service.get_recent_memories(db, usuario_id, limit=5)

# Progreso
progress_tracker_service.get_progress_insights(db, usuario_id, incluir_en_prompt=False)

# Temas pendientes
pending_topics_service.get_pending_topics(db, usuario_id, only_active=True)

# Nivel de confianza
trust_service.get_user_trust_info(db, usuario_id)
```

### Endpoints
```
GET /api/dashboard/auth?token={JWT}
```

**Parámetros:**
- `token` (query): JWT de autenticación generado desde WhatsApp

**Respuestas:**
- `200 OK`: HTML del dashboard completo
- Error page: Si token inválido/expirado

## 📱 Acceso

1. Usuario escribe **"dashboard"** en WhatsApp con Loki
2. Loki genera link temporal con JWT
3. Link válido por tiempo limitado (configurado en `auth_service`)
4. Dashboard se actualiza en tiempo real con datos de BD

## 🚀 Ventajas vs v1.0

| Característica | v1.0 | v2.0 |
|---------------|------|------|
| Gráficas | ❌ | ✅ Chart.js interactivo |
| Insights | ❌ | ✅ Múltiples fuentes |
| Memorias | ❌ | ✅ Significativas |
| Temas pendientes | ❌ | ✅ Con prioridades |
| Progreso | ❌ | ✅ Detección automática |
| Tendencias | ❌ | ✅ Análisis 7 días |
| Responsive | Básico | ✅ Mobile-first |
| Diseño | Simple | ✅ Moderno con gradientes |
| Métricas | 3 | 6+ |

## 🔧 Mantenimiento

### Agregar Nueva Sección
1. Crear función en `dashboard_helpers.py`:
```python
def generate_nueva_seccion(data: dict) -> str:
    return """<div class="card">...</div>"""
```

2. Importar en `dashboard.py`

3. Agregar a `_generate_dashboard_html()`:
```python
nueva_seccion_html = generate_nueva_seccion(data)
```

4. Insertar en template HTML

### Modificar Estilos
Editar función `generate_styles()` en `dashboard_helpers.py`

### Agregar Métrica
1. Calcular en `_collect_dashboard_data()`
2. Pasar en dict `data`
3. Mostrar en la sección correspondiente

## 📊 Datos Recopilados

```python
dashboard_data = {
    'estados': List[EstadoAnimo],
    'habitos': List[Habito],
    'avg_score': float,
    'pattern_analysis': dict,
    'trust_info': dict,
    'emotional_memories': List[EmotionalMemory],
    'progress_insights': Optional[ProgressInsight],
    'pending_topics': List[PendingTopic],
    'mood_chart_data': {
        'labels': List[str],  # Fechas
        'data': List[float]   # Scores
    },
    'recent_moods': List[EstadoAnimo]
}
```

## 🎯 Próximas Mejoras Potenciales

1. **Filtros temporales**: Permitir ver 7/30/90 días
2. **Comparación de períodos**: Este mes vs mes anterior
3. **Exportar PDF**: Generar reportes descargables
4. **Gráficas adicionales**: Por categoría de hábito
5. **Objetivos personales**: Tracking de metas
6. **Compartir insights**: Exportar insights específicos
7. **Dark mode**: Tema oscuro opcional
8. **Notificaciones**: Alertas de patrones críticos

## 💻 Tecnologías

- **Backend**: FastAPI, SQLAlchemy
- **Frontend**: HTML5, CSS3, JavaScript
- **Gráficas**: Chart.js 4.4.0
- **Diseño**: CSS Grid, Flexbox
- **Autenticación**: JWT tokens

## 🔒 Seguridad

- Token JWT temporal
- Validación en cada request
- Sin almacenamiento de tokens en cliente
- HTTPS requerido en producción
- Rate limiting (configurado en Railway)

---

**Versión**: 2.0  
**Fecha**: Noviembre 2025  
**Autor**: Sistema LokiMood
