"""
Servicio NLP avanzado para análisis profundo de contexto conversacional.
Extrae entidades, sentimientos granulares, valores implícitos y patrones de lenguaje.
"""

from typing import Dict, List, Optional, Tuple
from collections import defaultdict, Counter
import re
import json
from datetime import datetime


class AdvancedNLPService:
    """
    Servicio de procesamiento de lenguaje natural avanzado.
    Proporciona análisis profundo de contexto conversacional.
    """

    def __init__(self):
        """Inicializa el servicio NLP con diccionarios de palabras clave."""
        self._initialize_sentiment_dictionaries()
        self._initialize_entity_patterns()
        self._initialize_values_patterns()

    def _initialize_sentiment_dictionaries(self):
        """Inicializa diccionarios para análisis de sentimiento granular."""
        # Emociones primarias
        self.primary_emotions = {
            'alegría': {
                'keywords': ['feliz', 'alegre', 'contento', 'contenta', 'genial', 'excelente', 'maravilloso', 'increíble'],
                'intensity_words': {'muy': 1.5, 'super': 1.5, 'realmente': 1.2, 'tan': 1.2},
                'value': 0.8
            },
            'tristeza': {
                'keywords': ['triste', 'deprimido', 'deprimida', 'angustia', 'dolor', 'lloro', 'lloraba', 'desprecio'],
                'intensity_words': {'profundamente': 1.5, 'realmente': 1.2, 'mucho': 1.2},
                'value': -0.8
            },
            'ansiedad': {
                'keywords': ['ansioso', 'ansiosa', 'nervioso', 'nerviosa', 'preocupado', 'preocupada', 'inquieto', 'inquieta'],
                'intensity_words': {'muy': 1.5, 'constantemente': 1.3, 'mucho': 1.2},
                'value': -0.6
            },
            'estrés': {
                'keywords': ['estrés', 'estres', 'estresado', 'estresada', 'presión', 'agobiado', 'agobiada', 'sobrecargado'],
                'intensity_words': {'extremadamente': 1.8, 'muy': 1.5, 'bastante': 1.2},
                'value': -0.7
            },
            'enojo': {
                'keywords': ['enojado', 'enojada', 'furioso', 'furiosa', 'ira', 'rabia', 'irritado', 'irritada', 'furioso'],
                'intensity_words': {'cegadoramente': 2.0, 'intensamente': 1.8, 'muy': 1.5},
                'value': -0.9
            },
            'calma': {
                'keywords': ['tranquilo', 'tranquila', 'paz', 'sereno', 'serena', 'relajado', 'relajada', 'pacífico'],
                'intensity_words': {'profundamente': 1.5, 'muy': 1.3, 'realmente': 1.2},
                'value': 0.5
            },
            'esperanza': {
                'keywords': ['esperanza', 'esperanzado', 'optimista', 'ilusión', 'promete', 'posibilidad', 'oportunidad'],
                'intensity_words': {'tremendamente': 1.5, 'mucha': 1.3, 'renovada': 1.2},
                'value': 0.6
            },
            'culpa': {
                'keywords': ['culpa', 'culpable', 'arrepentido', 'arrepentida', 'vergüenza', 'avergonzado', 'avergonzada'],
                'intensity_words': {'profundamente': 1.5, 'mucha': 1.3, 'tremendamente': 1.5},
                'value': -0.7
            },
            'soledad': {
                'keywords': ['solo', 'sola', 'soledad', 'aislado', 'aislada', 'incomprendido', 'incomprendida', 'abandonado'],
                'intensity_words': {'profundamente': 1.5, 'terriblemente': 1.5, 'mucho': 1.2},
                'value': -0.7
            },
            'satisfacción': {
                'keywords': ['satisfecho', 'satisfecha', 'cumplido', 'cumplida', 'logro', 'conseguí', 'alcancé', 'realizado'],
                'intensity_words': {'profundamente': 1.5, 'muy': 1.3, 'realmente': 1.2},
                'value': 0.7
            }
        }

        # Emociones secundarias (matices)
        self.secondary_emotions = {
            'decepción': ['decepcionado', 'decepcionada', 'desilusión', 'defraudado'],
            'frustración': ['frustrado', 'frustrada', 'molesto', 'molesta', 'irritante'],
            'nostalgia': ['extraño', 'nostalgia', 'añoro', 'echo de menos'],
            'envidia': ['envido', 'envidioso', 'celoso', 'celosa'],
            'compasión': ['compasión', 'empático', 'empatica', 'solidario', 'solidaria'],
            'orgullo': ['orgulloso', 'orgullosa', 'satisfecho', 'satisfecha'],
        }

    def _initialize_entity_patterns(self):
        """Inicializa patrones para identificar entidades."""
        self.entity_patterns = {
            'personas': {
                'pronouns': ['yo', 'tú', 'él', 'ella', 'nosotros', 'nosotras', 'ustedes'],
                'relationships': ['pareja', 'amigo', 'amiga', 'hermano', 'hermana', 'padre', 'madre', 'jefe', 'compañero', 'compañera', 'psicólogo', 'doctor', 'médico']
            },
            'lugares': {
                'location_words': ['oficina', 'casa', 'trabajo', 'escuela', 'universidad', 'hospital', 'calle', 'parque', 'país', 'ciudad']
            },
            'eventos': {
                'event_words': ['reunión', 'reunion', 'cita', 'boda', 'fiesta', 'viaje', 'presentación', 'examen', 'prueba', 'entrevista']
            }
        }

    def _initialize_values_patterns(self):
        """Inicializa patrones para detectar valores implícitos."""
        self.value_patterns = {
            'familia': ['familia', 'padres', 'hijos', 'hermanos', 'abuela', 'abuelo', 'sobrino'],
            'amistad': ['amigos', 'amistades', 'comunidad', 'rodeado', 'conexión'],
            'carrera': ['profesión', 'carrera', 'éxito', 'desarrollo', 'crecimiento profesional'],
            'salud': ['salud', 'bienestar', 'ejercicio', 'dieta', 'médico', 'terapia'],
            'estabilidad': ['seguridad', 'estable', 'responsable', 'confianza', 'predictible'],
            'creatividad': ['crear', 'arte', 'música', 'escritura', 'innovación', 'expresión'],
            'aprendizaje': ['aprender', 'conocimiento', 'educación', 'cursos', 'desarrollo personal'],
            'libertad': ['libertad', 'independencia', 'autonomía', 'decisión propia'],
            'justicia': ['justicia', 'equidad', 'fairness', 'discriminación', 'derechos']
        }

    def analyze_sentiment_detailed(self, texto: str) -> Dict:
        """
        Analiza el sentimiento del texto de forma granular.
        Retorna emociones primarias, secundarias e intensidad.

        Returns:
            {
                'primary_emotions': [{'emotion': str, 'intensity': float, 'confidence': float}],
                'secondary_emotions': [{'emotion': str, 'confidence': float}],
                'overall_sentiment': float (-1 a 1),
                'emotional_complexity': str ('simple', 'moderate', 'complex'),
                'dominant_emotion': str
            }
        """
        texto_lower = texto.lower()
        detected_emotions = []

        # Detectar emociones primarias
        for emotion, data in self.primary_emotions.items():
            emotion_score = 0
            matches = 0

            for keyword in data['keywords']:
                if keyword in texto_lower:
                    matches += 1
                    # Buscar palabras de intensidad cerca del keyword
                    intensity_multiplier = 1.0
                    words = texto_lower.split()
                    for i, word in enumerate(words):
                        if keyword in word:
                            # Revisar palabras anteriores
                            if i > 0 and words[i-1] in data['intensity_words']:
                                intensity_multiplier = data['intensity_words'][words[i-1]]
                            break

                    emotion_score += data['value'] * intensity_multiplier

            if matches > 0:
                confidence = min(matches / 3.0, 1.0)  # Máx 3 keywords por emoción
                detected_emotions.append({
                    'emotion': emotion,
                    'intensity': emotion_score / matches if matches > 0 else 0,
                    'confidence': confidence,
                    'matches': matches
                })

        # Detectar emociones secundarias
        secondary_detected = []
        for emotion, keywords in self.secondary_emotions.items():
            for keyword in keywords:
                if keyword in texto_lower:
                    secondary_detected.append(emotion)
                    break

        # Ordenar por confianza
        detected_emotions.sort(key=lambda x: x['confidence'] * abs(x['intensity']), reverse=True)

        # Calcular sentimiento general
        overall_sentiment = sum(e['intensity'] * e['confidence'] for e in detected_emotions)
        overall_sentiment = max(-1, min(1, overall_sentiment))  # Normalizar -1 a 1

        # Determinar complejidad emocional
        emotional_complexity = 'simple'
        if len(detected_emotions) >= 3:
            emotional_complexity = 'complex'
        elif len(detected_emotions) >= 2:
            emotional_complexity = 'moderate'

        dominant_emotion = detected_emotions[0]['emotion'] if detected_emotions else 'neutral'

        return {
            'primary_emotions': detected_emotions[:3],  # Top 3
            'secondary_emotions': list(set(secondary_detected)),
            'overall_sentiment': round(overall_sentiment, 2),
            'emotional_complexity': emotional_complexity,
            'dominant_emotion': dominant_emotion,
            'text_length': len(texto.split())
        }

    def extract_entities(self, texto: str) -> Dict[str, List[str]]:
        """
        Extrae entidades nombradas: personas, lugares, eventos.

        Returns:
            {
                'personas': [str],
                'lugares': [str],
                'eventos': [str],
                'relationships': [str]
            }
        """
        texto_lower = texto.lower()
        entities = {
            'personas': [],
            'lugares': [],
            'eventos': [],
            'relationships': []
        }

        # Extraer personas y relaciones
        for relationship in self.entity_patterns['personas']['relationships']:
            if relationship in texto_lower:
                entities['relationships'].append(relationship)
                # Buscar adjetivos o nombres asociados
                pattern = rf'(?:mi|tu|su|el|la)?\s+(\w+)?\s+{relationship}'
                matches = re.findall(pattern, texto_lower)
                for match in matches:
                    if match and len(match) > 2:
                        entities['personas'].append(match.strip())

        # Extraer lugares
        for location in self.entity_patterns['lugares']['location_words']:
            if location in texto_lower:
                entities['lugares'].append(location)

        # Extraer eventos
        for event in self.entity_patterns['eventos']['event_words']:
            if event in texto_lower:
                entities['eventos'].append(event)

        # Limpiar duplicados
        for key in entities:
            entities[key] = list(set(entities[key]))

        return entities

    def detect_values_and_priorities(self, texto: str) -> Dict[str, float]:
        """
        Detecta valores e prioridades implícitas del usuario.

        Returns:
            {'valor_1': confidence, 'valor_2': confidence, ...}
        """
        texto_lower = texto.lower()
        detected_values = {}

        # Palabras que indican prioridad/importancia
        priority_indicators = ['importante', 'prioridad', 'necesito', 'debo', 'quiero', 'sueño', 'meta', 'objetivo']

        for value, keywords in self.value_patterns.items():
            matches = sum(1 for keyword in keywords if keyword in texto_lower)

            if matches > 0:
                # Aumentar confianza si hay palabras de prioridad cercanas
                confidence = min(matches / len(keywords), 1.0)

                for indicator in priority_indicators:
                    if indicator in texto_lower:
                        # Buscar si están cerca
                        for keyword in keywords:
                            if keyword in texto_lower:
                                confidence = min(confidence * 1.3, 1.0)
                                break

                detected_values[value] = round(confidence, 2)

        return dict(sorted(detected_values.items(), key=lambda x: x[1], reverse=True))

    def extract_language_patterns(self, texts: List[str]) -> Dict:
        """
        Extrae patrones de lenguaje favoritos del usuario a partir de múltiples mensajes.
        Análisis de vocabulario, expresiones recurrentes, nivel de formalidad.

        Args:
            texts: Lista de mensajes del usuario

        Returns:
            {
                'favorite_expressions': [str],
                'vocabulary_level': str ('simple', 'moderate', 'formal'),
                'use_emojis': bool,
                'use_exclamations': bool,
                'common_words': [str],
                'sentence_structure': str ('short', 'medium', 'long')
            }
        """
        if not texts:
            return self._empty_language_patterns()

        combined_text = ' '.join(texts).lower()

        # Contar palabras
        words = re.findall(r'\b\w+\b', combined_text)
        word_freq = Counter(words)

        # Filtrar palabras comunes sin sentido
        stop_words = {'el', 'la', 'de', 'que', 'y', 'a', 'en', 'es', 'se', 'no', 'por', 'para', 'con', 'un', 'una', 'los', 'las', 'del', 'al'}
        meaningful_words = [word for word, count in word_freq.most_common(20) if word not in stop_words and len(word) > 2]

        # Detectar nivel de formalidad
        formal_words = ['así mismo', 'no obstante', 'por lo tanto', 'puesto que', 'en conclusión']
        formal_count = sum(1 for formal_word in formal_words if formal_word in combined_text)

        if formal_count > 5:
            vocabulary_level = 'formal'
        elif len(meaningful_words) > 15 or any(len(w) > 10 for w in meaningful_words):
            vocabulary_level = 'moderate'
        else:
            vocabulary_level = 'simple'

        # Detectar emojis y puntuación
        use_emojis = any(ord(char) > 127 for char in ''.join(texts) if char not in 'áéíóúñüàâäèêëìîïòôöùûü')
        use_exclamations = any(text.count('!') > 0 or text.count('?') > 1 for text in texts)

        # Analizar longitud de oraciones
        sentences = re.split(r'[.!?]+', combined_text)
        avg_sentence_length = sum(len(s.split()) for s in sentences) / max(len(sentences), 1)

        if avg_sentence_length > 15:
            sentence_structure = 'long'
        elif avg_sentence_length > 8:
            sentence_structure = 'medium'
        else:
            sentence_structure = 'short'

        # Extraer expresiones recurrentes (frases de 2-3 palabras que aparecen varias veces)
        phrases = defaultdict(int)
        for i in range(len(words) - 2):
            phrase = ' '.join(words[i:i+3])
            if len(phrase.split()) >= 2 and all(word not in stop_words for word in phrase.split()):
                phrases[phrase] += 1

        favorite_expressions = [phrase for phrase, count in phrases.most_common(5) if count >= 2]

        return {
            'favorite_expressions': favorite_expressions,
            'vocabulary_level': vocabulary_level,
            'use_emojis': use_emojis,
            'use_exclamations': use_exclamations,
            'common_words': meaningful_words[:5],
            'sentence_structure': sentence_structure,
            'avg_sentence_length': round(avg_sentence_length, 1)
        }

    def _empty_language_patterns(self) -> Dict:
        """Retorna estructura vacía de patrones de lenguaje."""
        return {
            'favorite_expressions': [],
            'vocabulary_level': 'moderate',
            'use_emojis': False,
            'use_exclamations': False,
            'common_words': [],
            'sentence_structure': 'medium',
            'avg_sentence_length': 0
        }

    def analyze_complete_context(self, texto: str, conversation_history: List[str] = None) -> Dict:
        """
        Realiza un análisis completo del contexto conversacional.
        Combina todas las capacidades de NLP.

        Returns:
            {
                'sentiment': {...},
                'entities': {...},
                'values': {...},
                'language_patterns': {...} (si hay historial)
            }
        """
        result = {
            'sentiment': self.analyze_sentiment_detailed(texto),
            'entities': self.extract_entities(texto),
            'values': self.detect_values_and_priorities(texto),
        }

        if conversation_history:
            result['language_patterns'] = self.extract_language_patterns(conversation_history + [texto])

        return result


# Instancia global del servicio NLP
nlp_service = AdvancedNLPService()
