"""
Servicio de análisis de patrones personales para Loki.
Permite detectar correlaciones entre hábitos y estados de ánimo,
generando insights personalizados para cada usuario.
"""
from typing import List, Dict, Optional, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import func, and_
import datetime
from collections import defaultdict
import statistics

from app.models.mood import (
    Usuario, EstadoAnimo, Habito, RegistroHabito, 
    Correlacion, ConversacionContexto
)


class PatternAnalysisService:
    """
    Servicio para analizar patrones personales y generar insights.
    """
    
    def __init__(self):
        self.min_data_points = 5  # Mínimo de datos para análisis confiable
        self.correlation_threshold = 0.3  # Correlación mínima significativa
    
    def analyze_user_patterns(
        self, 
        db: Session, 
        usuario_id: int,
        days_lookback: int = 30
    ) -> Dict:
        """
        Analiza patrones del usuario en los últimos N días.
        Retorna insights accionables.
        """
        # 1. Obtener estados de ánimo recientes
        cutoff_date = datetime.datetime.utcnow() - datetime.timedelta(days=days_lookback)
        
        mood_states = db.query(EstadoAnimo).filter(
            and_(
                EstadoAnimo.usuario_id == usuario_id,
                EstadoAnimo.timestamp >= cutoff_date
            )
        ).order_by(EstadoAnimo.timestamp).all()
        
        if len(mood_states) < self.min_data_points:
            return {
                'has_enough_data': False,
                'message': 'Necesitamos más datos para encontrar patrones significativos.',
                'data_points': len(mood_states),
                'min_required': self.min_data_points
            }
        
        # 2. Analizar correlaciones con hábitos
        correlations = self._analyze_habit_mood_correlations(db, usuario_id, cutoff_date)
        
        # 3. Detectar tendencias temporales
        temporal_patterns = self._analyze_temporal_patterns(mood_states)
        
        # 4. Identificar disparadores emocionales
        emotional_triggers = self._identify_emotional_triggers(db, usuario_id, cutoff_date)
        
        # 5. Generar insights accionables
        insights = self._generate_actionable_insights(
            correlations, 
            temporal_patterns, 
            emotional_triggers
        )
        
        return {
            'has_enough_data': True,
            'data_points': len(mood_states),
            'average_mood': statistics.mean([m.nivel for m in mood_states]),
            'mood_stability': statistics.stdev([m.nivel for m in mood_states]) if len(mood_states) > 1 else 0,
            'correlations': correlations,
            'temporal_patterns': temporal_patterns,
            'emotional_triggers': emotional_triggers,
            'insights': insights
        }
    
    def _analyze_habit_mood_correlations(
        self, 
        db: Session, 
        usuario_id: int, 
        cutoff_date: datetime.datetime
    ) -> List[Dict]:
        """
        Calcula correlaciones entre hábitos y estados de ánimo.
        """
        # Obtener todos los hábitos del usuario
        habitos = db.query(Habito).filter(
            Habito.usuario_id == usuario_id,
            Habito.activo == True
        ).all()
        
        correlations = []
        
        for habito in habitos:
            # Obtener registros del hábito
            registros = db.query(RegistroHabito).filter(
                and_(
                    RegistroHabito.habito_id == habito.id,
                    RegistroHabito.timestamp >= cutoff_date,
                    RegistroHabito.completado == True
                )
            ).all()
            
            if len(registros) < self.min_data_points:
                continue
            
            # Comparar ánimo en días con hábito vs días sin hábito
            mood_with_habit = []
            mood_without_habit = []
            
            # Obtener todos los días en el rango
            all_moods = db.query(EstadoAnimo).filter(
                and_(
                    EstadoAnimo.usuario_id == usuario_id,
                    EstadoAnimo.timestamp >= cutoff_date
                )
            ).all()
            
            # Agrupar por fecha
            habit_dates = {r.timestamp.date() for r in registros}
            
            for mood in all_moods:
                mood_date = mood.timestamp.date()
                if mood_date in habit_dates:
                    mood_with_habit.append(mood.nivel)
                else:
                    mood_without_habit.append(mood.nivel)
            
            if mood_with_habit and mood_without_habit:
                avg_with = statistics.mean(mood_with_habit)
                avg_without = statistics.mean(mood_without_habit)
                
                # Calcular diferencia normalizada (impacto)
                impact = (avg_with - avg_without) / 10.0  # Normalizar a -1 a 1
                
                # Calcular confianza basada en cantidad de datos
                confidence = min(
                    1.0, 
                    (len(mood_with_habit) + len(mood_without_habit)) / 20.0
                )
                
                if abs(impact) >= self.correlation_threshold:
                    correlations.append({
                        'habit': habito.nombre_habito,
                        'habit_id': habito.id,
                        'category': habito.categoria,
                        'impact': round(impact, 3),
                        'confidence': round(confidence, 2),
                        'avg_mood_with': round(avg_with, 1),
                        'avg_mood_without': round(avg_without, 1),
                        'occurrences': len(mood_with_habit),
                        'interpretation': self._interpret_correlation(impact, habito.nombre_habito)
                    })
        
        # Ordenar por impacto absoluto (más significativos primero)
        correlations.sort(key=lambda x: abs(x['impact']), reverse=True)
        
        # Guardar correlaciones en BD para uso futuro
        self._save_correlations_to_db(db, usuario_id, correlations)
        
        return correlations
    
    def _analyze_temporal_patterns(self, mood_states: List[EstadoAnimo]) -> Dict:
        """
        Analiza patrones temporales (hora del día, día de la semana).
        """
        if not mood_states:
            return {}
        
        # Agrupar por día de la semana
        by_weekday = defaultdict(list)
        for mood in mood_states:
            weekday = mood.timestamp.weekday()  # 0=Lunes, 6=Domingo
            by_weekday[weekday].append(mood.nivel)
        
        weekday_patterns = {}
        weekday_names = ['Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes', 'Sábado', 'Domingo']
        
        for day, moods in by_weekday.items():
            if len(moods) >= 2:
                weekday_patterns[weekday_names[day]] = {
                    'avg_mood': round(statistics.mean(moods), 1),
                    'count': len(moods)
                }
        
        # Encontrar mejor y peor día
        if weekday_patterns:
            best_day = max(weekday_patterns.items(), key=lambda x: x[1]['avg_mood'])
            worst_day = min(weekday_patterns.items(), key=lambda x: x[1]['avg_mood'])
            
            return {
                'by_weekday': weekday_patterns,
                'best_day': best_day[0],
                'worst_day': worst_day[0],
                'best_day_avg': best_day[1]['avg_mood'],
                'worst_day_avg': worst_day[1]['avg_mood']
            }
        
        return {}
    
    def _identify_emotional_triggers(
        self, 
        db: Session, 
        usuario_id: int, 
        cutoff_date: datetime.datetime
    ) -> List[Dict]:
        """
        Identifica palabras/temas recurrentes en momentos de bajo ánimo.
        """
        # Obtener conversaciones con estados de ánimo bajos (<=4)
        low_mood_states = db.query(EstadoAnimo).filter(
            and_(
                EstadoAnimo.usuario_id == usuario_id,
                EstadoAnimo.timestamp >= cutoff_date,
                EstadoAnimo.nivel <= 4
            )
        ).all()
        
        if not low_mood_states:
            return []
        
        # Analizar notas y contexto de esos momentos
        triggers = defaultdict(int)
        trigger_keywords = {
            'trabajo': ['trabajo', 'jefe', 'proyecto', 'reunión', 'laboral'],
            'relaciones': ['pareja', 'familia', 'amigo', 'pelea', 'discusión'],
            'salud': ['cansado', 'enfermo', 'dolor', 'medicamento'],
            'estrés': ['estrés', 'presión', 'ansiedad', 'agobio', 'desbordado'],
            'soledad': ['solo', 'soledad', 'aislado', 'nadie']
        }
        
        for mood in low_mood_states:
            text = (mood.notas_texto or '') + ' ' + (mood.disparadores_detectados or '')
            text_lower = text.lower()
            
            for category, keywords in trigger_keywords.items():
                if any(keyword in text_lower for keyword in keywords):
                    triggers[category] += 1
        
        # Convertir a lista ordenada
        trigger_list = [
            {'trigger': k, 'occurrences': v, 'percentage': round(v/len(low_mood_states)*100, 1)}
            for k, v in triggers.items()
        ]
        trigger_list.sort(key=lambda x: x['occurrences'], reverse=True)
        
        return trigger_list
    
    def _generate_actionable_insights(
        self, 
        correlations: List[Dict], 
        temporal_patterns: Dict,
        emotional_triggers: List[Dict]
    ) -> List[str]:
        """
        Genera insights en lenguaje natural que Loki puede usar.
        """
        insights = []
        
        # Insights de hábitos
        if correlations:
            top_positive = [c for c in correlations if c['impact'] > 0]
            top_negative = [c for c in correlations if c['impact'] < 0]
            
            if top_positive:
                best = top_positive[0]
                insights.append(
                    f"He notado que cuando hacés {best['habit']}, tu ánimo promedio "
                    f"es {best['avg_mood_with']}/10, comparado con {best['avg_mood_without']}/10 "
                    f"cuando no lo hacés. Esto ha pasado en {best['occurrences']} ocasiones."
                )
            
            if top_negative:
                worst = top_negative[0]
                insights.append(
                    f"Parece que {worst['habit']} se asocia con un ánimo más bajo "
                    f"({worst['avg_mood_with']}/10 vs {worst['avg_mood_without']}/10). "
                    f"¿Querés explorar esto?"
                )
        
        # Insights temporales
        if temporal_patterns.get('best_day') and temporal_patterns.get('worst_day'):
            insights.append(
                f"Tus {temporal_patterns['best_day']} suelen ser mejores "
                f"(promedio {temporal_patterns['best_day_avg']}/10) que tus "
                f"{temporal_patterns['worst_day']} ({temporal_patterns['worst_day_avg']}/10)."
            )
        
        # Insights de disparadores
        if emotional_triggers:
            top_trigger = emotional_triggers[0]
            insights.append(
                f"En momentos de bajo ánimo, {top_trigger['trigger']} aparece "
                f"frecuentemente ({top_trigger['percentage']}% de las veces)."
            )
        
        return insights
    
    def _interpret_correlation(self, impact: float, habit_name: str) -> str:
        """
        Interpreta la correlación en lenguaje natural.
        """
        if impact > 0.5:
            return f"{habit_name} tiene un impacto MUY POSITIVO en tu ánimo"
        elif impact > 0.3:
            return f"{habit_name} tiene un impacto POSITIVO en tu ánimo"
        elif impact < -0.5:
            return f"{habit_name} parece afectar NEGATIVAMENTE tu ánimo"
        elif impact < -0.3:
            return f"{habit_name} podría estar afectando tu ánimo negativamente"
        else:
            return f"{habit_name} tiene un impacto neutral"
    
    def _save_correlations_to_db(
        self, 
        db: Session, 
        usuario_id: int, 
        correlations: List[Dict]
    ):
        """
        Guarda o actualiza correlaciones en la base de datos.
        """
        for corr in correlations:
            # Buscar si ya existe
            existing = db.query(Correlacion).filter(
                and_(
                    Correlacion.usuario_id == usuario_id,
                    Correlacion.factor == corr['habit']
                )
            ).first()
            
            if existing:
                # Actualizar
                existing.impacto_animo = corr['impact']
                existing.confianza_estadistica = corr['confidence']
                existing.num_datos = corr['occurrences']
                existing.fecha_calculo = datetime.datetime.utcnow()
            else:
                # Crear nueva
                nueva_corr = Correlacion(
                    usuario_id=usuario_id,
                    factor=corr['habit'],
                    impacto_animo=corr['impact'],
                    confianza_estadistica=corr['confidence'],
                    num_datos=corr['occurrences'],
                    fecha_calculo=datetime.datetime.utcnow()
                )
                db.add(nueva_corr)
        
        db.commit()
    
    def get_relevant_insights_for_conversation(
        self, 
        db: Session, 
        usuario_id: int,
        current_mood: Optional[int] = None
    ) -> str:
        """
        Obtiene insights relevantes para incluir en la conversación actual.
        """
        # Obtener análisis reciente
        patterns = self.analyze_user_patterns(db, usuario_id, days_lookback=30)
        
        if not patterns.get('has_enough_data'):
            return ""
        
        insights = patterns.get('insights', [])
        
        if not insights:
            return ""
        
        # Si el ánimo es bajo, sugerir hábitos positivos
        if current_mood and current_mood <= 4:
            positive_habits = [
                c for c in patterns.get('correlations', []) 
                if c['impact'] > 0.3
            ]
            
            if positive_habits:
                best_habit = positive_habits[0]
                return (
                    f"💡 Según tus datos, cuando hacés {best_habit['habit']}, "
                    f"tu ánimo suele mejorar a {best_habit['avg_mood_with']}/10. "
                    f"¿Probaste con eso hoy?"
                )
        
        # Retornar el insight más relevante
        return f"💡 {insights[0]}" if insights else ""


# Instancia global del servicio
pattern_service = PatternAnalysisService()
