"""
Endpoints para análisis de patrones y correlaciones personales.
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional

from app.db.session import get_db
from app import crud
from app.services.pattern_analysis import pattern_service

router = APIRouter()


@router.get("/analyze/{usuario_id}")
async def analyze_user_patterns(
    usuario_id: int,
    days: int = Query(default=30, ge=7, le=90, description="Días hacia atrás para analizar"),
    db: Session = Depends(get_db)
):
    """
    Analiza patrones del usuario en los últimos N días.
    Retorna correlaciones entre hábitos y ánimo, patrones temporales, etc.
    """
    # Verificar que el usuario existe
    usuario = crud.get_usuario(db, usuario_id=usuario_id)
    if not usuario:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    
    # Realizar análisis
    analysis = pattern_service.analyze_user_patterns(db, usuario_id, days_lookback=days)
    
    return {
        "usuario": usuario.nombre,
        "periodo_analizado_dias": days,
        "analisis": analysis
    }


@router.get("/insights/{usuario_id}")
async def get_user_insights(
    usuario_id: int,
    current_mood: Optional[int] = Query(default=None, ge=1, le=10),
    db: Session = Depends(get_db)
):
    """
    Obtiene insights relevantes para el usuario actual.
    Si se proporciona current_mood, personaliza las recomendaciones.
    """
    # Verificar que el usuario existe
    usuario = crud.get_usuario(db, usuario_id=usuario_id)
    if not usuario:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    
    # Obtener insight conversacional
    insight = pattern_service.get_relevant_insights_for_conversation(
        db, usuario_id, current_mood=current_mood
    )
    
    # Obtener análisis completo
    full_analysis = pattern_service.analyze_user_patterns(db, usuario_id, days_lookback=30)
    
    return {
        "usuario": usuario.nombre,
        "insight_conversacional": insight,
        "tiene_datos_suficientes": full_analysis.get('has_enough_data', False),
        "correlaciones_significativas": full_analysis.get('correlations', [])[:3],  # Top 3
        "insights_generales": full_analysis.get('insights', [])
    }


@router.get("/correlations/{usuario_id}")
async def get_saved_correlations(usuario_id: int, db: Session = Depends(get_db)):
    """
    Obtiene las correlaciones guardadas en la base de datos.
    """
    # Verificar que el usuario existe
    usuario = crud.get_usuario(db, usuario_id=usuario_id)
    if not usuario:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    
    # Obtener correlaciones de la BD
    correlaciones = db.query(crud.Correlacion).filter(
        crud.Correlacion.usuario_id == usuario_id
    ).order_by(crud.Correlacion.impacto_animo.desc()).all()
    
    return {
        "usuario": usuario.nombre,
        "total_correlaciones": len(correlaciones),
        "correlaciones": [
            {
                "factor": corr.factor,
                "impacto": round(corr.impacto_animo, 3),
                "confianza": round(corr.confianza_estadistica, 2),
                "num_datos": corr.num_datos,
                "fecha_calculo": corr.fecha_calculo
            }
            for corr in correlaciones
        ]
    }
