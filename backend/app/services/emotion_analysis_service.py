"""
Servicio de análisis emocional multidimensional para Loki.
Mapea emociones complejas, detecta ciclos emocionales y analiza patrones de recuperación.
"""

from typing import List, Dict, Optional, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import func, and_
from datetime import datetime, timedelta
import statistics
from collections import defaultdict
import json

from app.models.mood import EstadoAnimo, Usuario


class EmotionalAnalysisService:
    """
    Servicio para análisis profundo y multidimensional de emociones.
    Mapea relaciones complejas entre emociones y detecta patrones cíclicos.
    """

    def __init__(self):
        # Matriz de transiciones emocionales (qué emociones suelen seguirse)
        self.emotion_transitions = {
            'ansiedad': ['preocupación', 'estrés', 'miedo', 'irritabilidad'],
            'tristeza': ['apatía', 'soledad', 'culpa', 'desesperanza'],
            'enojo': ['frustración', 'resentimiento', 'culpa posterior'],
            'miedo': ['ansiedad', 'paranoia', 'parálisis'],
            'alegría': ['entusiasmo', 'gratitud', 'esperanza'],
            'calma': ['aceptación', 'claridad', 'paz'],
        }

        # Ciclos emocionales típicos
        self.emotional_cycles = {
            'diario': 24,  # 24 horas
            'semanal': 7,  # 7 días
            'menstrual': 28,  # 28 días (si aplica)
        }

    def map_primary_and_secondary_emotions(
        self,
        texto: str
    ) -> Dict:
        """
        Mapea emociones primarias y secundarias en el texto.
        Las emociones secundarias son matices o consecuencias de las primarias.

        Returns:
            {
                'primary': {'emoción': intensidad},
                'secondary': {'emoción': relación_con_primaria},
                'emotional_trajectory': str,
                'complexity_score': float (0-10)
            }
        """
        # Diccionarios de palabras clave
        primary_emotions = {
            'alegría': ['feliz', 'alegre', 'contento', 'genial', 'emocionado'],
            'tristeza': ['triste', 'deprimido', 'angustia', 'dolor', 'melancólico'],
            'miedo': ['miedo', 'aterrado', 'asustado', 'pánico', 'fobia'],
            'enojo': ['enojado', 'furioso', 'ira', 'rabia', 'irritado'],
            'sorpresa': ['sorprendido', 'asombrado', 'impactado', 'sorpresivo'],
            'asco': ['asco', 'repugnancia', 'repulsión', 'disgusto'],
        }

        secondary_emotions = {
            'ansiedad': ['ansioso', 'nervioso', 'preocupado', 'intranquilo'],
            'esperanza': ['esperanzado', 'optimista', 'ilusionado', 'confiado'],
            'culpa': ['culpa', 'culpable', 'arrepentido', 'avergonzado'],
            'soledad': ['solo', 'aislado', 'incomprendido', 'abandonado'],
            'frustración': ['frustrado', 'irritante', 'molesto', 'exasperado'],
            'gratitud': ['agradecido', 'valioso', 'apreciado', 'privilegiado'],
        }

        texto_lower = texto.lower()
        detected = {'primary': {}, 'secondary': {}}

        # Detectar emociones primarias
        for emotion, keywords in primary_emotions.items():
            count = sum(1 for keyword in keywords if keyword in texto_lower)
            if count > 0:
                detected['primary'][emotion] = count

        # Detectar emociones secundarias
        for emotion, keywords in secondary_emotions.items():
            count = sum(1 for keyword in keywords if keyword in texto_lower)
            if count > 0:
                detected['secondary'][emotion] = count

        # Calcular trayectoria emocional (cómo progresa la emoción en el texto)
        trajectory = self._calculate_emotional_trajectory(texto_lower, primary_emotions)

        # Calcular complejidad (cuántas emociones diferentes se mencionan)
        total_emotions = len(detected['primary']) + len(detected['secondary'])
        complexity_score = min(total_emotions * 1.5, 10.0)

        return {
            'primary_emotions': detected['primary'],
            'secondary_emotions': detected['secondary'],
            'emotional_trajectory': trajectory,
            'complexity_score': round(complexity_score, 1),
            'likely_secondary_chain': self._infer_secondary_chain(detected['primary'])
        }

    def _calculate_emotional_trajectory(
        self,
        texto_lower: str,
        emotions_dict: Dict
    ) -> str:
        """
        Analiza cómo cambia la emoción a lo largo del texto.
        Retorna: 'improving', 'deteriorating', 'volatile', 'stable'
        """
        # Dividir texto en tercios
        words = texto_lower.split()
        third_size = len(words) // 3

        tercio1 = ' '.join(words[:third_size])
        tercio2 = ' '.join(words[third_size:third_size*2])
        tercio3 = ' '.join(words[third_size*2:])

        score1 = sum(1 for keywords in emotions_dict.values() for k in keywords if k in tercio1)
        score2 = sum(1 for keywords in emotions_dict.values() for k in keywords if k in tercio2)
        score3 = sum(1 for keywords in emotions_dict.values() for k in keywords if k in tercio3)

        if score3 > score1:
            return 'deteriorating'
        elif score3 < score1:
            return 'improving'
        elif abs(score2 - score1) > 2 or abs(score3 - score2) > 2:
            return 'volatile'
        else:
            return 'stable'

    def _infer_secondary_chain(
        self,
        primary_emotions: Dict
    ) -> List[str]:
        """
        Infiere qué emociones secundarias probablemente acompañan a las primarias.
        """
        chains = []
        for emotion in primary_emotions.keys():
            if emotion in self.emotion_transitions:
                chains.extend(self.emotion_transitions[emotion])

        return list(set(chains))[:3]  # Top 3

    def detect_emotional_cycles(
        self,
        db: Session,
        usuario_id: int,
        days_lookback: int = 90
    ) -> Dict:
        """
        Detecta ciclos emocionales (patrones que se repiten en tiempo).
        Analiza: ciclos diarios, semanales, menstruales.

        Returns:
            {
                'daily_pattern': {...},
                'weekly_pattern': {...},
                'monthly_pattern': {...},
                'predominant_cycle': str,
                'next_low_mood_prediction': datetime
            }
        """
        cutoff_date = datetime.utcnow() - timedelta(days=days_lookback)

        moods = db.query(EstadoAnimo).filter(
            and_(
                EstadoAnimo.usuario_id == usuario_id,
                EstadoAnimo.timestamp >= cutoff_date
            )
        ).order_by(EstadoAnimo.timestamp).all()

        if len(moods) < 5:
            return {'error': 'Datos insuficientes para análisis cíclico'}

        # Analizar patrones por hora del día
        daily_pattern = self._analyze_daily_pattern(moods)

        # Analizar patrones por día de la semana
        weekly_pattern = self._analyze_weekly_pattern(moods)

        # Analizar patrones mensuales (si hay datos)
        monthly_pattern = self._analyze_monthly_pattern(moods) if len(moods) > 20 else None

        # Detectar ciclo predominante
        predominant = self._detect_predominant_cycle(daily_pattern, weekly_pattern, monthly_pattern)

        # Predecir próximo ánimo bajo
        next_low_prediction = self._predict_low_mood_time(moods, predominant)

        return {
            'daily_pattern': daily_pattern,
            'weekly_pattern': weekly_pattern,
            'monthly_pattern': monthly_pattern,
            'predominant_cycle': predominant,
            'next_low_mood_prediction': next_low_prediction
        }

    def _analyze_daily_pattern(self, moods: List[EstadoAnimo]) -> Dict:
        """Analiza patrón de ánimo por hora del día."""
        by_hour = defaultdict(list)

        for mood in moods:
            hour = mood.timestamp.hour
            by_hour[hour].append(mood.nivel)

        pattern = {}
        for hour in range(24):
            if hour in by_hour:
                pattern[f'{hour:02d}:00'] = {
                    'avg_mood': round(statistics.mean(by_hour[hour]), 1),
                    'count': len(by_hour[hour])
                }

        return pattern

    def _analyze_weekly_pattern(self, moods: List[EstadoAnimo]) -> Dict:
        """Analiza patrón de ánimo por día de la semana."""
        by_weekday = defaultdict(list)

        for mood in moods:
            weekday = mood.timestamp.weekday()
            by_weekday[weekday].append(mood.nivel)

        weekday_names = ['Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes', 'Sábado', 'Domingo']

        pattern = {}
        for day in range(7):
            if day in by_weekday:
                pattern[weekday_names[day]] = {
                    'avg_mood': round(statistics.mean(by_weekday[day]), 1),
                    'count': len(by_weekday[day])
                }

        return pattern

    def _analyze_monthly_pattern(self, moods: List[EstadoAnimo]) -> Dict:
        """Analiza patrón de ánimo por semana del mes."""
        by_week = defaultdict(list)

        for mood in moods:
            week_of_month = (mood.timestamp.day - 1) // 7 + 1
            by_week[week_of_month].append(mood.nivel)

        pattern = {}
        for week in range(1, 5):
            if week in by_week:
                pattern[f'Semana {week}'] = {
                    'avg_mood': round(statistics.mean(by_week[week]), 1),
                    'count': len(by_week[week])
                }

        return pattern

    def _detect_predominant_cycle(
        self,
        daily: Dict,
        weekly: Dict,
        monthly: Optional[Dict]
    ) -> str:
        """Detecta cuál es el ciclo más marcado."""
        # Calcular varianza en cada ciclo
        daily_moods = [v['avg_mood'] for v in daily.values() if 'avg_mood' in v]
        weekly_moods = [v['avg_mood'] for v in weekly.values() if 'avg_mood' in v]

        if not daily_moods or not weekly_moods:
            return 'unknown'

        daily_var = statistics.variance(daily_moods) if len(daily_moods) > 1 else 0
        weekly_var = statistics.variance(weekly_moods) if len(weekly_moods) > 1 else 0

        if monthly:
            monthly_moods = [v['avg_mood'] for v in monthly.values() if 'avg_mood' in v]
            monthly_var = statistics.variance(monthly_moods) if len(monthly_moods) > 1 else 0

            if monthly_var > daily_var and monthly_var > weekly_var:
                return 'monthly'

        if daily_var > weekly_var:
            return 'daily'
        else:
            return 'weekly'

    def _predict_low_mood_time(
        self,
        moods: List[EstadoAnimo],
        predominant_cycle: str
    ) -> Optional[datetime]:
        """Predice cuándo será el próximo período de bajo ánimo."""
        if not moods or predominant_cycle == 'unknown':
            return None

        # Encontrar ánimos bajos pasados
        low_moods = [m for m in moods if m.nivel <= 4]

        if not low_moods:
            return None

        # Calcular intervalo promedio entre ánimos bajos
        if len(low_moods) >= 2:
            intervals = []
            for i in range(len(low_moods) - 1):
                interval = (low_moods[i + 1].timestamp - low_moods[i].timestamp).days
                if interval > 0:
                    intervals.append(interval)

            if intervals:
                avg_interval = statistics.mean(intervals)
                last_low = low_moods[-1].timestamp
                next_prediction = last_low + timedelta(days=avg_interval)
                return next_prediction

        return None

    def identify_causal_relationships(
        self,
        db: Session,
        usuario_id: int,
        days_lookback: int = 30
    ) -> List[Dict]:
        """
        Identifica relaciones causales entre eventos mencionados y cambios emocionales.

        Returns:
            [{'evento': str, 'efecto_emocional': str, 'impacto': float, 'confianza': float}]
        """
        cutoff_date = datetime.utcnow() - timedelta(days=days_lookback)

        moods = db.query(EstadoAnimo).filter(
            and_(
                EstadoAnimo.usuario_id == usuario_id,
                EstadoAnimo.timestamp >= cutoff_date
            )
        ).order_by(EstadoAnimo.timestamp).all()

        if len(moods) < 5:
            return []

        causalities = []

        # Patrones de eventos y sus efectos
        event_patterns = {
            'trabajo': {'keywords': ['trabajo', 'jefe', 'proyecto'], 'typical_effect': 'estrés'},
            'ejercicio': {'keywords': ['ejercicio', 'gym', 'correr'], 'typical_effect': 'mejora'},
            'sueño': {'keywords': ['dormir', 'sueño', 'descanso'], 'typical_effect': 'mejora'},
            'relación': {'keywords': ['pareja', 'pelea', 'discusión'], 'typical_effect': 'variado'},
            'socialización': {'keywords': ['amigos', 'salir', 'reunión'], 'typical_effect': 'mejora'},
        }

        for i in range(len(moods) - 1):
            current_mood = moods[i]
            next_mood = moods[i + 1]
            mood_change = next_mood.nivel - current_mood.nivel

            # Buscar eventos mencionados
            texto = (current_mood.notas_texto or '').lower()

            for event, data in event_patterns.items():
                for keyword in data['keywords']:
                    if keyword in texto:
                        # Calcular confianza basada en consistencia
                        confidence = 0.5  # Base

                        if mood_change > 0 and data['typical_effect'] == 'mejora':
                            confidence = 0.8
                        elif mood_change < 0 and data['typical_effect'] != 'mejora':
                            confidence = 0.7
                        elif data['typical_effect'] == 'variado':
                            confidence = 0.5

                        causalities.append({
                            'evento': event,
                            'efecto_emocional': 'positivo' if mood_change > 0 else 'negativo' if mood_change < 0 else 'neutral',
                            'cambio_mood': mood_change,
                            'impacto': abs(mood_change) / 10.0,
                            'confianza': confidence
                        })
                        break

        # Agrupar y promediar
        event_summary = defaultdict(list)
        for causal in causalities:
            key = f"{causal['evento']}-{causal['efecto_emocional']}"
            event_summary[key].append(causal)

        # Consolidar
        consolidated = []
        for key, items in event_summary.items():
            avg_impacto = statistics.mean([i['impacto'] for i in items])
            avg_confianza = statistics.mean([i['confianza'] for i in items])

            evento, efecto = key.rsplit('-', 1)
            consolidated.append({
                'evento': evento,
                'efecto_emocional': efecto,
                'impacto': round(avg_impacto, 2),
                'confianza': round(avg_confianza, 2),
                'occurrencias': len(items)
            })

        consolidated.sort(key=lambda x: x['confianza'] * x['impacto'], reverse=True)
        return consolidated[:5]

    def analyze_resilience(
        self,
        db: Session,
        usuario_id: int,
        days_lookback: int = 60
    ) -> Dict:
        """
        Analiza la capacidad de recuperación del usuario ante momentos bajos.
        Mide tiempo de recuperación, patrones de recuperación exitosa, etc.

        Returns:
            {
                'avg_recovery_time': timedelta,
                'recovery_success_rate': float (0-1),
                'fastest_recovery': timedelta,
                'slowest_recovery': timedelta,
                'recovery_strategies': [str],
                'resilience_score': float (0-10)
            }
        """
        cutoff_date = datetime.utcnow() - timedelta(days=days_lookback)

        moods = db.query(EstadoAnimo).filter(
            and_(
                EstadoAnimo.usuario_id == usuario_id,
                EstadoAnimo.timestamp >= cutoff_date
            )
        ).order_by(EstadoAnimo.timestamp).all()

        if len(moods) < 5:
            return {'error': 'Datos insuficientes para análisis de resiliencia'}

        # Encontrar períodos de "crisis" (ánimos bajos < 4) y su recuperación
        low_mood_periods = []
        in_crisis = False
        crisis_start = None

        for mood in moods:
            if mood.nivel <= 4 and not in_crisis:
                in_crisis = True
                crisis_start = mood
            elif mood.nivel > 6 and in_crisis:
                in_crisis = False
                recovery_time = mood.timestamp - crisis_start.timestamp
                low_mood_periods.append({
                    'start': crisis_start.timestamp,
                    'recovery': recovery_time,
                    'final_mood': mood.nivel
                })

        if not low_mood_periods:
            return {'error': 'No hay períodos de bajo ánimo registrados'}

        recovery_times = [p['recovery'].total_seconds() for p in low_mood_periods]
        final_moods = [p['final_mood'] for p in low_mood_periods]

        avg_recovery = timedelta(seconds=statistics.mean(recovery_times))
        success_rate = sum(1 for m in final_moods if m >= 6) / len(final_moods)

        # Estrategias de recuperación (eventos que ocurren durante recuperación)
        recovery_strategies = self._identify_recovery_strategies(db, usuario_id, low_mood_periods)

        # Calcular score de resiliencia (0-10)
        resilience_score = min(10, (success_rate * 10) - (avg_recovery.total_seconds() / 86400))  # Penalizar por tiempo lento

        return {
            'avg_recovery_time': str(avg_recovery),
            'recovery_success_rate': round(success_rate, 2),
            'fastest_recovery': str(timedelta(seconds=min(recovery_times))),
            'slowest_recovery': str(timedelta(seconds=max(recovery_times))),
            'recovery_periods_analyzed': len(low_mood_periods),
            'recovery_strategies': recovery_strategies,
            'resilience_score': round(max(0, resilience_score), 1)
        }

    def _identify_recovery_strategies(
        self,
        db: Session,
        usuario_id: int,
        low_mood_periods: List[Dict]
    ) -> List[str]:
        """Identifica qué hábitos/actividades ayudan a la recuperación."""
        strategies = []

        from app.models.mood import RegistroHabito, Habito

        for period in low_mood_periods:
            # Buscar hábitos completados durante la recuperación
            recovery_start = period['start']
            recovery_end = recovery_start + timedelta(days=int(float(period['recovery'].total_seconds() / 86400)))

            habitos = db.query(RegistroHabito).filter(
                and_(
                    RegistroHabito.usuario_id == usuario_id,
                    RegistroHabito.timestamp >= recovery_start,
                    RegistroHabito.timestamp <= recovery_end,
                    RegistroHabito.completado == True
                )
            ).all()

            for registro in habitos:
                habito_name = registro.habito.nombre_habito if registro.habito else 'desconocido'
                if habito_name not in strategies:
                    strategies.append(habito_name)

        return strategies[:3]  # Top 3


# Instancia global del servicio
emotion_service = EmotionalAnalysisService()
