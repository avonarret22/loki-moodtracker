"""
Servicio de adaptación de personalidad para Loki.
Aprende y adapta la personalidad de Loki según las preferencias del usuario.
"""

from typing import List, Dict, Optional
from sqlalchemy.orm import Session
import json
from datetime import datetime, timedelta
from collections import defaultdict, Counter

from app.models.mood import ConversacionContexto, PerfilUsuario, EstadoAnimo
from app.services.nlp_service import nlp_service


class PersonalityAdaptationService:
    """
    Servicio para adaptar la personalidad de Loki según el usuario.
    Detecta preferencias, temas sensibles y patrones de comunicación.
    """

    def __init__(self):
        # Roles que Loki puede adoptar
        self.available_roles = {
            'coach': {
                'description': 'Motivador y propositivo',
                'tone': 'energético, positivo, orientado a metas',
                'approach': 'directivo, con sugerencias claras'
            },
            'confidente': {
                'description': 'Empático y validante',
                'tone': 'cálido, comprensivo, no juzgador',
                'approach': 'escucha activa, validación emocional'
            },
            'psicólogo': {
                'description': 'Reflexivo y profundo',
                'tone': 'profesional pero accesible, reflexivo',
                'approach': 'preguntas profundas, análisis de patrones'
            },
            'amigo': {
                'description': 'Informal y cercano',
                'tone': 'casual, relajado, conversacional',
                'approach': 'compartir experiencias, humor inclusivo'
            },
        }

        # Umbrales emocionales para detectar sensibilidad
        self.sensitivity_threshold = 0.3  # 30% de apariciones de un tema en ánimos bajos

    def detect_user_conversation_preferences(
        self,
        conversation_texts: List[str]
    ) -> Dict:
        """
        Detecta preferencias conversacionales del usuario.
        Analiza: formalidad, directitud, preferencia por detalle, velocidad de respuesta.

        Returns:
            {
                'formality_level': 'casual'|'moderate'|'formal',
                'directness': 'indirect'|'balanced'|'direct',
                'detail_preference': 'brief'|'moderate'|'detailed',
                'response_speed': 'quick'|'thoughtful',
                'preferred_role': 'coach'|'confidente'|'psicólogo'|'amigo'
            }
        """
        if not conversation_texts:
            return self._default_preferences()

        combined = ' '.join(conversation_texts).lower()

        # Analizar formalidad
        formal_markers = ['por lo tanto', 'así mismo', 'no obstante', 'en conclusión']
        casual_markers = ['jaja', 'haha', 'lol', 'pero bueno', 'viste']
        formal_count = sum(combined.count(m) for m in formal_markers)
        casual_count = sum(combined.count(m) for m in casual_markers)

        if formal_count > casual_count * 2:
            formality = 'formal'
        elif casual_count > formal_count * 2:
            formality = 'casual'
        else:
            formality = 'moderate'

        # Analizar directitud
        direct_phrases = ['necesito', 'quiero', 'tengo que', 'debo', 'voy a']
        indirect_phrases = ['creo que', 'siento que', 'parece que', 'podría ser', 'quizás']
        direct_count = sum(combined.count(p) for p in direct_phrases)
        indirect_count = sum(combined.count(p) for p in indirect_phrases)

        if direct_count > indirect_count * 1.5:
            directness = 'direct'
        elif indirect_count > direct_count * 1.5:
            directness = 'indirect'
        else:
            directness = 'balanced'

        # Analizar preferencia por detalle (longitud promedio de mensajes)
        avg_message_length = sum(len(t.split()) for t in conversation_texts) / max(len(conversation_texts), 1)
        if avg_message_length < 10:
            detail_pref = 'brief'
        elif avg_message_length < 30:
            detail_pref = 'moderate'
        else:
            detail_pref = 'detailed'

        # Analizar velocidad de respuesta (cuánto espera para escribir)
        # Esto se inferiría de marcas de continuidad ("...", "bueno", "espera")
        continuation_markers = ['...', 'bueno', 'espera', 'un momento', 'dejame']
        if sum(combined.count(m) for m in continuation_markers) > 5:
            response_speed = 'quick'
        else:
            response_speed = 'thoughtful'

        # Determinar rol preferido basado en patrones
        preferred_role = self._infer_preferred_role(formality, directness, detail_pref)

        return {
            'formality_level': formality,
            'directness': directness,
            'detail_preference': detail_pref,
            'response_speed': response_speed,
            'preferred_role': preferred_role,
            'conversation_count': len(conversation_texts)
        }

    def _default_preferences(self) -> Dict:
        """Retorna preferencias por defecto."""
        return {
            'formality_level': 'moderate',
            'directness': 'balanced',
            'detail_preference': 'moderate',
            'response_speed': 'thoughtful',
            'preferred_role': 'confidente',
            'conversation_count': 0
        }

    def _infer_preferred_role(
        self,
        formality: str,
        directness: str,
        detail_pref: str
    ) -> str:
        """
        Infiere el rol preferido basado en preferencias de comunicación.
        """
        if formality == 'casual' and directness == 'balanced':
            return 'amigo'
        elif detail_pref == 'detailed' and directness != 'direct':
            return 'psicólogo'
        elif directness == 'direct' and formality != 'formal':
            return 'coach'
        else:
            return 'confidente'

    def identify_sensitive_topics(
        self,
        db: Session,
        usuario_id: int,
        days_lookback: int = 60
    ) -> List[Dict]:
        """
        Identifica temas que están asociados con emociones negativas o baja de ánimo.
        Estos temas requieren mayor sensibilidad y cuidado.

        Returns:
            [{'tema': str, 'sensibilidad': float (0-1), 'ultimo_incidente': datetime}]
        """
        cutoff_date = datetime.utcnow() - timedelta(days=days_lookback)

        # Obtener ánimos bajos
        low_moods = db.query(EstadoAnimo).filter(
            and_(
                EstadoAnimo.usuario_id == usuario_id,
                EstadoAnimo.timestamp >= cutoff_date,
                EstadoAnimo.nivel <= 4
            )
        ).all()

        if not low_moods:
            return []

        # Definir temas potencialmente sensibles
        sensitive_topic_keywords = {
            'trabajo': ['trabajo', 'jefe', 'proyecto', 'laboral', 'carrera', 'despido'],
            'relaciones': ['pareja', 'ruptura', 'pelea', 'familia', 'discusión', 'infidelidad'],
            'salud': ['enfermo', 'dolor', 'cansado', 'medicina', 'hospital', 'depresión'],
            'economía': ['dinero', 'deuda', 'dinero', 'pobreza', 'gastar', 'cuenta'],
            'soledad': ['solo', 'aislado', 'incomprendido', 'abandonado', 'nadie'],
            'auto-confianza': ['fracaso', 'incapaz', 'inútil', 'no puedo', 'no merezco'],
            'trauma': ['miedo', 'pánico', 'fobia', 'pesadilla', 'recuerdo'],
        }

        tema_sensitivity = defaultdict(lambda: {'count': 0, 'total_low_moods': len(low_moods), 'ultimo': None})

        for mood in low_moods:
            texto_combined = (mood.notas_texto or '') + ' ' + (mood.disparadores_detectados or '')
            texto_lower = texto_combined.lower()

            for tema, keywords in sensitive_topic_keywords.items():
                if any(keyword in texto_lower for keyword in keywords):
                    tema_sensitivity[tema]['count'] += 1
                    tema_sensitivity[tema]['ultimo'] = mood.timestamp

        # Convertir a lista con sensibilidad calculada
        sensitive_topics = []
        for tema, data in tema_sensitivity.items():
            sensibilidad = data['count'] / data['total_low_moods']
            if sensibilidad >= self.sensitivity_threshold:
                sensitive_topics.append({
                    'tema': tema,
                    'sensibilidad': round(sensibilidad, 2),
                    'incidentes': data['count'],
                    'ultimo_incidente': data['ultimo']
                })

        # Ordenar por sensibilidad
        sensitive_topics.sort(key=lambda x: x['sensibilidad'], reverse=True)

        return sensitive_topics

    def learn_favorite_phrases(
        self,
        conversation_texts: List[str]
    ) -> List[str]:
        """
        Extrae las expresiones y frases favoritas del usuario.
        Útil para mejorar la naturalidad de las respuestas.

        Returns:
            ['frase 1', 'frase 2', ...]
        """
        if not conversation_texts:
            return []

        combined = ' '.join(conversation_texts)

        # Extraer usando NLP service
        patterns = nlp_service.extract_language_patterns(conversation_texts)

        favorite_expressions = patterns.get('favorite_expressions', [])

        # Agregar expresiones adicionales que aparecen frecuentemente
        from collections import Counter
        import re

        # Buscar frases cortas recurrentes (2-4 palabras)
        phrase_pattern = r'\b(?:me|te|nos|les)?\s+\w+\s+(?:que|de|por)\s+\w+\b'
        phrases = re.findall(phrase_pattern, combined)
        phrase_counts = Counter(phrases)

        for phrase, count in phrase_counts.most_common(3):
            if count >= 2 and phrase not in favorite_expressions:
                favorite_expressions.append(phrase)

        return favorite_expressions[:5]

    def adapt_tone_to_emotional_state(
        self,
        current_mood: Optional[int],
        emotional_complexity: Optional[str] = None
    ) -> Dict:
        """
        Adapta el tono de Loki según el estado emocional actual del usuario.

        Args:
            current_mood: Nivel de ánimo 1-10
            emotional_complexity: 'simple'|'moderate'|'complex'

        Returns:
            {
                'tone': str,
                'approach': str,
                'response_length': 'brief'|'moderate'|'detailed',
                'emoji_usage': bool,
                'humor_level': 'none'|'light'|'moderate'
            }
        """
        if current_mood is None:
            return self._default_tone_adaptation()

        # Adaptar según ánimo
        if current_mood <= 3:
            # Bajo ánimo: máxima empatía, validación
            tone = 'muy empático, validante, sin presión'
            approach = 'escucha activa, validación emocional'
            response_length = 'moderate'
            emoji_usage = False
            humor_level = 'none'

        elif current_mood <= 5:
            # Ánimo bajo-moderado: empatía con esperanza
            tone = 'empático, comprensivo, con toque de esperanza'
            approach = 'validación + exploración reflexiva'
            response_length = 'moderate'
            emoji_usage = False
            humor_level = 'light'

        elif current_mood <= 7:
            # Ánimo moderado: equilibrio
            tone = 'amable, equilibrado, accesible'
            approach = 'conversación natural'
            response_length = 'moderate'
            emoji_usage = True
            humor_level = 'light'

        else:
            # Ánimo alto: entusiasta, constructivo
            tone = 'positivo, entusiasta, empoderador'
            approach = 'refuerzo, exploración de oportunidades'
            response_length = 'moderate'
            emoji_usage = True
            humor_level = 'moderate'

        # Adaptar según complejidad emocional
        if emotional_complexity == 'complex':
            response_length = 'detailed'
            approach = 'análisis profundo, reflexión'

        return {
            'tone': tone,
            'approach': approach,
            'response_length': response_length,
            'emoji_usage': emoji_usage,
            'humor_level': humor_level,
            'current_mood_level': current_mood
        }

    def _default_tone_adaptation(self) -> Dict:
        """Retorna adaptación de tono por defecto."""
        return {
            'tone': 'empático, equilibrado',
            'approach': 'escucha activa',
            'response_length': 'moderate',
            'emoji_usage': True,
            'humor_level': 'light',
            'current_mood_level': None
        }

    def generate_adapted_system_prompt_enhancement(
        self,
        db: Session,
        usuario_id: int,
        usuario_nombre: str,
        current_mood: Optional[int] = None
    ) -> str:
        """
        Genera un enhancement al system prompt basado en la personalidad aprendida.
        Este texto se agrega al system prompt de Claude.

        Returns:
            Texto de instrucciones adicionales para enriquecer el prompt
        """
        # Obtener o crear perfil del usuario
        perfil = db.query(PerfilUsuario).filter(
            PerfilUsuario.usuario_id == usuario_id
        ).first()

        if not perfil:
            return ""

        # Parsear datos JSON del perfil
        try:
            prefs = json.loads(perfil.preferencias_conversacionales or '{}')
            temas_sensibles = json.loads(perfil.temas_sensibles or '[]')
            expresiones_favoritas = json.loads(perfil.patrones_lenguaje_favoritos or '[]')
            emociones_frecuentes = json.loads(perfil.emociones_primarias_frecuentes or '{}')
        except:
            return ""

        # Construir enhancement
        enhancement = f"\n## PERSONALIZACIÓN PARA {usuario_nombre.upper()}\n\n"

        # Rol preferido
        preferred_role = prefs.get('preferred_role', 'confidente')
        role_data = self.available_roles.get(preferred_role, {})
        enhancement += f"**Rol recomendado:** {preferred_role.capitalize()}\n"
        if role_data:
            enhancement += f"- Tono: {role_data['tone']}\n"
            enhancement += f"- Enfoque: {role_data['approach']}\n"

        # Preferencias de comunicación
        if prefs.get('formality_level'):
            enhancement += f"\n**Estilo conversacional:** {prefs['formality_level'].capitalize()}\n"
        if prefs.get('directness'):
            enhancement += f"**Directitud:** {prefs['directness'].capitalize()}\n"

        # Temas sensibles
        if temas_sensibles:
            enhancement += f"\n**⚠️ TEMAS SENSIBLES** (mayor cuidado):\n"
            for tema in temas_sensibles[:3]:
                enhancement += f"- {tema}: Mostrar extra empatía, no asumir nada\n"

        # Emociones frecuentes
        if emociones_frecuentes:
            enhancement += f"\n**Emociones frecuentes:**\n"
            for emocion in list(emociones_frecuentes.keys())[:3]:
                enhancement += f"- {emocion}: Probablemente lo pueda ayudar\n"

        # Expresiones favoritas a usar
        if expresiones_favoritas:
            enhancement += f"\n**Expresiones favoritas a incorporar naturalmente:**\n"
            for expr in expresiones_favoritas[:3]:
                enhancement += f"- '{expr}'\n"

        # Adaptación por estado emocional actual
        tone_adapt = self.adapt_tone_to_emotional_state(current_mood)
        if tone_adapt['tone']:
            enhancement += f"\n**Adaptación actual:** {tone_adapt['tone']}\n"

        return enhancement


# Instancia global del servicio
personality_service = PersonalityAdaptationService()
