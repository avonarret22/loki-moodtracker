"""
Servicio de recomendaciones proactivas para Loki.
Sugiere actividades y hábitos basados en patrones personales.
"""

from typing import List, Dict, Optional
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
import json
import random

from app.models.mood import Usuario, EstadoAnimo, Habito, RegistroHabito
from app.services.pattern_analysis import pattern_service
from app.services.emotion_analysis_service import emotion_service


class ProactiveRecommendationService:
    """
    Servicio para generar recomendaciones proactivas e inteligentes.
    Basadas en patrones, patrones cíclicos y hábitos efectivos.
    """

    def __init__(self):
        # Banco de recomendaciones genéricas
        self.recommendation_templates = {
            'ejercicio': [
                'Una caminata corta puede ayudarte a despejar la mente',
                'El movimiento físico suele mejorar tu ánimo',
                'Un poco de ejercicio puede ser exactamente lo que necesitas ahora',
            ],
            'sueño': [
                'Parece que necesitas descanso. ¿Qué tal relajarte un poco?',
                'Un buen descanso puede cambiar tu perspectiva',
                'Tu cuerpo podría estar pidiendo más sueño',
            ],
            'social': [
                'Conectar con alguien podría levantarte el ánimo',
                'A veces el apoyo de otros es lo que necesitamos',
                'Estar acompañado suele ayudar en momentos como este',
            ],
            'meditación': [
                'Un momento de calma podría ayudarte',
                'La meditación o respiración consciente puede ser reconfortante',
                'Tomarte unos minutos para respirar profundamente podría ayudar',
            ],
            'creatividad': [
                'Expresarte de forma creativa podría ser catártico',
                'Un poco de música o arte podría cambiar tu estado de ánimo',
                'La creatividad es una excelente forma de procesar emociones',
            ],
        }

        self.micro_habits_templates = {
            'nivel_bajo': [
                'Bebe agua y tómate 5 minutos de pausa',
                'Abre una ventana y respira aire fresco',
                'Estira tu cuerpo durante 2 minutos',
                'Escucha tu canción favorita',
            ],
            'nivel_moderado': [
                'Sal a caminar 15 minutos',
                'Llama a alguien que te importe',
                'Escribe 3 cosas por las que estés agradecido',
                'Haz algo creativo por 20 minutos',
            ],
            'nivel_alto': [
                'Planifica algo que disfrutes para esta semana',
                'Identifica un objetivo y haz un primer paso',
                'Comparte tu progreso con alguien de confianza',
            ],
        }

    def suggest_preventive_activities(
        self,
        db: Session,
        usuario_id: int,
        days_lookback: int = 30
    ) -> List[Dict]:
        """
        Sugiere actividades preventivas basadas en patrones cíclicos.
        Si típicamente el viernes es mal día, recomienda actividades para prevenir.

        Returns:
            [{'actividad': str, 'razón': str, 'día_target': str, 'confianza': float}]
        """
        # Analizar ciclos emocionales
        cycles = emotion_service.detect_emotional_cycles(db, usuario_id, days_lookback)

        if 'error' in cycles:
            return []

        recommendations = []

        # Analizar patrones semanales
        if cycles.get('weekly_pattern'):
            worst_day = None
            worst_score = 10

            for day, data in cycles['weekly_pattern'].items():
                if data.get('avg_mood', 10) < worst_score:
                    worst_score = data['avg_mood']
                    worst_day = day

            if worst_day and worst_score < 6:
                # Este día típicamente es malo, recomendar prevención
                positive_habits = self._get_positive_habits(db, usuario_id)

                for habit in positive_habits[:2]:
                    recommendations.append({
                        'actividad': habit['nombre'],
                        'razón': f"Típicamente {worst_day.lower()} es un día más desafiante ({worst_score}/10). {habit['nombre']} suele ayudarte.",
                        'día_target': worst_day,
                        'confianza': 0.75,
                        'tipo': 'preventiva'
                    })

        # Analizar patrones diarios
        if cycles.get('daily_pattern'):
            worst_hour = None
            worst_score = 10

            for hour, data in cycles['daily_pattern'].items():
                if data.get('avg_mood', 10) < worst_score:
                    worst_score = data['avg_mood']
                    worst_hour = hour

            if worst_hour and worst_score < 6:
                recommendations.append({
                    'actividad': 'Preparar algo especial para esta hora',
                    'razón': f"Alrededor de las {worst_hour} tu ánimo típicamente baja. Prepara algo que disfrutes.",
                    'hora_target': worst_hour,
                    'confianza': 0.6,
                    'tipo': 'preventiva_horaria'
                })

        return recommendations

    def _get_positive_habits(
        self,
        db: Session,
        usuario_id: int
    ) -> List[Dict]:
        """Obtiene hábitos que tienen impacto positivo."""
        patterns = pattern_service.analyze_user_patterns(db, usuario_id, days_lookback=30)

        if not patterns.get('has_enough_data'):
            return []

        positive = [
            {
                'nombre': c['habit'],
                'impacto': c['impact'],
                'confianza': c['confidence']
            }
            for c in patterns.get('correlations', [])
            if c['impact'] > 0.2
        ]

        positive.sort(key=lambda x: x['impacto'], reverse=True)
        return positive

    def create_contextual_reminders(
        self,
        db: Session,
        usuario_id: int,
        current_mood: Optional[int] = None,
        recent_triggers: Optional[List[str]] = None
    ) -> List[Dict]:
        """
        Crea recordatorios contextuales basados en la situación actual.

        Args:
            db: Sesión de base de datos
            usuario_id: ID del usuario
            current_mood: Ánimo actual (1-10)
            recent_triggers: Desencadenantes emocionales recientes

        Returns:
            [{'recordatorio': str, 'contexto': str, 'prioridad': int (1-10)}]
        """
        reminders = []

        # Recordatorios basados en ánimo bajo
        if current_mood and current_mood <= 4:
            # Recordar que han pasado momentos similares
            low_moods = db.query(EstadoAnimo).filter(
                EstadoAnimo.usuario_id == usuario_id,
                EstadoAnimo.nivel <= 4
            ).order_by(EstadoAnimo.timestamp.desc()).limit(5).all()

            if len(low_moods) >= 2:
                recuperations = [m for m in low_moods if m.nivel > 6]
                if recuperations:
                    reminders.append({
                        'recordatorio': 'Recuerda que ya has salido de momentos como este antes',
                        'contexto': 'resilience',
                        'prioridad': 8
                    })

            # Recordar hábitos que ayudan
            positive_habits = self._get_positive_habits(db, usuario_id)
            if positive_habits:
                habit = positive_habits[0]
                reminders.append({
                    'recordatorio': f"Sabemos que {habit['nombre']} te ayuda. ¿Lo intentamos?",
                    'contexto': 'habit_suggestion',
                    'prioridad': 9
                })

        # Recordatorios basados en disparadores
        if recent_triggers:
            for trigger in recent_triggers[:2]:
                if trigger in ['estrés', 'ansiedad']:
                    reminders.append({
                        'recordatorio': f'Notamos {trigger}. ¿Quieres hablar sobre qué está pasando?',
                        'contexto': 'trigger_acknowledgment',
                        'prioridad': 7
                    })

        # Recordatorio de tracking
        if current_mood is None:
            reminders.append({
                'recordatorio': '¿Cómo te sientes en este momento?',
                'contexto': 'check_in',
                'prioridad': 3
            })

        reminders.sort(key=lambda x: x['prioridad'], reverse=True)
        return reminders[:3]

    def generate_personalized_challenges(
        self,
        db: Session,
        usuario_id: int,
        difficulty: str = 'moderate'
    ) -> List[Dict]:
        """
        Genera desafíos personalizados basados en hábitos positivos del usuario.
        Los desafíos son actividades pequeñas pero significativas.

        Args:
            difficulty: 'easy'|'moderate'|'hard'

        Returns:
            [{'desafío': str, 'descripción': str, 'beneficio_esperado': str, 'duración': str}]
        """
        positive_habits = self._get_positive_habits(db, usuario_id)

        if not positive_habits:
            return self._generic_challenges(difficulty)

        challenges = []

        difficulty_map = {
            'easy': {'duration': '5-10 minutos', 'intensity': 'baja'},
            'moderate': {'duration': '15-30 minutos', 'intensity': 'media'},
            'hard': {'duration': '45+ minutos', 'intensity': 'alta'},
        }

        params = difficulty_map.get(difficulty, difficulty_map['moderate'])

        # Crear desafíos basados en hábitos positivos
        for habit in positive_habits[:3]:
            if difficulty == 'easy':
                descripcion = f"Dedica 10 minutos a {habit['nombre']}. No es para perfeccionar, solo para empezar."
            elif difficulty == 'moderate':
                descripcion = f"Haz {habit['nombre']} con intención. Nota cómo te sientes antes y después."
            else:
                descripcion = f"Crea una rutina donde {habit['nombre']} sea un pilar. Hazlo 3 días seguidos."

            challenges.append({
                'desafío': f"Desafío: {habit['nombre'].capitalize()}",
                'descripción': descripcion,
                'beneficio_esperado': 'Mejorar tu ánimo y crear momentum positivo',
                'duración': params['duration'],
                'intensidad': params['intensity'],
                'hábito_base': habit['nombre']
            })

        return challenges[:3]

    def _generic_challenges(self, difficulty: str) -> List[Dict]:
        """Retorna desafíos genéricos si no hay datos personalizados."""
        generic = {
            'easy': [
                {
                    'desafío': 'Desafío 5 minutos',
                    'descripción': 'Tómate 5 minutos para respirar profundamente o escuchar música',
                    'beneficio_esperado': 'Calmar la mente',
                    'duración': '5 minutos'
                }
            ],
            'moderate': [
                {
                    'desafío': 'Paseo reflexivo',
                    'descripción': 'Camina durante 20 minutos sin distracciones, observando tu entorno',
                    'beneficio_esperado': 'Claridad mental y movimiento físico',
                    'duración': '20 minutos'
                }
            ],
            'hard': [
                {
                    'desafío': 'Proyecto creativo',
                    'descripción': 'Inicia un proyecto creativo pequeño (dibujo, escritura, música)',
                    'beneficio_esperado': 'Expresión emocional y sensación de logro',
                    'duración': '1+ hora'
                }
            ]
        }

        return generic.get(difficulty, generic['moderate'])

    def suggest_micro_habits(
        self,
        current_mood: Optional[int] = None,
        user_preferences: Optional[Dict] = None
    ) -> List[Dict]:
        """
        Sugiere micro-hábitos (acciones pequeñas de 1-5 minutos) adaptadas al ánimo actual.

        Returns:
            [{'micro_hábito': str, 'tiempo': str, 'efecto_esperado': str}]
        """
        if current_mood is None:
            mood_category = 'neutral'
        elif current_mood <= 3:
            mood_category = 'bajo'
        elif current_mood <= 6:
            mood_category = 'moderado'
        else:
            mood_category = 'alto'

        # Seleccionar templates basados en ánimo
        templates = self.micro_habits_templates.get(f'nivel_{mood_category}', self.micro_habits_templates['nivel_moderado'])

        micro_habits = []
        selected = random.sample(templates, min(3, len(templates)))

        mood_effects = {
            'bajo': 'pequeño paso hacia la mejora',
            'moderado': 'mantener el momentum',
            'alto': 'canalizar la energía positiva',
            'neutral': 'explorar qué te funciona',
        }

        for habit in selected:
            # Estimar duración
            if habit in self.micro_habits_templates['nivel_bajo']:
                tiempo = '2-5 minutos'
            elif habit in self.micro_habits_templates['nivel_moderado']:
                tiempo = '15-20 minutos'
            else:
                tiempo = '20+ minutos'

            micro_habits.append({
                'micro_hábito': habit,
                'tiempo': tiempo,
                'efecto_esperado': mood_effects[mood_category],
                'ánimo_target': mood_category
            })

        return micro_habits

    def get_next_recommended_action(
        self,
        db: Session,
        usuario_id: int,
        current_mood: Optional[int] = None
    ) -> Optional[Dict]:
        """
        Obtiene la próxima acción recomendada más relevante.
        Combinación inteligente de todas las recomendaciones.

        Returns:
            {'acción': str, 'razón': str, 'tipo': str, 'urgencia': int (1-10)}
        """
        recommendations = []

        # 1. Remindadores contextuales (más urgentes)
        contextual = self.create_contextual_reminders(db, usuario_id, current_mood)
        if contextual:
            rec = contextual[0]
            recommendations.append({
                'acción': rec['recordatorio'],
                'razón': f"Contexto actual: {rec['contexto']}",
                'tipo': 'recordatorio',
                'urgencia': rec['prioridad']
            })

        # 2. Micro-hábitos (inmediatos)
        micro = self.suggest_micro_habits(current_mood)
        if micro:
            rec = micro[0]
            recommendations.append({
                'acción': rec['micro_hábito'],
                'razón': f"Acción rápida para {rec['efecto_esperado']}",
                'tipo': 'micro_hábito',
                'urgencia': 7
            })

        # 3. Actividades preventivas (para los próximos días)
        preventivas = self.suggest_preventive_activities(db, usuario_id)
        if preventivas:
            rec = preventivas[0]
            recommendations.append({
                'acción': f"{rec['actividad']}",
                'razón': rec['razón'],
                'tipo': 'preventiva',
                'urgencia': int(rec['confianza'] * 8)
            })

        # Retornar la más urgente
        if recommendations:
            recommendations.sort(key=lambda x: x['urgencia'], reverse=True)
            return recommendations[0]

        return None


# Instancia global del servicio
recommendation_service = ProactiveRecommendationService()
