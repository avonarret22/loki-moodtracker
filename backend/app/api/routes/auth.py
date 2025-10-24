"""
Endpoints de autenticación para acceso al dashboard.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app.db.session import get_db
from app.services.auth_service import auth_service
from app.db import crud

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
        Información completa del usuario
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
    
    return {
        "id": usuario.id,
        "nombre": usuario.nombre,
        "telefono": usuario.telefono,
        "fecha_registro": usuario.fecha_registro,
        "nivel_CMV": usuario.nivel_CMV,
        "frecuencia_checkins": usuario.frecuencia_checkins
    }
