"""
Servicio para detectar y celebrar progresos del usuario.
Analiza tendencias de estado de ánimo y genera reconocimientos sutiles.

Características:
- Detecta mejorías en el mood promedio
- Identifica rachas positivas
- Reconoce superación de momentos difíciles
- Genera mensajes sutiles y naturales (no cursis)
"""

from typing import Optional, Dict, List
from datetime import datetime, timedelta
from dataclasses import dataclass
from sqlalchemy.orm import Session
from sqlalchemy import func, and_

from app.models.mood import EstadoAnimo
from app.core.logger import setup_logger

logger = setup_logger(__name__)


@dataclass
class ProgressInsight:
    """Representa un insight de progreso detectado."""
    tipo: str  # 'mejoria_promedio', 'racha_positiva', 'superacion_momento_dificil'
    mensaje_contexto: str  # Para incluir en el prompt del sistema
    datos: Dict  # Datos específicos del progreso
    nivel_significancia: int  # 1-10: qué tan importante es este progreso


class ProgressTrackerService:
    """
    Servicio para detectar progresos y generar reconocimientos.
    """
    
    def __init__(self):
        self.MOOD_THRESHOLD_POSITIVE = 7  # Mood >= 7 se considera positivo
        self.MOOD_THRESHOLD_NEGATIVE = 4  # Mood <= 4 se considera negativo
        self.MIN_RACHA_DIAS = 3  # Mínimo de días para considerar una racha
        self.VENTANA_COMPARACION_DIAS = 14  # Comparar últimos 7 días vs 7 anteriores
    
    def get_progress_insights(
        self,
        db: Session,
        usuario_id: int,
        incluir_en_prompt: bool = True
    ) -> Optional[ProgressInsight]:
        """
        Obtiene el insight de progreso más relevante para el usuario.
        
        Args:
            db: Sesión de base de datos
            usuario_id: ID del usuario
            incluir_en_prompt: Si True, genera mensaje para el prompt del sistema
        
        Returns:
            ProgressInsight si se detecta algún progreso significativo, None si no
        """
        try:
            # Detectar diferentes tipos de progreso
            mejoria = self._detect_mood_improvement(db, usuario_id)
            racha = self._detect_positive_streak(db, usuario_id)
            superacion = self._detect_overcome_difficulty(db, usuario_id)
            
            # Priorizar el más significativo
            insights = []
            
            if mejoria:
                insights.append(mejoria)
            
            if racha:
                insights.append(racha)
            
            if superacion:
                insights.append(superacion)
            
            if not insights:
                return None
            
            # Retornar el de mayor significancia
            insight_principal = max(insights, key=lambda x: x.nivel_significancia)
            
            logger.info(f"📈 Progreso detectado para usuario {usuario_id}: {insight_principal.tipo}")
            
            return insight_principal
        
        except Exception as e:
            logger.error(f"⚠️ Error detectando progresos: {e}")
            return None
    
    def _detect_mood_improvement(
        self,
        db: Session,
        usuario_id: int
    ) -> Optional[ProgressInsight]:
        """
        Detecta si ha mejorado el mood promedio comparando períodos.
        """
        try:
            ahora = datetime.utcnow()
            medio_periodo = ahora - timedelta(days=self.VENTANA_COMPARACION_DIAS // 2)
            inicio_periodo = ahora - timedelta(days=self.VENTANA_COMPARACION_DIAS)
            
            # Mood promedio de la primera mitad del período
            mood_anterior = db.query(func.avg(EstadoAnimo.nivel)).filter(
                and_(
                    EstadoAnimo.usuario_id == usuario_id,
                    EstadoAnimo.timestamp >= inicio_periodo,
                    EstadoAnimo.timestamp < medio_periodo
                )
            ).scalar()
            
            # Mood promedio de la segunda mitad (reciente)
            mood_reciente = db.query(func.avg(EstadoAnimo.nivel)).filter(
                and_(
                    EstadoAnimo.usuario_id == usuario_id,
                    EstadoAnimo.timestamp >= medio_periodo,
                    EstadoAnimo.timestamp <= ahora
                )
            ).scalar()
            
            if mood_anterior is None or mood_reciente is None:
                return None
            
            # Calcular mejora
            mejora = round(mood_reciente - mood_anterior, 1)
            
            # Solo considerar mejorías significativas (>= 1 punto)
            if mejora >= 1.0:
                # Calcular nivel de significancia (1-10)
                # Mejora de 1 = nivel 5, mejora de 3+ = nivel 10
                nivel_significancia = min(10, int(5 + (mejora * 2)))
                
                dias = self.VENTANA_COMPARACION_DIAS // 2
                mensaje = (
                    f"Noto que en los últimos {dias} días tu ánimo promedio ha sido "
                    f"{mood_reciente:.1f}, comparado con {mood_anterior:.1f} en la semana anterior. "
                    f"Es una mejora de {mejora} puntos."
                )
                
                return ProgressInsight(
                    tipo='mejoria_promedio',
                    mensaje_contexto=mensaje,
                    datos={
                        'mood_anterior': float(mood_anterior),
                        'mood_reciente': float(mood_reciente),
                        'mejora': float(mejora),
                        'dias_comparados': dias
                    },
                    nivel_significancia=nivel_significancia
                )
            
            return None
        
        except Exception as e:
            logger.error(f"⚠️ Error detectando mejora de mood: {e}")
            return None
    
    def _detect_positive_streak(
        self,
        db: Session,
        usuario_id: int
    ) -> Optional[ProgressInsight]:
        """
        Detecta rachas de días consecutivos con mood positivo.
        """
        try:
            # Obtener últimos 14 días de moods
            hace_14_dias = datetime.utcnow() - timedelta(days=14)
            
            moods = db.query(EstadoAnimo).filter(
                and_(
                    EstadoAnimo.usuario_id == usuario_id,
                    EstadoAnimo.timestamp >= hace_14_dias
                )
            ).order_by(EstadoAnimo.timestamp.desc()).all()
            
            if not moods:
                return None
            
            # Agrupar por día (tomar el promedio del día)
            moods_por_dia = {}
            for mood in moods:
                dia = mood.timestamp.date()
                if dia not in moods_por_dia:
                    moods_por_dia[dia] = []
                moods_por_dia[dia].append(mood.nivel)
            
            # Calcular promedio por día
            dias_ordenados = sorted(moods_por_dia.keys(), reverse=True)
            promedios_dias = [
                sum(moods_por_dia[dia]) / len(moods_por_dia[dia])
                for dia in dias_ordenados
            ]
            
            # Detectar racha actual (desde el día más reciente hacia atrás)
            racha_actual = 0
            for promedio in promedios_dias:
                if promedio >= self.MOOD_THRESHOLD_POSITIVE:
                    racha_actual += 1
                else:
                    break
            
            # Solo celebrar rachas significativas
            if racha_actual >= self.MIN_RACHA_DIAS:
                # Nivel de significancia: 3 días = 6, 5+ días = 10
                nivel_significancia = min(10, 4 + racha_actual)
                
                mensaje = (
                    f"Llevas {racha_actual} días consecutivos con un estado de ánimo "
                    f"positivo (≥{self.MOOD_THRESHOLD_POSITIVE}/10)."
                )
                
                return ProgressInsight(
                    tipo='racha_positiva',
                    mensaje_contexto=mensaje,
                    datos={
                        'dias_racha': racha_actual,
                        'threshold': self.MOOD_THRESHOLD_POSITIVE,
                        'promedio_racha': sum(promedios_dias[:racha_actual]) / racha_actual
                    },
                    nivel_significancia=nivel_significancia
                )
            
            return None
        
        except Exception as e:
            logger.error(f"⚠️ Error detectando racha positiva: {e}")
            return None
    
    def _detect_overcome_difficulty(
        self,
        db: Session,
        usuario_id: int
    ) -> Optional[ProgressInsight]:
        """
        Detecta si el usuario ha superado un momento difícil reciente.
        Busca un patrón de: bajo → mejorando → alto
        """
        try:
            # Obtener últimos 10 días de moods
            hace_10_dias = datetime.utcnow() - timedelta(days=10)
            
            moods = db.query(EstadoAnimo).filter(
                and_(
                    EstadoAnimo.usuario_id == usuario_id,
                    EstadoAnimo.timestamp >= hace_10_dias
                )
            ).order_by(EstadoAnimo.timestamp.asc()).all()
            
            if len(moods) < 6:  # Necesitamos datos suficientes
                return None
            
            # Dividir en 3 períodos
            tercio = len(moods) // 3
            periodo_1 = moods[:tercio]  # Antiguo
            periodo_2 = moods[tercio:tercio*2]  # Medio
            periodo_3 = moods[tercio*2:]  # Reciente
            
            avg_1 = sum(m.nivel for m in periodo_1) / len(periodo_1)
            avg_2 = sum(m.nivel for m in periodo_2) / len(periodo_2)
            avg_3 = sum(m.nivel for m in periodo_3) / len(periodo_3)
            
            # Patrón de superación: bajo → medio → alto
            # Período 1 debe ser bajo (<=4), Período 3 debe ser alto (>=7)
            if (avg_1 <= self.MOOD_THRESHOLD_NEGATIVE and 
                avg_3 >= self.MOOD_THRESHOLD_POSITIVE and
                avg_2 > avg_1 and avg_3 > avg_2):
                
                mejora_total = avg_3 - avg_1
                
                # Nivel de significancia basado en la magnitud de la recuperación
                nivel_significancia = min(10, int(mejora_total * 2))
                
                mensaje = (
                    f"Has pasado de un período con mood promedio de {avg_1:.1f} "
                    f"a {avg_3:.1f}. Es una recuperación notable."
                )
                
                return ProgressInsight(
                    tipo='superacion_momento_dificil',
                    mensaje_contexto=mensaje,
                    datos={
                        'mood_inicial': round(avg_1, 1),
                        'mood_intermedio': round(avg_2, 1),
                        'mood_actual': round(avg_3, 1),
                        'mejora_total': round(mejora_total, 1)
                    },
                    nivel_significancia=nivel_significancia
                )
            
            return None
        
        except Exception as e:
            logger.error(f"⚠️ Error detectando superación: {e}")
            return None
    
    def generate_celebration_context(
        self,
        insight: ProgressInsight,
        nivel_confianza: int
    ) -> str:
        """
        Genera un contexto de celebración sutil para el prompt del sistema.
        Adapta el tono según el nivel de confianza.
        
        Args:
            insight: El insight de progreso detectado
            nivel_confianza: Nivel de confianza del usuario (1-5)
        
        Returns:
            String para agregar al prompt del sistema
        """
        # Mensajes según tipo y nivel de confianza
        if insight.tipo == 'mejoria_promedio':
            if nivel_confianza <= 2:
                # Nivel bajo: muy sutil
                base = f"Nota: {insight.mensaje_contexto}"
            else:
                # Nivel alto: más directo
                base = (
                    f"PROGRESO DETECTADO: {insight.mensaje_contexto}\n"
                    f"Puedes mencionarlo de forma natural si es relevante, "
                    f"pero no fuerces la conversación hacia eso."
                )
        
        elif insight.tipo == 'racha_positiva':
            dias = insight.datos['dias_racha']
            if nivel_confianza <= 2:
                base = f"Nota: El usuario lleva {dias} días con buen ánimo."
            else:
                base = (
                    f"RACHA POSITIVA: {insight.mensaje_contexto}\n"
                    f"Si es relevante, puedes reconocerlo con algo casual como: "
                    f"'Oye, llevas {dias} días de buen ánimo' (sin ser efusivo)."
                )
        
        elif insight.tipo == 'superacion_momento_dificil':
            if nivel_confianza <= 2:
                base = f"Nota: {insight.mensaje_contexto}"
            else:
                mejora = insight.datos['mejora_total']
                base = (
                    f"SUPERACIÓN DETECTADA: {insight.mensaje_contexto}\n"
                    f"El usuario ha mejorado {mejora} puntos desde un momento difícil. "
                    f"Puedes reconocerlo de forma sutil si surge naturalmente."
                )
        else:
            base = f"Progreso detectado: {insight.mensaje_contexto}"
        
        # IMPORTANTE: Instrucción para evitar cursilería
        footer = (
            "\n\n⚠️ IMPORTANTE sobre el progreso:\n"
            "- NO uses frases como 'estoy orgulloso', 'eres increíble', 'qué logro'\n"
            "- SÍ usa tono casual: 'noto que...', 'veo que...', 'llevas X días...'\n"
            "- NO hagas todo sobre el progreso, solo menciónalo si es relevante\n"
            "- Sé genuino, no motivador de autoayuda"
        )
        
        return base + footer


# Singleton
progress_tracker_service = ProgressTrackerService()
