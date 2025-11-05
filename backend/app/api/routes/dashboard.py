"""
Dashboard mejorado de Loki - muestra análisis completo del usuario.
Incluye insights de memoria emocional, progreso y temas pendientes.
"""
from fastapi import APIRouter, Depends, Query, HTTPException
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
import json

from app.db.session import get_db
from app.services.auth_service import auth_service
from app.crud import mood as crud
from app.services.pattern_analysis import pattern_service
from app.services.emotional_memory_service import emotional_memory_service
from app.services.progress_tracker_service import progress_tracker_service
from app.services.pending_topics_service import pending_topics_service
from app.services.trust_level_service import trust_service
from app.api.routes.dashboard_helpers import (
    generate_styles, generate_header, generate_stats_section,
    generate_chart_section, generate_insights_section, generate_memories_section,
    generate_topics_section, generate_recent_moods_section, generate_habits_section,
    generate_footer, generate_chart_script
)

router = APIRouter()


@router.get("/auth", response_class=HTMLResponse)
async def dashboard_auth(
    token: str = Query(..., description="JWT token de autenticación"),
    db: Session = Depends(get_db)
):
    """
    Dashboard mejorado con análisis completo e insights inteligentes.
    """
    # Verificar token
    user_data = auth_service.verify_token(token)
    
    if not user_data:
        return _generate_error_page()
    
    # Obtener usuario de la base de datos
    usuario = crud.get_usuario(db, usuario_id=user_data['usuario_id'])
    
    if not usuario:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    
    # Recopilar todos los datos necesarios
    dashboard_data = _collect_dashboard_data(db, usuario)
    
    # Generar HTML del dashboard mejorado
    html_content = _generate_dashboard_html(usuario, dashboard_data)
    
    return html_content


def _generate_error_page() -> str:
    """Genera página de error de autenticación."""
    return """
    <html>
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Error - Loki Dashboard</title>
            <style>
                body {
                    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                    display: flex;
                    justify-content: center;
                    align-items: center;
                    min-height: 100vh;
                    margin: 0;
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                }
                .container {
                    background: white;
                    padding: 2rem;
                    border-radius: 16px;
                    box-shadow: 0 10px 40px rgba(0,0,0,0.1);
                    text-align: center;
                    max-width: 400px;
                }
                h1 { color: #e53e3e; margin: 0 0 1rem 0; }
                p { color: #4a5568; line-height: 1.6; }
            </style>
        </head>
        <body>
            <div class="container">
                <h1>❌ Error al verificar el acceso</h1>
                <p>El token ha expirado o no es válido.</p>
                <p>Por favor, solicita un nuevo link escribiendo <strong>"dashboard"</strong> en WhatsApp.</p>
            </div>
        </body>
    </html>
    """


def _collect_dashboard_data(db: Session, usuario) -> dict:
    """Recopila todos los datos necesarios para el dashboard."""
    usuario_id = usuario.id
    
    # Datos básicos
    estados = crud.get_estados_animo_by_usuario(db, usuario_id=usuario_id)
    habitos = crud.get_habitos_by_usuario(db, usuario_id=usuario_id)
    
    # Estadísticas básicas
    avg_score = sum(e.nivel for e in estados) / len(estados) if estados else 0
    
    # Análisis de patrones
    pattern_analysis = pattern_service.analyze_user_patterns(db, usuario_id, days_lookback=30)
    
    # Nivel de confianza
    trust_info = trust_service.get_user_trust_info(db, usuario_id)
    
    # Memorias emocionales recientes
    emotional_memories = emotional_memory_service.get_recent_memories(db, usuario_id, limit=5)
    
    # Insights de progreso
    progress_insights = progress_tracker_service.get_progress_insights(
        db, usuario_id, incluir_en_prompt=False
    )
    
    # Temas pendientes
    pending_topics = pending_topics_service.get_pending_topics(db, usuario_id, only_active=True)
    
    # Últimos 30 días para gráfica
    cutoff_date = datetime.utcnow() - timedelta(days=30)
    recent_moods = [e for e in estados if e.timestamp >= cutoff_date]
    
    # Preparar datos para gráfica
    mood_chart_data = _prepare_mood_chart_data(recent_moods)
    
    return {
        'estados': estados,
        'habitos': habitos,
        'avg_score': avg_score,
        'pattern_analysis': pattern_analysis,
        'trust_info': trust_info,
        'emotional_memories': emotional_memories,
        'progress_insights': progress_insights,
        'pending_topics': pending_topics,
        'mood_chart_data': mood_chart_data,
        'recent_moods': recent_moods,
    }


def _prepare_mood_chart_data(recent_moods) -> dict:
    """Prepara datos para la gráfica de estado de ánimo."""
    if not recent_moods:
        return {'labels': [], 'data': []}
    
    # Agrupar por día
    from collections import defaultdict
    daily_moods = defaultdict(list)
    
    for mood in recent_moods:
        date_key = mood.timestamp.strftime('%Y-%m-%d')
        daily_moods[date_key].append(mood.nivel)
    
    # Calcular promedio diario
    sorted_dates = sorted(daily_moods.keys())
    labels = [datetime.strptime(d, '%Y-%m-%d').strftime('%d/%m') for d in sorted_dates]
    data = [sum(daily_moods[d]) / len(daily_moods[d]) for d in sorted_dates]
    
    return {
        'labels': labels,
        'data': data
    }


def _generate_dashboard_html(usuario, data: dict) -> str:
    """Genera el HTML completo del dashboard mejorado."""
    
    # Generar secciones HTML
    stats_html = generate_stats_section(usuario, data)
    chart_html = generate_chart_section(data)
    insights_html = generate_insights_section(data)
    memories_html = generate_memories_section(data)
    topics_html = generate_topics_section(data)
    recent_moods_html = generate_recent_moods_section(data)
    habits_html = generate_habits_section(data)
    
    return f"""
    <!DOCTYPE html>
    <html lang="es">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Dashboard - {usuario.nombre} | Loki</title>
            <script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js"></script>
            {generate_styles()}
        </head>
        <body>
            <div class="container">
                {generate_header(usuario, data)}
                {stats_html}
                {chart_html}
                {insights_html}
                {memories_html}
                {topics_html}
                <div class="grid-2">
                    {recent_moods_html}
                    {habits_html}
                </div>
                {generate_footer()}
            </div>
            {generate_chart_script(data)}
        </body>
    </html>
    """
