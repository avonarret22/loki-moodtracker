"""
Servicio de Memoria Emocional Mejorada para Loki.
Recuerda no solo QUÉ dijeron los usuarios, sino CÓMO se sentían.
"""

from typing import Dict, List, Optional, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import func, desc, and_
from datetime import datetime, timedelta
from collections import defaultdict
import json

from app.models.mood import (
    Usuario, ConversacionContexto, EstadoAnimo, 
    RegistroHabito, Habito
)
from app.core.logger import setup_logger

logger = setup_logger(__name__)


class EmotionalMemory:
    """
    Representa un recuerdo emocional específico.
    """
    def __init__(
        self,
        tema: str,
        sentimiento: str,
        intensidad: int,
        fecha: datetime,
        contexto: str,
        usuario_mensaje: str = None
    ):
        self.tema = tema
        self.sentimiento = sentimiento
        self.intensidad = intensidad  # 1-10
        self.fecha = fecha
        self.contexto = contexto
        self.usuario_mensaje = usuario_mensaje

    def to_dict(self) -> Dict:
        return {
            'tema': self.tema,
            'sentimiento': self.sentimiento,
            'intensidad': self.intensidad,
            'fecha': self.fecha.isoformat() if isinstance(self.fecha, datetime) else self.fecha,
            'contexto': self.contexto,
            'usuario_mensaje': self.usuario_mensaje
        }

    @classmethod
    def from_dict(cls, data: Dict) -> 'EmotionalMemory':
        fecha = data['fecha']
        if isinstance(fecha, str):
            fecha = datetime.fromisoformat(fecha)
        
        return cls(
            tema=data['tema'],
            sentimiento=data['sentimiento'],
            intensidad=data['intensidad'],
            fecha=fecha,
            contexto=data['contexto'],
            usuario_mensaje=data.get('usuario_mensaje')
        )


class EmotionalMemoryService:
    """
    Gestiona la memoria emocional de Loki.
    Recuerda conversaciones importantes con su contexto emocional.
    """

    # Palabras clave para detectar temas
    TOPIC_KEYWORDS = {
        'trabajo': ['trabajo', 'jefe', 'proyecto', 'reunión', 'laboral', 'carrera', 'oficina', 'compañero', 'cliente'],
        'pareja': ['pareja', 'novia', 'novio', 'esposa', 'esposo', 'relación', 'amor', 'pelea pareja'],
        'familia': ['familia', 'mamá', 'papá', 'hermano', 'hermana', 'hijo', 'hija', 'padres', 'familiar'],
        'amistades': ['amigo', 'amiga', 'amigos', 'amistad', 'salir', 'reunión social'],
        'salud': ['salud', 'enfermo', 'médico', 'doctor', 'dolor', 'síntoma', 'hospital', 'medicina'],
        'dinero': ['dinero', 'plata', 'deuda', 'pago', 'cuenta', 'financiero', 'económico', 'sueldo'],
        'estudios': ['estudio', 'universidad', 'examen', 'clase', 'tarea', 'profesor', 'carrera'],
        'hogar': ['casa', 'hogar', 'mudanza', 'renta', 'vecino', 'departamento'],
        'metas': ['meta', 'objetivo', 'quiero', 'aspiración', 'sueño', 'lograr', 'conseguir'],
        'pasatiempos': ['hobby', 'leer', 'música', 'juego', 'deporte', 'ejercicio', 'correr', 'gym'],
    }

    # Palabras clave para detectar sentimientos
    FEELING_KEYWORDS = {
        'feliz': ['feliz', 'alegre', 'contento', 'bien', 'genial', 'excelente', 'increíble', 'maravilloso'],
        'triste': ['triste', 'deprimido', 'mal', 'bajón', 'desanimado', 'apagado'],
        'ansioso': ['ansioso', 'nervioso', 'preocupado', 'inquieto', 'angustiado', 'tenso'],
        'estresado': ['estrés', 'estresado', 'presión', 'agobiado', 'abrumado', 'sobrecargado'],
        'enojado': ['enojado', 'furioso', 'molesto', 'irritado', 'rabia', 'ira', 'frustrado'],
        'cansado': ['cansado', 'agotado', 'exhausto', 'rendido', 'sin energía'],
        'motivado': ['motivado', 'animado', 'entusiasmado', 'energético', 'con ganas'],
        'confundido': ['confundido', 'perdido', 'indeciso', 'no sé', 'duda'],
        'solo': ['solo', 'solitario', 'aislado', 'abandonado'],
        'tranquilo': ['tranquilo', 'calmado', 'sereno', 'paz', 'relajado'],
    }

    def __init__(self):
        self.max_memories_per_user = 50  # Máximo de recuerdos a mantener
        self.significant_threshold = 6  # Intensidad mínima para guardar (1-10)

    def extract_emotional_memory(
        self,
        db: Session,
        usuario_id: int,
        mensaje: str,
        mood_level: Optional[int] = None
    ) -> Optional[EmotionalMemory]:
        """
        Extrae un recuerdo emocional de un mensaje.
        
        Args:
            db: Sesión de base de datos
            usuario_id: ID del usuario
            mensaje: Mensaje del usuario
            mood_level: Nivel de ánimo actual (1-10) si fue registrado
            
        Returns:
            EmotionalMemory si el mensaje es significativo, None si no
        """
        # Detectar tema principal
        tema = self._detect_topic(mensaje)
        
        # Detectar sentimiento principal
        sentimiento, intensidad_estimada = self._detect_feeling(mensaje, mood_level)
        
        # Si es muy leve o neutro, no guardar
        if intensidad_estimada < self.significant_threshold:
            return None
        
        # Crear recuerdo emocional
        memory = EmotionalMemory(
            tema=tema,
            sentimiento=sentimiento,
            intensidad=intensidad_estimada,
            fecha=datetime.now(),
            contexto=self._extract_context(mensaje),
            usuario_mensaje=mensaje[:200]  # Guardar primeros 200 chars
        )
        
        logger.info(f"💭 Recuerdo emocional creado: {tema} - {sentimiento} ({intensidad_estimada}/10)")
        return memory

    def _detect_topic(self, mensaje: str) -> str:
        """
        Detecta el tema principal del mensaje.
        """
        mensaje_lower = mensaje.lower()
        
        # Buscar coincidencias con keywords
        topic_scores = defaultdict(int)
        
        for topic, keywords in self.TOPIC_KEYWORDS.items():
            for keyword in keywords:
                if keyword in mensaje_lower:
                    topic_scores[topic] += 1
        
        # Retornar tema con más coincidencias, o 'general' si no hay
        if topic_scores:
            return max(topic_scores.items(), key=lambda x: x[1])[0]
        return 'general'

    def _detect_feeling(self, mensaje: str, mood_level: Optional[int] = None) -> Tuple[str, int]:
        """
        Detecta el sentimiento principal y su intensidad.
        
        Returns:
            Tupla (sentimiento, intensidad)
        """
        mensaje_lower = mensaje.lower()
        
        # Buscar coincidencias con keywords de sentimientos
        feeling_scores = defaultdict(int)
        
        for feeling, keywords in self.FEELING_KEYWORDS.items():
            for keyword in keywords:
                if keyword in mensaje_lower:
                    feeling_scores[feeling] += 1
        
        # Determinar sentimiento principal
        sentimiento = 'neutro'
        if feeling_scores:
            sentimiento = max(feeling_scores.items(), key=lambda x: x[1])[0]
        
        # Estimar intensidad
        intensidad = mood_level if mood_level else self._estimate_intensity(mensaje_lower, sentimiento)
        
        return sentimiento, intensidad

    def _estimate_intensity(self, mensaje_lower: str, sentimiento: str) -> int:
        """
        Estima la intensidad del sentimiento (1-10) basándose en intensificadores.
        """
        # Intensificadores
        muy_intenso = ['muy', 'súper', 'extremadamente', 'demasiado', 'totalmente']
        intenso = ['bastante', 'bien', 'realmente', 'verdaderamente']
        moderado = ['algo', 'un poco', 'medio']
        
        base_intensity = 5  # Default
        
        # Ajustar según intensificadores
        for word in muy_intenso:
            if word in mensaje_lower:
                base_intensity += 3
                break
        
        for word in intenso:
            if word in mensaje_lower:
                base_intensity += 2
                break
        
        for word in moderado:
            if word in mensaje_lower:
                base_intensity -= 1
                break
        
        # Signos de exclamación/interrogación aumentan intensidad
        if '!' in mensaje_lower:
            base_intensity += 1
        if '!!' in mensaje_lower:
            base_intensity += 2
        
        # Caps lock indica intensidad
        if any(c.isupper() for c in mensaje_lower):
            base_intensity += 1
        
        # Clamp entre 1-10
        return max(1, min(10, base_intensity))

    def _extract_context(self, mensaje: str) -> str:
        """
        Extrae contexto clave del mensaje (máximo 100 caracteres).
        """
        # Tomar primera oración o primeros 100 caracteres
        primera_oracion = mensaje.split('.')[0]
        contexto = primera_oracion[:100]
        
        if len(primera_oracion) > 100:
            contexto += '...'
        
        return contexto

    def save_memory(
        self,
        db: Session,
        usuario_id: int,
        memory: EmotionalMemory
    ) -> None:
        """
        Guarda un recuerdo emocional en el perfil del usuario.
        """
        from app.models.mood import PerfilUsuario
        
        # Obtener o crear perfil
        perfil = db.query(PerfilUsuario).filter(
            PerfilUsuario.usuario_id == usuario_id
        ).first()
        
        if not perfil:
            perfil = PerfilUsuario(
                usuario_id=usuario_id,
                temas_frecuentes='{}',
                sentimientos_comunes='{}',
                memoria_emocional='[]'
            )
            db.add(perfil)
        
        # Obtener recuerdos existentes
        try:
            recuerdos = json.loads(perfil.memoria_emocional or '[]')
        except:
            recuerdos = []
        
        # Agregar nuevo recuerdo
        recuerdos.append(memory.to_dict())
        
        # Mantener solo los últimos N recuerdos más significativos
        recuerdos = sorted(
            recuerdos,
            key=lambda x: (x['intensidad'], x['fecha']),
            reverse=True
        )[:self.max_memories_per_user]
        
        # Guardar
        perfil.memoria_emocional = json.dumps(recuerdos, ensure_ascii=False)
        db.commit()
        
        logger.info(f"💾 Recuerdo guardado para usuario {usuario_id} (total: {len(recuerdos)})")

    def get_memories_by_topic(
        self,
        db: Session,
        usuario_id: int,
        tema: str,
        limit: int = 5
    ) -> List[EmotionalMemory]:
        """
        Obtiene recuerdos relacionados con un tema específico.
        """
        from app.models.mood import PerfilUsuario
        
        perfil = db.query(PerfilUsuario).filter(
            PerfilUsuario.usuario_id == usuario_id
        ).first()
        
        if not perfil or not perfil.memoria_emocional:
            return []
        
        try:
            recuerdos = json.loads(perfil.memoria_emocional)
        except:
            return []
        
        # Filtrar por tema
        recuerdos_tema = [
            EmotionalMemory.from_dict(r) 
            for r in recuerdos 
            if r['tema'] == tema
        ]
        
        # Ordenar por fecha (más recientes primero)
        recuerdos_tema.sort(key=lambda x: x.fecha, reverse=True)
        
        return recuerdos_tema[:limit]

    def get_recent_memories(
        self,
        db: Session,
        usuario_id: int,
        days: int = 7,
        limit: int = 10
    ) -> List[EmotionalMemory]:
        """
        Obtiene recuerdos recientes de los últimos N días.
        """
        from app.models.mood import PerfilUsuario
        
        perfil = db.query(PerfilUsuario).filter(
            PerfilUsuario.usuario_id == usuario_id
        ).first()
        
        if not perfil or not perfil.memoria_emocional:
            return []
        
        try:
            recuerdos = json.loads(perfil.memoria_emocional)
        except:
            return []
        
        # Filtrar por fecha
        cutoff_date = datetime.now() - timedelta(days=days)
        
        recuerdos_recientes = []
        for r in recuerdos:
            fecha = datetime.fromisoformat(r['fecha']) if isinstance(r['fecha'], str) else r['fecha']
            if fecha >= cutoff_date:
                recuerdos_recientes.append(EmotionalMemory.from_dict(r))
        
        # Ordenar por fecha (más recientes primero)
        recuerdos_recientes.sort(key=lambda x: x.fecha, reverse=True)
        
        return recuerdos_recientes[:limit]

    def find_similar_memories(
        self,
        db: Session,
        usuario_id: int,
        sentimiento: str,
        limit: int = 3
    ) -> List[EmotionalMemory]:
        """
        Encuentra recuerdos con sentimientos similares.
        Útil para hacer conexiones: "Esto es parecido a cuando..."
        """
        from app.models.mood import PerfilUsuario
        
        perfil = db.query(PerfilUsuario).filter(
            PerfilUsuario.usuario_id == usuario_id
        ).first()
        
        if not perfil or not perfil.memoria_emocional:
            return []
        
        try:
            recuerdos = json.loads(perfil.memoria_emocional)
        except:
            return []
        
        # Filtrar por sentimiento
        recuerdos_similares = [
            EmotionalMemory.from_dict(r) 
            for r in recuerdos 
            if r['sentimiento'] == sentimiento
        ]
        
        # Ordenar por intensidad (más intensos primero)
        recuerdos_similares.sort(key=lambda x: x.intensidad, reverse=True)
        
        return recuerdos_similares[:limit]

    def generate_memory_context(
        self,
        db: Session,
        usuario_id: int,
        current_topic: Optional[str] = None
    ) -> str:
        """
        Genera un contexto narrativo de recuerdos para incluir en el prompt.
        
        Returns:
            String con recuerdos relevantes en lenguaje natural
        """
        context_parts = []
        
        # Recuerdos recientes (última semana)
        recent = self.get_recent_memories(db, usuario_id, days=7, limit=3)
        if recent:
            context_parts.append("### RECUERDOS RECIENTES:")
            for mem in recent:
                dias = (datetime.now() - mem.fecha).days
                tiempo = f"hace {dias} días" if dias > 0 else "hoy"
                context_parts.append(
                    f"- {tiempo.capitalize()}: {mem.tema} - se sentía {mem.sentimiento} "
                    f"({mem.intensidad}/10). Contexto: {mem.contexto}"
                )
        
        # Recuerdos sobre el tema actual (si hay)
        if current_topic:
            topic_memories = self.get_memories_by_topic(db, usuario_id, current_topic, limit=2)
            if topic_memories:
                context_parts.append(f"\n### RECUERDOS SOBRE '{current_topic.upper()}':")
                for mem in topic_memories:
                    dias = (datetime.now() - mem.fecha).days
                    tiempo = f"hace {dias} días" if dias > 0 else "hoy"
                    context_parts.append(
                        f"- {tiempo.capitalize()}: {mem.sentimiento} ({mem.intensidad}/10) - {mem.contexto}"
                    )
        
        return "\n".join(context_parts) if context_parts else ""


# Instancia global del servicio
emotional_memory_service = EmotionalMemoryService()
