"""
Funciones helper para generar el dashboard mejorado.
"""
import json


def generate_styles() -> str:
    """Genera los estilos CSS del dashboard."""
    return """
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 1rem;
        }
        .container {
            max-width: 1200px;
            margin: 0 auto;
        }
        .header {
            background: white;
            padding: 2rem;
            border-radius: 16px;
            box-shadow: 0 10px 40px rgba(0,0,0,0.1);
            margin-bottom: 1.5rem;
            text-align: center;
        }
        .header h1 {
            color: #2d3748;
            margin-bottom: 0.5rem;
            font-size: 2.5rem;
        }
        .header-subtitle {
            color: #718096;
            font-size: 1rem;
        }
        .trust-badge {
            display: inline-block;
            background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
            color: white;
            padding: 0.5rem 1.5rem;
            border-radius: 20px;
            font-size: 0.875rem;
            margin-top: 1rem;
            font-weight: 600;
        }
        .card {
            background: white;
            padding: 2rem;
            border-radius: 16px;
            box-shadow: 0 10px 40px rgba(0,0,0,0.1);
            margin-bottom: 1.5rem;
        }
        .card h2 {
            color: #2d3748;
            margin: 0 0 1.5rem 0;
            font-size: 1.75rem;
            display: flex;
            align-items: center;
            gap: 0.5rem;
        }
        .stats-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 1rem;
            margin-bottom: 1.5rem;
        }
        .stat-box {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 1.5rem;
            border-radius: 12px;
            text-align: center;
        }
        .stat-label {
            font-size: 0.875rem;
            opacity: 0.9;
            margin-bottom: 0.5rem;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }
        .stat-value {
            font-size: 2.5rem;
            font-weight: bold;
            margin-bottom: 0.25rem;
        }
        .stat-description {
            font-size: 0.75rem;
            opacity: 0.8;
        }
        .grid-2 {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(350px, 1fr));
            gap: 1.5rem;
        }
        .insight-box {
            background: #f7fafc;
            border-left: 4px solid #667eea;
            padding: 1rem;
            border-radius: 8px;
            margin: 0.75rem 0;
        }
        .insight-box.success {
            border-left-color: #48bb78;
            background: #f0fff4;
        }
        .insight-box.warning {
            border-left-color: #ed8936;
            background: #fffaf0;
        }
        .insight-box.info {
            border-left-color: #4299e1;
            background: #ebf8ff;
        }
        .insight-title {
            font-weight: 600;
            color: #2d3748;
            margin-bottom: 0.5rem;
        }
        .insight-text {
            color: #4a5568;
            line-height: 1.6;
            font-size: 0.9rem;
        }
        .memory-item {
            background: linear-gradient(135deg, #ffeaa7 0%, #fdcb6e 100%);
            padding: 1rem;
            border-radius: 12px;
            margin: 0.75rem 0;
            color: #2d3748;
        }
        .memory-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 0.5rem;
        }
        .memory-tema {
            font-weight: 600;
            font-size: 1.1rem;
        }
        .memory-intensidad {
            background: rgba(255,255,255,0.5);
            padding: 0.25rem 0.75rem;
            border-radius: 12px;
            font-size: 0.875rem;
        }
        .memory-sentimiento {
            color: #e17055;
            font-weight: 500;
            margin-bottom: 0.5rem;
        }
        .topic-item {
            background: #f7fafc;
            padding: 1rem;
            border-radius: 8px;
            margin: 0.75rem 0;
            border-left: 3px solid #667eea;
        }
        .topic-header {
            display: flex;
            justify-content: space-between;
            align-items: flex-start;
            margin-bottom: 0.5rem;
        }
        .topic-tema {
            font-weight: 600;
            color: #2d3748;
            flex: 1;
        }
        .topic-meta {
            font-size: 0.875rem;
            color: #718096;
        }
        .priority-badge {
            display: inline-block;
            padding: 0.25rem 0.75rem;
            border-radius: 12px;
            font-size: 0.875rem;
            font-weight: 600;
            margin-left: 0.5rem;
        }
        .priority-high {
            background: #feb2b2;
            color: #742a2a;
        }
        .priority-medium {
            background: #feebc8;
            color: #7c2d12;
        }
        .priority-low {
            background: #c6f6d5;
            color: #22543d;
        }
        .mood-item {
            background: #f7fafc;
            padding: 1rem;
            border-radius: 8px;
            margin: 0.75rem 0;
        }
        .mood-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 0.5rem;
        }
        .mood-date {
            font-weight: 600;
            color: #2d3748;
        }
        .mood-score {
            background: #667eea;
            color: white;
            padding: 0.25rem 0.75rem;
            border-radius: 12px;
            font-weight: 600;
        }
        .mood-notes {
            color: #718096;
            font-size: 0.9rem;
            line-height: 1.5;
        }
        .habit-item {
            background: #f7fafc;
            padding: 1rem;
            border-radius: 8px;
            margin: 0.75rem 0;
        }
        .habit-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 0.5rem;
        }
        .habit-name {
            font-weight: 600;
            color: #2d3748;
        }
        .habit-status {
            padding: 0.25rem 0.75rem;
            border-radius: 12px;
            font-size: 0.875rem;
            font-weight: 600;
        }
        .habit-active {
            background: #c6f6d5;
            color: #22543d;
        }
        .habit-inactive {
            background: #e2e8f0;
            color: #4a5568;
        }
        .empty-state {
            text-align: center;
            padding: 3rem 1rem;
            color: #a0aec0;
        }
        .empty-state-icon {
            font-size: 4rem;
            margin-bottom: 1rem;
        }
        .chart-container {
            position: relative;
            height: 300px;
            margin: 1rem 0;
        }
        .footer {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 2rem;
            border-radius: 16px;
            text-align: center;
            margin-top: 2rem;
        }
        .footer p {
            opacity: 0.9;
            margin: 0.5rem 0;
        }
        @media (max-width: 768px) {
            .stats-grid {
                grid-template-columns: 1fr;
            }
            .grid-2 {
                grid-template-columns: 1fr;
            }
            .header h1 {
                font-size: 1.75rem;
            }
            .stat-value {
                font-size: 2rem;
            }
        }
    </style>
    """


def generate_header(usuario, data: dict) -> str:
    """Genera el encabezado del dashboard."""
    trust_info = data.get('trust_info', {})
    nivel_nombre = trust_info.get('nivel_nombre', 'Conociendo') if trust_info else 'Conociendo'
    interacciones = trust_info.get('total_interacciones', 0) if trust_info else 0
    
    return f"""
    <div class="header">
        <h1>👋 Hola, {usuario.nombre}</h1>
        <p class="header-subtitle">📱 {usuario.telefono}</p>
        <span class="trust-badge">
            🤝 Nivel de Confianza: {nivel_nombre} ({interacciones} interacciones)
        </span>
    </div>
    """


def generate_stats_section(usuario, data: dict) -> str:
    """Genera la sección de estadísticas principales."""
    avg_score = data.get('avg_score', 0)
    estados_count = len(data.get('estados', []))
    habitos_count = len(data.get('habitos', []))
    memories_count = len(data.get('emotional_memories', []))
    pending_count = len(data.get('pending_topics', []))
    
    # Determinar tendencia
    recent_moods = data.get('recent_moods', [])
    tendencia = "Estable"
    if len(recent_moods) >= 7:
        last_7 = [m.nivel for m in recent_moods[-7:]]
        first_half = sum(last_7[:3]) / 3
        second_half = sum(last_7[-3:]) / 3
        if second_half > first_half + 1:
            tendencia = "↗️ Mejorando"
        elif second_half < first_half - 1:
            tendencia = "↘️ Descendiendo"
        else:
            tendencia = "→ Estable"
    
    return f"""
    <div class="card">
        <h2>📊 Resumen General</h2>
        <div class="stats-grid">
            <div class="stat-box">
                <div class="stat-label">Ánimo Promedio</div>
                <div class="stat-value">{avg_score:.1f}</div>
                <div class="stat-description">sobre 10</div>
            </div>
            <div class="stat-box">
                <div class="stat-label">Tendencia</div>
                <div class="stat-value">{tendencia}</div>
                <div class="stat-description">últimos 7 días</div>
            </div>
            <div class="stat-box">
                <div class="stat-label">Registros</div>
                <div class="stat-value">{estados_count}</div>
                <div class="stat-description">total de entradas</div>
            </div>
            <div class="stat-box">
                <div class="stat-label">Memorias</div>
                <div class="stat-value">{memories_count}</div>
                <div class="stat-description">momentos significativos</div>
            </div>
            <div class="stat-box">
                <div class="stat-label">Temas Pendientes</div>
                <div class="stat-value">{pending_count}</div>
                <div class="stat-description">en seguimiento</div>
            </div>
            <div class="stat-box">
                <div class="stat-label">Hábitos</div>
                <div class="stat-value">{habitos_count}</div>
                <div class="stat-description">activos</div>
            </div>
        </div>
    </div>
    """


def generate_chart_section(data: dict) -> str:
    """Genera la sección de gráfica."""
    chart_data = data.get('mood_chart_data', {'labels': [], 'data': []})
    
    if not chart_data['labels']:
        return """
        <div class="card">
            <h2>📈 Evolución del Ánimo (últimos 30 días)</h2>
            <div class="empty-state">
                <div class="empty-state-icon">📊</div>
                <p>Registra tu estado de ánimo para ver la evolución</p>
            </div>
        </div>
        """
    
    return """
    <div class="card">
        <h2>📈 Evolución del Ánimo (últimos 30 días)</h2>
        <div class="chart-container">
            <canvas id="moodChart"></canvas>
        </div>
    </div>
    """


def generate_insights_section(data: dict) -> str:
    """Genera la sección de insights."""
    pattern_analysis = data.get('pattern_analysis', {})
    progress_insights = data.get('progress_insights')
    
    insights_html = ""
    
    # Insight de progreso
    if progress_insights:
        tipo = progress_insights.tipo
        mensaje = progress_insights.mensaje_contexto
        insights_html += f"""
        <div class="insight-box success">
            <div class="insight-title">🎉 Progreso Detectado</div>
            <div class="insight-text">{mensaje}</div>
        </div>
        """
    
    # Insights de patrones
    if pattern_analysis.get('has_enough_data'):
        insights_list = pattern_analysis.get('insights', [])
        for insight in insights_list[:3]:  # Máximo 3 insights
            insights_html += f"""
            <div class="insight-box info">
                <div class="insight-title">💡 Patrón Detectado</div>
                <div class="insight-text">{insight}</div>
            </div>
            """
        
        # Estabilidad emocional
        stability = pattern_analysis.get('mood_stability', 0)
        if stability < 2:
            stability_text = "Tu estado de ánimo es muy estable. ¡Excelente!"
            stability_class = "success"
        elif stability < 3:
            stability_text = "Tu estado de ánimo tiene variaciones normales."
            stability_class = "info"
        else:
            stability_text = "Detectamos variaciones significativas en tu ánimo. Considera identificar los factores."
            stability_class = "warning"
        
        insights_html += f"""
        <div class="insight-box {stability_class}">
            <div class="insight-title">📊 Estabilidad Emocional</div>
            <div class="insight-text">{stability_text}</div>
        </div>
        """
    
    if not insights_html:
        insights_html = """
        <div class="empty-state">
            <div class="empty-state-icon">🔍</div>
            <p>Necesitamos más datos para generar insights personalizados</p>
        </div>
        """
    
    return f"""
    <div class="card">
        <h2>💡 Insights Personalizados</h2>
        {insights_html}
    </div>
    """


def generate_memories_section(data: dict) -> str:
    """Genera la sección de memorias emocionales."""
    memories = data.get('emotional_memories', [])
    
    if not memories:
        return """
        <div class="card">
            <h2>💭 Memorias Emocionales Significativas</h2>
            <div class="empty-state">
                <div class="empty-state-icon">💭</div>
                <p>Aún no hay memorias emocionales registradas</p>
            </div>
        </div>
        """
    
    memories_html = ""
    for memory in memories[:5]:
        memories_html += f"""
        <div class="memory-item">
            <div class="memory-header">
                <span class="memory-tema">{memory.tema}</span>
                <span class="memory-intensidad">Intensidad: {memory.intensidad_emocional}/10</span>
            </div>
            <div class="memory-sentimiento">Sentimiento: {memory.sentimiento}</div>
            <div class="memory-context">{memory.contexto[:150]}...</div>
        </div>
        """
    
    return f"""
    <div class="card">
        <h2>💭 Memorias Emocionales Significativas</h2>
        {memories_html}
    </div>
    """


def generate_topics_section(data: dict) -> str:
    """Genera la sección de temas pendientes."""
    topics = data.get('pending_topics', [])
    
    if not topics:
        return """
        <div class="card">
            <h2>🎯 Temas en Seguimiento</h2>
            <div class="empty-state">
                <div class="empty-state-icon">🎯</div>
                <p>No hay temas pendientes en este momento</p>
            </div>
        </div>
        """
    
    topics_html = ""
    for topic in topics[:5]:
        # Determinar badge de prioridad
        if topic.prioridad >= 7:
            priority_class = "priority-high"
            priority_label = "Alta"
        elif topic.prioridad >= 4:
            priority_class = "priority-medium"
            priority_label = "Media"
        else:
            priority_class = "priority-low"
            priority_label = "Baja"
        
        topics_html += f"""
        <div class="topic-item">
            <div class="topic-header">
                <span class="topic-tema">{topic.tema_extraido}</span>
                <span class="priority-badge {priority_class}">{priority_label}</span>
            </div>
            <div class="topic-meta">
                📅 Hace {topic.dias_desde_mencion} día(s) | 
                📁 {topic.categoria.capitalize()}
            </div>
        </div>
        """
    
    return f"""
    <div class="card">
        <h2>🎯 Temas en Seguimiento</h2>
        {topics_html}
    </div>
    """


def generate_recent_moods_section(data: dict) -> str:
    """Genera la sección de estados de ánimo recientes."""
    estados = data.get('estados', [])
    
    if not estados:
        return """
        <div class="card">
            <h2>📝 Últimos Registros</h2>
            <div class="empty-state">
                <div class="empty-state-icon">📝</div>
                <p>Aún no hay registros de estado de ánimo</p>
            </div>
        </div>
        """
    
    moods_html = ""
    for estado in reversed(estados[-10:]):
        moods_html += f"""
        <div class="mood-item">
            <div class="mood-header">
                <span class="mood-date">{estado.timestamp.strftime('%d/%m/%Y %H:%M')}</span>
                <span class="mood-score">{estado.nivel}/10</span>
            </div>
            <div class="mood-notes">{estado.notas_texto or 'Sin notas'}</div>
        </div>
        """
    
    return f"""
    <div class="card">
        <h2>📝 Últimos Registros</h2>
        {moods_html}
    </div>
    """


def generate_habits_section(data: dict) -> str:
    """Genera la sección de hábitos."""
    habitos = data.get('habitos', [])
    
    if not habitos:
        return """
        <div class="card">
            <h2>💪 Hábitos</h2>
            <div class="empty-state">
                <div class="empty-state-icon">💪</div>
                <p>Aún no tienes hábitos en seguimiento</p>
            </div>
        </div>
        """
    
    habits_html = ""
    for habito in habitos:
        status_class = "habit-active" if habito.activo else "habit-inactive"
        status_text = "🟢 Activo" if habito.activo else "⚫ Inactivo"
        
        habits_html += f"""
        <div class="habit-item">
            <div class="habit-header">
                <span class="habit-name">{habito.nombre_habito}</span>
                <span class="habit-status {status_class}">{status_text}</span>
            </div>
            <div class="mood-notes">
                Categoría: {habito.categoria or 'General'} | 
                Objetivo: {habito.objetivo_semanal or 0} veces/semana
            </div>
        </div>
        """
    
    return f"""
    <div class="card">
        <h2>💪 Hábitos</h2>
        {habits_html}
    </div>
    """


def generate_footer() -> str:
    """Genera el footer del dashboard."""
    return """
    <div class="footer">
        <p style="font-size: 1.25rem; margin-bottom: 0.5rem;">✨ Loki Dashboard v2.0</p>
        <p style="font-size: 0.875rem;">Continúa usando WhatsApp para hablar con Loki y registrar tu estado de ánimo</p>
        <p style="font-size: 0.75rem; margin-top: 1rem; opacity: 0.7;">Este dashboard se actualiza automáticamente con tus conversaciones</p>
    </div>
    """


def generate_chart_script(data: dict) -> str:
    """Genera el script de Chart.js para la gráfica."""
    chart_data = data.get('mood_chart_data', {'labels': [], 'data': []})
    
    if not chart_data['labels']:
        return "<script></script>"
    
    labels_json = json.dumps(chart_data['labels'])
    data_json = json.dumps(chart_data['data'])
    
    return f"""
    <script>
        const ctx = document.getElementById('moodChart');
        if (ctx) {{
            new Chart(ctx, {{
                type: 'line',
                data: {{
                    labels: {labels_json},
                    datasets: [{{
                        label: 'Estado de Ánimo',
                        data: {data_json},
                        borderColor: '#667eea',
                        backgroundColor: 'rgba(102, 126, 234, 0.1)',
                        tension: 0.4,
                        fill: true,
                        pointBackgroundColor: '#667eea',
                        pointBorderColor: '#fff',
                        pointHoverBackgroundColor: '#fff',
                        pointHoverBorderColor: '#667eea',
                        pointRadius: 5,
                        pointHoverRadius: 7
                    }}]
                }},
                options: {{
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {{
                        legend: {{
                            display: false
                        }},
                        tooltip: {{
                            backgroundColor: 'rgba(0,0,0,0.8)',
                            padding: 12,
                            titleFont: {{ size: 14 }},
                            bodyFont: {{ size: 16 }},
                            callbacks: {{
                                label: function(context) {{
                                    return 'Ánimo: ' + context.parsed.y.toFixed(1) + '/10';
                                }}
                            }}
                        }}
                    }},
                    scales: {{
                        y: {{
                            beginAtZero: true,
                            max: 10,
                            ticks: {{
                                stepSize: 2
                            }},
                            grid: {{
                                color: 'rgba(0,0,0,0.05)'
                            }}
                        }},
                        x: {{
                            grid: {{
                                display: false
                            }}
                        }}
                    }}
                }}
            }});
        }}
    </script>
    """
