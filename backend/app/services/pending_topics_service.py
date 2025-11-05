"""
Servicio de Proactividad Contextual para LokiMood.

Este servicio detecta temas mencionados pero no elaborados, y genera
seguimientos naturales en conversaciones futuras.

Funcionalidades:
- Detectar menciones breves de temas sin desarrollo
- Rastrear tópicos pendientes por usuario
- Generar preguntas de seguimiento contextuales
- Priorizar qué temas vale la pena retomar
- Detectar cuándo es apropiado hacer seguimiento

Autor: Sistema LokiMood
Fecha: 2024
"""

from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import desc
import logging
import json
import re

from app.models.mood import EstadoAnimo, Usuario

logger = logging.getLogger(__name__)


# ============================================================================
# CONFIGURACIÓN
# ============================================================================

# Palabras clave que indican un tema pendiente (menciones sin elaboración)
PENDING_INDICATORS = [
    r'\btengo que\b',
    r'\bvoy a\b', 
    r'\bdebo\b',
    r'\bquiero\b',
    r'\bplaneo\b',
    r'\bpensando en\b',
    r'\btal vez\b',
    r'\ba ver si\b',
    r'\bintentaré\b',
    r'\bver[ée] si\b',
]

# Palabras clave que indican resolución de un tema
RESOLUTION_INDICATORS = [
    r'\blo hice\b',
    r'\bya lo\b',
    r'\btermin[eé]\b',
    r'\bcomplet[eé]\b',
    r'\bresol[víĺ]\b',
    r'\bsali[óo] bien\b',
    r'\bsali[óo] mal\b',
    r'\bno pude\b',
    r'\bno funcion[óo]\b',
]

# Categorías de tópicos para clasificación
TOPIC_CATEGORIES = {
    'trabajo': ['trabajo', 'jefe', 'oficina', 'proyecto', 'reunión', 'cliente', 'colega'],
    'relaciones': ['pareja', 'novi[oa]', 'amig[oa]', 'familia', 'mamá', 'papá', 'herman[oa]'],
    'salud': ['doctor', 'médico', 'cita', 'salud', 'ejercicio', 'gym', 'terapia'],
    'personal': ['curso', 'estudiar', 'aprender', 'leer', 'hobby', 'proyecto personal'],
    'tareas': ['pagar', 'llamar', 'enviar', 'comprar', 'arreglar', 'hacer'],
}

# Días máximos para considerar un tema como "reciente"
MAX_DAYS_RECENT = 7

# Días mínimos antes de hacer seguimiento
MIN_DAYS_BEFORE_FOLLOWUP = 1

# Número máximo de tópicos pendientes a rastrear por usuario
MAX_PENDING_TOPICS = 10


# ============================================================================
# MODELOS DE DATOS
# ============================================================================

@dataclass
class PendingTopic:
    """Representa un tema pendiente de seguimiento."""
    topic_id: str  # Hash único del tópico
    usuario_id: int
    texto_original: str  # Texto donde se mencionó
    tema_extraido: str  # Tema extraído (ej: "ir al doctor")
    categoria: str  # trabajo, relaciones, salud, personal, tareas
    fecha_mencion: datetime
    prioridad: int  # 1-10, basado en contexto emocional
    estado: str  # 'pendiente', 'seguimiento_hecho', 'resuelto', 'abandonado'
    dias_desde_mencion: int
    metadata: Dict[str, Any]  # Info adicional
    
    def to_dict(self) -> Dict[str, Any]:
        """Convierte a diccionario para almacenamiento JSON."""
        return {
            'topic_id': self.topic_id,
            'usuario_id': self.usuario_id,
            'texto_original': self.texto_original,
            'tema_extraido': self.tema_extraido,
            'categoria': self.categoria,
            'fecha_mencion': self.fecha_mencion.isoformat(),
            'prioridad': self.prioridad,
            'estado': self.estado,
            'dias_desde_mencion': self.dias_desde_mencion,
            'metadata': self.metadata,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'PendingTopic':
        """Crea instancia desde diccionario."""
        data['fecha_mencion'] = datetime.fromisoformat(data['fecha_mencion'])
        return cls(**data)


# ============================================================================
# SERVICIO PRINCIPAL
# ============================================================================

class PendingTopicsService:
    """
    Servicio para detectar y gestionar temas pendientes de seguimiento.
    """
    
    def __init__(self):
        self.pending_indicators_regex = [re.compile(pattern, re.IGNORECASE) 
                                        for pattern in PENDING_INDICATORS]
        self.resolution_indicators_regex = [re.compile(pattern, re.IGNORECASE)
                                           for pattern in RESOLUTION_INDICATORS]
    
    # ========================================================================
    # DETECCIÓN DE TEMAS PENDIENTES
    # ========================================================================
    
    def detect_pending_topics(
        self,
        db: Session,
        usuario_id: int,
        mensaje_usuario: str,
        mood_score: Optional[int] = None
    ) -> List[PendingTopic]:
        """
        Detecta temas pendientes mencionados en el mensaje del usuario.
        
        Args:
            db: Sesión de base de datos
            usuario_id: ID del usuario
            mensaje_usuario: Mensaje actual del usuario
            mood_score: Puntuación de ánimo (0-10) para priorización
            
        Returns:
            Lista de temas pendientes detectados
        """
        try:
            topics_detectados = []
            
            # Verificar si hay indicadores de temas pendientes
            tiene_indicador = any(
                regex.search(mensaje_usuario)
                for regex in self.pending_indicators_regex
            )
            
            if not tiene_indicador:
                return []
            
            # Extraer oraciones con indicadores
            oraciones = self._extract_sentences_with_indicators(mensaje_usuario)
            
            for oracion in oraciones:
                # Extraer el tema específico
                tema = self._extract_topic_from_sentence(oracion)
                
                if not tema:
                    continue
                
                # Clasificar categoría
                categoria = self._classify_topic(tema)
                
                # Calcular prioridad
                prioridad = self._calculate_priority(
                    tema, oracion, mood_score, categoria
                )
                
                # Generar ID único
                topic_id = self._generate_topic_id(usuario_id, tema)
                
                # Crear objeto PendingTopic
                topic = PendingTopic(
                    topic_id=topic_id,
                    usuario_id=usuario_id,
                    texto_original=oracion,
                    tema_extraido=tema,
                    categoria=categoria,
                    fecha_mencion=datetime.utcnow(),
                    prioridad=prioridad,
                    estado='pendiente',
                    dias_desde_mencion=0,
                    metadata={
                        'mood_score': mood_score,
                        'mensaje_completo': mensaje_usuario[:200],  # Primeros 200 chars
                    }
                )
                
                topics_detectados.append(topic)
                logger.info(f"🎯 Tema pendiente detectado: {tema} (prioridad: {prioridad})")
            
            return topics_detectados
            
        except Exception as e:
            logger.error(f"Error detectando temas pendientes: {e}", exc_info=True)
            return []
    
    def _extract_sentences_with_indicators(self, texto: str) -> List[str]:
        """Extrae oraciones que contienen indicadores de temas pendientes."""
        # Dividir en oraciones (simple, basado en puntos)
        oraciones = [s.strip() for s in texto.split('.') if s.strip()]
        
        # Filtrar oraciones con indicadores
        oraciones_relevantes = []
        for oracion in oraciones:
            if any(regex.search(oracion) for regex in self.pending_indicators_regex):
                oraciones_relevantes.append(oracion)
        
        return oraciones_relevantes
    
    def _extract_topic_from_sentence(self, oracion: str) -> Optional[str]:
        """
        Extrae el tema específico de una oración.
        Esto es simplificado; idealmente usaría NLP más sofisticado.
        """
        # Patrones para extraer el tema después del indicador
        patterns = [
            r'(?:tengo que|debo|voy a|quiero|planeo)\s+(.+)',
            r'(?:pensando en|intentaré|ver[ée] si)\s+(.+)',
            r'(?:tal vez|a ver si)\s+(.+)',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, oracion, re.IGNORECASE)
            if match:
                tema = match.group(1).strip()
                # Limpiar y limitar longitud
                tema = tema[:100]
                return tema
        
        return None
    
    def _classify_topic(self, tema: str) -> str:
        """Clasifica el tema en una categoría."""
        tema_lower = tema.lower()
        
        for categoria, keywords in TOPIC_CATEGORIES.items():
            for keyword in keywords:
                if re.search(r'\b' + keyword + r'\b', tema_lower):
                    return categoria
        
        return 'general'
    
    def _calculate_priority(
        self,
        tema: str,
        oracion: str,
        mood_score: Optional[int],
        categoria: str
    ) -> int:
        """
        Calcula la prioridad del tema (1-10).
        
        Factores:
        - Mood bajo = mayor prioridad
        - Categorías importantes (salud, relaciones) = mayor prioridad
        - Palabras de urgencia = mayor prioridad
        """
        prioridad = 5  # Base
        
        # Factor 1: Mood score
        if mood_score is not None:
            if mood_score <= 3:
                prioridad += 3
            elif mood_score <= 5:
                prioridad += 2
            elif mood_score <= 7:
                prioridad += 1
        
        # Factor 2: Categoría
        if categoria in ['salud', 'relaciones']:
            prioridad += 2
        elif categoria in ['trabajo', 'personal']:
            prioridad += 1
        
        # Factor 3: Palabras de urgencia
        urgency_words = ['urgente', 'importante', 'necesito', 'pronto', 'ya']
        if any(word in oracion.lower() for word in urgency_words):
            prioridad += 2
        
        # Limitar a rango 1-10
        return max(1, min(10, prioridad))
    
    def _generate_topic_id(self, usuario_id: int, tema: str) -> str:
        """Genera un ID único para el tema."""
        import hashlib
        content = f"{usuario_id}_{tema}_{datetime.utcnow().date()}"
        return hashlib.md5(content.encode()).hexdigest()[:12]
    
    # ========================================================================
    # ALMACENAMIENTO Y RECUPERACIÓN
    # ========================================================================
    
    def save_pending_topics(
        self,
        db: Session,
        usuario_id: int,
        topics: List[PendingTopic]
    ) -> bool:
        """
        Guarda temas pendientes en el perfil del usuario.
        """
        try:
            from app.models.mood import PerfilUsuario
            
            # Obtener perfil
            perfil = db.query(PerfilUsuario).filter(
                PerfilUsuario.usuario_id == usuario_id
            ).first()
            
            if not perfil:
                logger.warning(f"No se encontró perfil para usuario {usuario_id}")
                return False
            
            # Cargar tópicos existentes
            existing_topics = []
            if perfil.topics_pendientes:
                try:
                    existing_topics = [
                        PendingTopic.from_dict(t)
                        for t in json.loads(perfil.topics_pendientes)
                    ]
                except json.JSONDecodeError:
                    logger.error("Error decodificando topics_pendientes existentes")
            
            # Agregar nuevos topics (evitar duplicados)
            existing_ids = {t.topic_id for t in existing_topics}
            for topic in topics:
                if topic.topic_id not in existing_ids:
                    existing_topics.append(topic)
            
            # Limitar a MAX_PENDING_TOPICS (ordenar por prioridad)
            existing_topics.sort(key=lambda t: t.prioridad, reverse=True)
            existing_topics = existing_topics[:MAX_PENDING_TOPICS]
            
            # Guardar
            perfil.topics_pendientes = json.dumps([t.to_dict() for t in existing_topics])
            db.commit()
            
            logger.info(f"💾 Guardados {len(topics)} temas pendientes para usuario {usuario_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error guardando temas pendientes: {e}", exc_info=True)
            db.rollback()
            return False
    
    def get_pending_topics(
        self,
        db: Session,
        usuario_id: int,
        only_active: bool = True
    ) -> List[PendingTopic]:
        """
        Recupera temas pendientes del usuario.
        
        Args:
            db: Sesión de base de datos
            usuario_id: ID del usuario
            only_active: Si True, solo devuelve temas en estado 'pendiente'
            
        Returns:
            Lista de temas pendientes
        """
        try:
            from app.models.mood import PerfilUsuario
            
            perfil = db.query(PerfilUsuario).filter(
                PerfilUsuario.usuario_id == usuario_id
            ).first()
            
            if not perfil or not perfil.topics_pendientes:
                return []
            
            topics = [
                PendingTopic.from_dict(t)
                for t in json.loads(perfil.topics_pendientes)
            ]
            
            # Actualizar días desde mención
            now = datetime.utcnow()
            for topic in topics:
                topic.dias_desde_mencion = (now - topic.fecha_mencion).days
            
            # Filtrar por estado si se solicita
            if only_active:
                topics = [t for t in topics if t.estado == 'pendiente']
            
            # Ordenar por prioridad
            topics.sort(key=lambda t: t.prioridad, reverse=True)
            
            return topics
            
        except Exception as e:
            logger.error(f"Error recuperando temas pendientes: {e}", exc_info=True)
            return []
    
    # ========================================================================
    # DETECCIÓN DE RESOLUCIONES
    # ========================================================================
    
    def check_topic_resolutions(
        self,
        db: Session,
        usuario_id: int,
        mensaje_usuario: str
    ) -> List[PendingTopic]:
        """
        Verifica si el mensaje actual resuelve algún tema pendiente.
        
        Returns:
            Lista de temas que fueron resueltos
        """
        try:
            pending_topics = self.get_pending_topics(db, usuario_id, only_active=True)
            
            if not pending_topics:
                return []
            
            resolved_topics = []
            
            # Verificar indicadores de resolución
            tiene_resolucion = any(
                regex.search(mensaje_usuario)
                for regex in self.resolution_indicators_regex
            )
            
            if not tiene_resolucion:
                return []
            
            # Buscar coincidencias entre temas pendientes y mensaje
            for topic in pending_topics:
                # Extraer palabras clave del tema
                keywords = self._extract_keywords(topic.tema_extraido)
                
                # Verificar si el mensaje menciona el tema
                tema_mencionado = any(
                    keyword.lower() in mensaje_usuario.lower()
                    for keyword in keywords
                )
                
                if tema_mencionado:
                    topic.estado = 'resuelto'
                    resolved_topics.append(topic)
                    logger.info(f"✅ Tema resuelto: {topic.tema_extraido}")
            
            # Actualizar en base de datos
            if resolved_topics:
                self._update_topic_states(db, usuario_id, pending_topics)
            
            return resolved_topics
            
        except Exception as e:
            logger.error(f"Error verificando resoluciones: {e}", exc_info=True)
            return []
    
    def _extract_keywords(self, tema: str) -> List[str]:
        """Extrae palabras clave significativas del tema."""
        # Palabras a ignorar
        stopwords = {'el', 'la', 'los', 'las', 'un', 'una', 'de', 'a', 'en', 'con', 'para'}
        
        # Dividir y limpiar
        words = tema.lower().split()
        keywords = [w for w in words if w not in stopwords and len(w) > 3]
        
        return keywords[:5]  # Máximo 5 keywords
    
    def _update_topic_states(
        self,
        db: Session,
        usuario_id: int,
        topics: List[PendingTopic]
    ) -> None:
        """Actualiza los estados de los temas en la base de datos."""
        try:
            from app.models.mood import PerfilUsuario
            
            perfil = db.query(PerfilUsuario).filter(
                PerfilUsuario.usuario_id == usuario_id
            ).first()
            
            if perfil:
                perfil.topics_pendientes = json.dumps([t.to_dict() for t in topics])
                db.commit()
                
        except Exception as e:
            logger.error(f"Error actualizando estados de temas: {e}", exc_info=True)
            db.rollback()
    
    # ========================================================================
    # GENERACIÓN DE SEGUIMIENTOS
    # ========================================================================
    
    def get_followup_suggestions(
        self,
        db: Session,
        usuario_id: int,
        nivel_confianza: int = 1
    ) -> Optional[str]:
        """
        Genera sugerencias de seguimiento para temas pendientes.
        
        Args:
            db: Sesión de base de datos
            usuario_id: ID del usuario
            nivel_confianza: Nivel de confianza (1-5)
            
        Returns:
            Contexto de seguimiento para agregar al prompt, o None
        """
        try:
            topics = self.get_pending_topics(db, usuario_id, only_active=True)
            
            if not topics:
                return None
            
            # Filtrar temas que cumplan condiciones para seguimiento
            followup_topics = [
                t for t in topics
                if t.dias_desde_mencion >= MIN_DAYS_BEFORE_FOLLOWUP
                and t.dias_desde_mencion <= MAX_DAYS_RECENT
            ]
            
            if not followup_topics:
                return None
            
            # Tomar el de mayor prioridad
            top_topic = followup_topics[0]
            
            # Generar contexto según nivel de confianza
            context = self._generate_followup_context(top_topic, nivel_confianza)
            
            return context
            
        except Exception as e:
            logger.error(f"Error generando seguimientos: {e}", exc_info=True)
            return None
    
    def _generate_followup_context(
        self,
        topic: PendingTopic,
        nivel_confianza: int
    ) -> str:
        """Genera el contexto de seguimiento para el prompt."""
        dias = topic.dias_desde_mencion
        tiempo_desc = f"hace {dias} día{'s' if dias > 1 else ''}"
        
        # Adaptar tono según confianza
        if nivel_confianza <= 2:
            # Tono sutil y opcional
            context = f"""
### TEMA PENDIENTE (OPCIONAL - solo mencionar si es relevante al contexto):
{tiempo_desc} el usuario mencionó: "{topic.tema_extraido}"
Categoría: {topic.categoria}
Si es natural en la conversación, podrías preguntar cómo le fue.
⚠️ NO fuerces el tema si están hablando de otra cosa.
"""
        else:
            # Tono más directo
            context = f"""
### SEGUIMIENTO CONTEXTUAL:
{tiempo_desc} el usuario mencionó: "{topic.tema_extraido}"
Categoría: {topic.categoria}
Prioridad: {topic.prioridad}/10

Puedes hacer seguimiento de forma natural, por ejemplo:
- "Por cierto, {tiempo_desc} mencionaste {topic.tema_extraido}. ¿Cómo te fue?"
- "Me acordé que querías {topic.tema_extraido}. ¿Lo hiciste?"

⚠️ IMPORTANTE: Solo pregunta si es relevante al momento. No interrumpas si están en otro tema.
"""
        
        return context.strip()


# ============================================================================
# INSTANCIA SINGLETON
# ============================================================================

pending_topics_service = PendingTopicsService()
