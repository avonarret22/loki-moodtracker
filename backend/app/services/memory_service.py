"""
Servicio de memoria conversacional para Loki.
Gestiona resúmenes de conversaciones, perfiles de usuario y contexto histórico.
"""

from typing import List, Dict, Optional
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, desc
from datetime import datetime, timedelta
import json
from collections import defaultdict, Counter

from app.models.mood import (
    Usuario, ConversacionContexto, ResumenConversacion,
    PerfilUsuario, EstadoAnimo
)


class ConversationalMemoryService:
    """
    Servicio para gestionar memoria conversacional de largo plazo.
    Mantiene resúmenes, perfiles de usuario y contexto histórico.
    """

    def __init__(self):
        self.summary_interval = 10  # Generar resumen cada 10 mensajes
        self.lookback_days = 30  # Analizar últimos 30 días para patrones

    def generate_conversation_summary(
        self,
        db: Session,
        usuario_id: int,
        num_messages: int = None
    ) -> Optional[ResumenConversacion]:
        """
        Genera un resumen de las últimas N conversaciones.
        Identifica temas principales, emociones y progreso emocional.

        Args:
            db: Sesión de base de datos
            usuario_id: ID del usuario
            num_messages: Número de mensajes a resumir (default: summary_interval)

        Returns:
            Objeto ResumenConversacion guardado en BD
        """
        if num_messages is None:
            num_messages = self.summary_interval

        # Obtener últimas conversaciones
        conversaciones = db.query(ConversacionContexto).filter(
            ConversacionContexto.usuario_id == usuario_id
        ).order_by(desc(ConversacionContexto.timestamp)).limit(num_messages).all()

        if not conversaciones or len(conversaciones) < 3:
            return None

        # Invertir para tener orden cronológico
        conversaciones = list(reversed(conversaciones))

        # Extraer información
        temas = self._extract_topics(conversaciones)
        emociones = self._extract_emotions(conversaciones)
        progreso = self._calculate_emotional_progress(conversaciones)

        # Generar resumen en lenguaje natural
        resumen_texto = self._generate_natural_summary(
            conversaciones, temas, emociones, progreso
        )

        # Guardar resumen en BD
        resumen = ResumenConversacion(
            usuario_id=usuario_id,
            resumen_texto=resumen_texto,
            temas_principales=json.dumps(temas, ensure_ascii=False),
            emociones_detectadas=json.dumps(emociones, ensure_ascii=False),
            progreso_emocional=json.dumps(progreso, ensure_ascii=False),
            num_mensajes=len(conversaciones),
            periodo_inicio=conversaciones[0].timestamp,
            periodo_fin=conversaciones[-1].timestamp
        )

        db.add(resumen)
        db.commit()

        return resumen

    def _extract_topics(self, conversaciones: List[ConversacionContexto]) -> List[str]:
        """
        Extrae temas principales de las conversaciones.
        """
        temas = []

        topic_keywords = {
            'trabajo': ['trabajo', 'jefe', 'proyecto', 'reunión', 'laboral', 'carrera'],
            'relaciones': ['pareja', 'familia', 'amigo', 'pelea', 'discusión', 'relación'],
            'salud_bienestar': ['salud', 'ejercicio', 'dieta', 'cansado', 'enfermo', 'médico'],
            'emociones': ['triste', 'ansioso', 'feliz', 'enojado', 'deprimido', 'estrés'],
            'metas_aspiraciones': ['quiero', 'objetivo', 'meta', 'sueño', 'quería', 'esperanza'],
            'eventos_especiales': ['fiesta', 'viaje', 'cita', 'boda', 'cumpleaños'],
            'hobbies_ocio': ['hobby', 'lectura', 'música', 'juego', 'películas', 'series'],
        }

        for conversacion in conversaciones:
            texto_lower = (conversacion.mensaje_usuario or '').lower()

            for tema, keywords in topic_keywords.items():
                for keyword in keywords:
                    if keyword in texto_lower and tema not in temas:
                        temas.append(tema)
                        break

        return temas

    def _extract_emotions(self, conversaciones: List[ConversacionContexto]) -> Dict[str, int]:
        """
        Extrae y cuenta emociones de las conversaciones.
        """
        emociones = defaultdict(int)

        emotion_keywords = {
            'alegría': ['feliz', 'alegre', 'contento', 'genial', 'excelente'],
            'tristeza': ['triste', 'deprimido', 'angustia', 'dolor'],
            'ansiedad': ['ansioso', 'nervioso', 'preocupado', 'inquieto'],
            'estrés': ['estrés', 'presión', 'agobiado', 'sobrecargado'],
            'enojo': ['enojado', 'furioso', 'ira', 'rabia', 'irritado'],
            'calma': ['tranquilo', 'paz', 'sereno', 'relajado'],
            'esperanza': ['esperanza', 'optimista', 'ilusión', 'posibilidad'],
        }

        for conversacion in conversaciones:
            texto_lower = (conversacion.mensaje_usuario or '').lower()

            for emocion, keywords in emotion_keywords.items():
                for keyword in keywords:
                    if keyword in texto_lower:
                        emociones[emocion] += 1

        # Retornar top 5 emociones
        return dict(sorted(emociones.items(), key=lambda x: x[1], reverse=True)[:5])

    def _calculate_emotional_progress(
        self,
        conversaciones: List[ConversacionContexto]
    ) -> Dict:
        """
        Calcula la progresión emocional a través de las conversaciones.
        """
        if not conversaciones:
            return {}

        # Obtener niveles de ánimo si están registrados en notas
        progress = {
            'inicio': None,
            'fin': None,
            'cambio': None,
            'estabilidad': 'desconocida'
        }

        # Búsqueda simple de números en los mensajes para extraer mood
        import re

        moods = []
        for conv in conversaciones:
            matches = re.findall(r'\b([1-9]|10)\b', conv.mensaje_usuario or '')
            if matches:
                moods.extend([int(m) for m in matches])

        if moods:
            progress['inicio'] = moods[0]
            progress['fin'] = moods[-1]
            progress['cambio'] = moods[-1] - moods[0]

            # Calcular estabilidad
            if len(moods) > 1:
                variance = sum((m - sum(moods) / len(moods)) ** 2 for m in moods) / len(moods)
                if variance < 2:
                    progress['estabilidad'] = 'estable'
                elif variance < 5:
                    progress['estabilidad'] = 'variable'
                else:
                    progress['estabilidad'] = 'muy variable'

        return progress

    def _generate_natural_summary(
        self,
        conversaciones: List[ConversacionContexto],
        temas: List[str],
        emociones: Dict[str, int],
        progreso: Dict
    ) -> str:
        """
        Genera un resumen en lenguaje natural de las conversaciones.
        """
        temas_str = ', '.join(temas) if temas else 'varios temas'
        emocion_dominante = list(emociones.keys())[0] if emociones else 'neutral'
        num_conversaciones = len(conversaciones)

        cambio_emocional = ""
        if progreso.get('cambio') is not None:
            cambio = progreso['cambio']
            if cambio > 0:
                cambio_emocional = f"con una tendencia positiva de +{cambio} puntos"
            elif cambio < 0:
                cambio_emocional = f"con una tendencia negativa de {cambio} puntos"
            else:
                cambio_emocional = "sin cambios significativos"

        resumen = (
            f"En las últimas {num_conversaciones} conversaciones, hemos hablado sobre {temas_str}. "
            f"La emoción dominante ha sido {emocion_dominante} {cambio_emocional}. "
            f"La estabilidad emocional se mantiene {progreso.get('estabilidad', 'desconocida')}."
        )

        return resumen

    def extract_recurring_themes(
        self,
        db: Session,
        usuario_id: int,
        days: int = None
    ) -> List[Dict]:
        """
        Identifica temas recurrentes en el historial de conversaciones.
        Analiza qué temas aparecen frecuentemente a lo largo del tiempo.

        Returns:
            [{'tema': str, 'frecuencia': int, 'ultima_mencion': datetime}]
        """
        if days is None:
            days = self.lookback_days

        cutoff_date = datetime.utcnow() - timedelta(days=days)

        conversaciones = db.query(ConversacionContexto).filter(
            and_(
                ConversacionContexto.usuario_id == usuario_id,
                ConversacionContexto.timestamp >= cutoff_date
            )
        ).all()

        tema_frecuencia = defaultdict(lambda: {'count': 0, 'ultima_mencion': None})

        topic_keywords = {
            'trabajo': ['trabajo', 'jefe', 'proyecto', 'reunión'],
            'relaciones': ['pareja', 'familia', 'amigos'],
            'salud': ['ejercicio', 'sueño', 'dieta'],
            'emociones_bajas': ['triste', 'deprimido', 'ansioso', 'estres'],
            'objetivos': ['quiero', 'objetivo', 'meta', 'sueño'],
        }

        for conversacion in conversaciones:
            texto_lower = (conversacion.mensaje_usuario or '').lower()

            for tema, keywords in topic_keywords.items():
                for keyword in keywords:
                    if keyword in texto_lower:
                        tema_frecuencia[tema]['count'] += 1
                        tema_frecuencia[tema]['ultima_mencion'] = conversacion.timestamp
                        break

        # Formatear resultado
        temas_recurrentes = [
            {
                'tema': tema,
                'frecuencia': data['count'],
                'ultima_mencion': data['ultima_mencion']
            }
            for tema, data in tema_frecuencia.items()
            if data['count'] >= 3  # Solo temas mencionados 3+ veces
        ]

        # Ordenar por frecuencia
        temas_recurrentes.sort(key=lambda x: x['frecuencia'], reverse=True)

        return temas_recurrentes

    def build_user_profile(
        self,
        db: Session,
        usuario_id: int
    ) -> PerfilUsuario:
        """
        Construye o actualiza el perfil emocional del usuario.
        Consolida información de conversaciones, patrones de lenguaje y valores.

        Returns:
            Objeto PerfilUsuario guardado en BD
        """
        # Verificar si ya existe perfil
        perfil = db.query(PerfilUsuario).filter(
            PerfilUsuario.usuario_id == usuario_id
        ).first()

        # Extraer información del usuario
        conversaciones = db.query(ConversacionContexto).filter(
            ConversacionContexto.usuario_id == usuario_id
        ).order_by(desc(ConversacionContexto.timestamp)).limit(50).all()

        if not conversaciones:
            if not perfil:
                perfil = PerfilUsuario(usuario_id=usuario_id)
                db.add(perfil)
            db.commit()
            return perfil

        # Extraer patrones
        conversacion_texts = [c.mensaje_usuario for c in conversaciones if c.mensaje_usuario]

        temas_recurrentes = self.extract_recurring_themes(db, usuario_id)
        emociones_dict = self._extract_emotions(conversaciones)

        # Detectar preferencias conversacionales (formalidad, directitud)
        vocab_level = self._detect_vocabulary_level(conversacion_texts)
        directness = self._detect_directness(conversacion_texts)

        # Detectar temas sensibles (asociados con ánimos bajos)
        sensibles = self._identify_sensitive_topics(db, usuario_id)

        # Extraer patrones de lenguaje favoritos
        from app.services.nlp_service import nlp_service
        language_patterns = nlp_service.extract_language_patterns(conversacion_texts)

        # Crear o actualizar perfil
        if not perfil:
            perfil = PerfilUsuario(usuario_id=usuario_id)

        perfil.preferencias_conversacionales = json.dumps({
            'nivel_formalidad': vocab_level,
            'directness': directness
        }, ensure_ascii=False)

        perfil.temas_sensibles = json.dumps([t['tema'] for t in sensibles], ensure_ascii=False)

        perfil.patrones_lenguaje_favoritos = json.dumps(
            language_patterns['favorite_expressions'],
            ensure_ascii=False
        )

        perfil.historial_temas_recurrentes = json.dumps(
            temas_recurrentes,
            ensure_ascii=False,
            default=str
        )

        perfil.emociones_primarias_frecuentes = json.dumps(
            emociones_dict,
            ensure_ascii=False
        )

        perfil.fecha_actualizacion = datetime.utcnow()

        db.add(perfil)
        db.commit()

        return perfil

    def _detect_vocabulary_level(self, texts: List[str]) -> str:
        """Detecta el nivel de vocabulario (simple, moderate, formal)."""
        if not texts:
            return 'moderate'

        combined = ' '.join(texts).lower()
        formal_words = ['así mismo', 'no obstante', 'puesto que', 'conclusión']
        formal_count = sum(combined.count(word) for word in formal_words)

        if formal_count > 10:
            return 'formal'
        elif len(texts) > 20 and sum(len(t.split()) for t in texts) / len(texts) > 12:
            return 'formal'
        else:
            return 'casual'

    def _detect_directness(self, texts: List[str]) -> str:
        """Detecta si el usuario es directo o más empático."""
        if not texts:
            return 'moderate'

        combined = ' '.join(texts).lower()

        # Palabras que indican estilo directo
        direct_words = ['necesito', 'quiero', 'puedo', 'voy a', 'tengo que']
        direct_count = sum(combined.count(word) for word in direct_words)

        # Palabras que indican estilo empático
        empathetic_words = ['creo que', 'siento que', 'parece que', 'podría']
        empathetic_count = sum(combined.count(word) for word in empathetic_words)

        if direct_count > empathetic_count * 1.5:
            return 'directo'
        elif empathetic_count > direct_count * 1.5:
            return 'empático'
        else:
            return 'equilibrado'

    def _identify_sensitive_topics(
        self,
        db: Session,
        usuario_id: int
    ) -> List[Dict]:
        """
        Identifica temas que tienden a estar asociados con ánimos bajos.
        """
        # Obtener conversaciones con ánimos bajos
        low_mood_states = db.query(EstadoAnimo).filter(
            and_(
                EstadoAnimo.usuario_id == usuario_id,
                EstadoAnimo.nivel <= 4
            )
        ).all()

        if not low_mood_states:
            return []

        # Buscar temas comunes en momentos de bajo ánimo
        sensibles = defaultdict(int)

        for mood in low_mood_states:
            if mood.notas_texto:
                texto_lower = mood.notas_texto.lower()

                temas = ['trabajo', 'pareja', 'familia', 'salud', 'soledad', 'fracaso']
                for tema in temas:
                    if tema in texto_lower:
                        sensibles[tema] += 1

        # Retornar temas que aparecen en 30%+ de ánimos bajos
        threshold = max(1, len(low_mood_states) // 3)

        return [
            {'tema': tema, 'apariciones': count}
            for tema, count in sensibles.items()
            if count >= threshold
        ]

    def get_long_term_context(
        self,
        db: Session,
        usuario_id: int,
        num_summaries: int = 3
    ) -> str:
        """
        Obtiene contexto histórico de largo plazo basado en resúmenes previos.
        Útil para incluir en el prompt de Claude.

        Returns:
            Texto de contexto histórico formateado
        """
        resumenes = db.query(ResumenConversacion).filter(
            ResumenConversacion.usuario_id == usuario_id
        ).order_by(desc(ResumenConversacion.fecha_resumen)).limit(num_summaries).all()

        if not resumenes:
            return ""

        contexto = "### CONTEXTO HISTÓRICO DE CONVERSACIONES PREVIAS\n\n"

        for resumen in reversed(resumenes):
            contexto += f"**Período: {resumen.periodo_inicio.strftime('%d/%m/%Y')} - {resumen.periodo_fin.strftime('%d/%m/%Y')}**\n"
            contexto += f"{resumen.resumen_texto}\n\n"

        return contexto


# Instancia global del servicio
memory_service = ConversationalMemoryService()
