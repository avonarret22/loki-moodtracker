"""
Endpoint temporal de dashboard - muestra datos básicos del usuario
"""
from fastapi import APIRouter, Depends, Query, HTTPException
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.services.auth_service import auth_service
from app.crud import mood as crud

router = APIRouter()


@router.get("/auth", response_class=HTMLResponse)
async def dashboard_auth(
    token: str = Query(..., description="JWT token de autenticación"),
    db: Session = Depends(get_db)
):
    """
    Endpoint temporal de dashboard - verifica token y muestra datos básicos.
    """
    # Verificar token
    user_data = auth_service.verify_token(token)
    
    if not user_data:
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
    
    # Obtener usuario de la base de datos
    usuario = crud.get_usuario(db, usuario_id=user_data['usuario_id'])
    
    if not usuario:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    
    # Obtener estadísticas básicas
    estados = crud.get_estados_animo_by_usuario(db, usuario_id=usuario.id)
    habitos = crud.get_habitos_by_usuario(db, usuario_id=usuario.id)
    
    # Calcular promedio de estados de ánimo
    avg_score = sum(e.puntuacion for e in estados) / len(estados) if estados else 0
    
    # Generar HTML del dashboard
    html_content = f"""
    <html>
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Dashboard - {usuario.nombre}</title>
            <style>
                * {{
                    margin: 0;
                    padding: 0;
                    box-sizing: border-box;
                }}
                body {{
                    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    min-height: 100vh;
                    padding: 2rem;
                }}
                .container {{
                    max-width: 800px;
                    margin: 0 auto;
                }}
                .card {{
                    background: white;
                    padding: 2rem;
                    border-radius: 16px;
                    box-shadow: 0 10px 40px rgba(0,0,0,0.1);
                    margin-bottom: 1.5rem;
                }}
                h1 {{
                    color: #2d3748;
                    margin-bottom: 0.5rem;
                    font-size: 2rem;
                }}
                .subtitle {{
                    color: #718096;
                    margin-bottom: 2rem;
                }}
                .stat {{
                    display: inline-block;
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    color: white;
                    padding: 1rem 2rem;
                    border-radius: 12px;
                    margin: 0.5rem;
                    min-width: 150px;
                }}
                .stat-label {{
                    font-size: 0.875rem;
                    opacity: 0.9;
                    margin-bottom: 0.5rem;
                }}
                .stat-value {{
                    font-size: 2rem;
                    font-weight: bold;
                }}
                .list-item {{
                    background: #f7fafc;
                    padding: 1rem;
                    border-radius: 8px;
                    margin: 0.5rem 0;
                    display: flex;
                    justify-content: space-between;
                    align-items: center;
                }}
                .badge {{
                    background: #667eea;
                    color: white;
                    padding: 0.25rem 0.75rem;
                    border-radius: 12px;
                    font-size: 0.875rem;
                }}
                .emoji {{
                    font-size: 2rem;
                    margin-right: 1rem;
                }}
                h2 {{
                    color: #2d3748;
                    margin: 1.5rem 0 1rem 0;
                    font-size: 1.5rem;
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="card">
                    <h1>👋 Hola, {usuario.nombre}</h1>
                    <p class="subtitle">📱 {usuario.telefono}</p>
                    
                    <div style="text-align: center; margin: 2rem 0;">
                        <div class="stat">
                            <div class="stat-label">Promedio de Ánimo</div>
                            <div class="stat-value">{avg_score:.1f}/10</div>
                        </div>
                        <div class="stat">
                            <div class="stat-label">Registros Totales</div>
                            <div class="stat-value">{len(estados)}</div>
                        </div>
                        <div class="stat">
                            <div class="stat-label">Hábitos Activos</div>
                            <div class="stat-value">{len(habitos)}</div>
                        </div>
                    </div>
                </div>
                
                <div class="card">
                    <h2>📊 Últimos Estados de Ánimo</h2>
                    {''.join([
                        f'''<div class="list-item">
                        <div>
                            <strong>{e.fecha_registro.strftime("%d/%m/%Y %H:%M")}</strong>
                            <p style="color: #718096; margin: 0.25rem 0 0 0;">{e.notas or "Sin notas"}</p>
                        </div>
                        <span class="badge">{e.puntuacion}/10</span>
                    </div>''' for e in estados[-5:][::-1]
                    ])}
                    {'' if estados else '<p style="color: #718096; text-align: center;">Aún no hay registros de estado de ánimo.</p>'}
                </div>
                
                <div class="card">
                    <h2>💪 Hábitos en Seguimiento</h2>
                    {''.join([
                        f'''<div class="list-item">
                        <div>
                            <strong>{h.nombre}</strong>
                            <p style="color: #718096; margin: 0.25rem 0 0 0;">{h.descripcion or "Sin descripción"}</p>
                        </div>
                        <span class="badge">{'🟢 Activo' if h.activo else '⚫ Inactivo'}</span>
                    </div>''' for h in habitos
                    ])}
                    {'' if habitos else '<p style="color: #718096; text-align: center;">Aún no tienes hábitos registrados.</p>'}
                </div>
                
                <div class="card" style="text-align: center; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white;">
                    <p style="opacity: 0.9;">✨ Dashboard temporal v1.0</p>
                    <p style="font-size: 0.875rem; margin-top: 0.5rem; opacity: 0.8;">
                        Sigue usando WhatsApp para registrar tu estado de ánimo
                    </p>
                </div>
            </div>
        </body>
    </html>
    """
    
    return html_content
