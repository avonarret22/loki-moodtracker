"""
Endpoints de autenticación para acceso al dashboard.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func, cast, Integer
from pydantic import BaseModel
from datetime import datetime, timedelta
from collections import defaultdict

from app.db.session import get_db
from app.services.auth_service import auth_service
from app.services.trust_level_service import trust_service
from app.crud import mood as crud
from app.models.mood import EstadoAnimo, RegistroHabito

router = APIRouter()


class TokenResponse(BaseModel):
    """Respuesta con token de acceso."""
    access_token: str
    token_type: str = "bearer"
    expires_in: int = 86400  # 24 horas en segundos
    dashboard_url: str


class TokenVerifyRequest(BaseModel):
    """Request para verificar un token."""
    token: str


class TokenVerifyResponse(BaseModel):
    """Respuesta de verificación de token."""
    valid: bool
    usuario_id: int | None = None
    telefono: str | None = None
    expires_at: int | None = None


@router.post("/generate-token/{telefono}", response_model=TokenResponse)
async def generate_dashboard_token(
    telefono: str,
    db: Session = Depends(get_db)
):
    """
    Genera un token de acceso al dashboard para un usuario.
    
    Este endpoint es llamado internamente cuando un usuario solicita
    ver su dashboard desde WhatsApp.
    
    Args:
        telefono: Número de teléfono del usuario (en formato WhatsApp)
        
    Returns:
        Token de acceso y URL completa del dashboard
    """
    # Limpiar formato de WhatsApp si viene con "whatsapp:"
    telefono_limpio = telefono.replace("whatsapp:", "").strip()
    
    # Buscar usuario por teléfono
    usuario = crud.get_usuario_by_telefono(db, telefono=telefono_limpio)
    
    if not usuario:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Usuario con teléfono {telefono_limpio} no encontrado"
        )
    
    # Generar link completo al dashboard
    dashboard_link = auth_service.generate_dashboard_link(
        usuario_id=usuario.id,
        telefono=usuario.telefono
    )
    
    # Generar solo el token para la respuesta
    token = auth_service.generate_dashboard_token(
        usuario_id=usuario.id,
        telefono=usuario.telefono
    )
    
    return TokenResponse(
        access_token=token,
        dashboard_url=dashboard_link
    )


@router.post("/verify-token", response_model=TokenVerifyResponse)
async def verify_dashboard_token(
    request: TokenVerifyRequest
):
    """
    Verifica si un token es válido y retorna la información del usuario.
    
    Este endpoint será usado por el frontend del dashboard para
    validar tokens cuando un usuario accede.
    
    Args:
        request: Request con el token a verificar
        
    Returns:
        Información de validez y datos del usuario
    """
    token_data = auth_service.verify_token(request.token)
    
    if not token_data:
        return TokenVerifyResponse(valid=False)
    
    return TokenVerifyResponse(
        valid=True,
        usuario_id=token_data.get('usuario_id'),
        telefono=token_data.get('telefono'),
        expires_at=token_data.get('exp')
    )


def _get_weekly_data(db: Session, usuario_id: int):
    """
    Obtiene datos agregados de los últimos 7 días para gráficos.

    Returns:
        Lista de datos por día: [{"day": "Lun", "mood": 7.5, "activities": 3}, ...]
    """
    # Calcular fecha de hace 7 días
    seven_days_ago = datetime.utcnow() - timedelta(days=7)

    # Nombres de días en español
    day_names = ['Lun', 'Mar', 'Mié', 'Jue', 'Vie', 'Sáb', 'Dom']

    # Inicializar estructura de datos para los últimos 7 días
    today = datetime.utcnow()
    weekly_data = {}

    for i in range(7):
        day = today - timedelta(days=6-i)  # Empezar desde hace 6 días
        day_key = day.strftime('%Y-%m-%d')
        weekday_index = day.weekday()

        weekly_data[day_key] = {
            'day': day_names[weekday_index],
            'mood': 0,
            'mood_count': 0,
            'activities': 0
        }

    # Obtener moods de los últimos 7 días
    moods = db.query(EstadoAnimo).filter(
        EstadoAnimo.usuario_id == usuario_id,
        EstadoAnimo.timestamp >= seven_days_ago
    ).all()

    # Agregar moods por día
    for mood in moods:
        day_key = mood.timestamp.strftime('%Y-%m-%d')
        if day_key in weekly_data:
            weekly_data[day_key]['mood'] += mood.nivel
            weekly_data[day_key]['mood_count'] += 1

    # Obtener actividades (registros de hábitos) de los últimos 7 días
    activities = db.query(RegistroHabito).filter(
        RegistroHabito.usuario_id == usuario_id,
        RegistroHabito.timestamp >= seven_days_ago,
        RegistroHabito.completado == True
    ).all()

    # Contar actividades por día
    for activity in activities:
        day_key = activity.timestamp.strftime('%Y-%m-%d')
        if day_key in weekly_data:
            weekly_data[day_key]['activities'] += 1

    # Convertir a lista y calcular promedios
    result = []
    for day_key in sorted(weekly_data.keys()):
        data = weekly_data[day_key]
        avg_mood = round(data['mood'] / data['mood_count'], 1) if data['mood_count'] > 0 else 0

        result.append({
            'day': data['day'],
            'mood': avg_mood,
            'activities': data['activities']
        })

    return result


@router.get("/me")
async def get_current_user(
    token: str,
    db: Session = Depends(get_db)
):
    """
    Obtiene información del usuario actual basado en el token.

    Args:
        token: Token JWT del usuario

    Returns:
        Información completa del usuario incluyendo moods, trust level y datos semanales para gráficos
    """
    token_data = auth_service.verify_token(token)

    if not token_data:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido o expirado"
        )

    usuario_id = token_data.get('usuario_id')
    usuario = crud.get_usuario(db, usuario_id=usuario_id)

    if not usuario:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuario no encontrado"
        )

    # Obtener estados de ánimo del usuario
    estados_animo = crud.get_estados_animo_by_usuario(db, usuario_id=usuario_id, limit=100)
    moods = [
        {
            "timestamp": estado.timestamp.isoformat() if estado.timestamp else None,
            "nivel": estado.nivel,
            "notas_texto": estado.notas_texto
        }
        for estado in estados_animo
    ]

    # Obtener información del nivel de confianza
    trust_info = trust_service.get_user_trust_info(db, usuario_id)

    # Obtener datos semanales para gráficos
    weekly_data = _get_weekly_data(db, usuario_id)

    return {
        "id": usuario.id,
        "nombre": usuario.nombre,
        "telefono": usuario.telefono,
        "fecha_registro": usuario.fecha_registro.isoformat() if usuario.fecha_registro else None,
        "nivel_CMV": usuario.nivel_CMV,
        "frecuencia_checkins": usuario.frecuencia_checkins,
        "moods": moods,
        "weekly_data": weekly_data,  # NUEVO: datos para gráficos
        "trust_level": trust_info if trust_info else {
            "nivel_confianza": 1,
            "total_interacciones": 0,
            "nivel_nombre": "Conociendo",
            "mensajes_hasta_siguiente_nivel": 10
        }
    }
