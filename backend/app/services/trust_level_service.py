"""
Servicio para gestionar los niveles de confianza entre Loki y el usuario.
El nivel de confianza determina cómo Loki se comunica: de reservado a cercano.
"""
from sqlalchemy.orm import Session
from app.models.mood import Usuario
from typing import Dict, Optional


class TrustLevelService:
    """
    Gestiona los niveles de confianza basados en la cantidad de interacciones.

    Niveles:
    1. Conociendo (1-10 mensajes): Reservado, educado, preguntas básicas
    2. Estableciendo (11-30 mensajes): Más cercano, recuerda cosas, menos formal
    3. Construyendo (31-60 mensajes): Confidente, hace conexiones, sugiere patterns
    4. Consolidado (61-100 mensajes): Amigo cercano, humor apropiado, lee entre líneas
    5. Íntimo (100+ mensajes): Profundo entendimiento, anticipa necesidades, honesto directo
    """

    TRUST_LEVELS = {
        1: {
            'name': 'Conociendo',
            'range': (1, 10),
            'description': 'Primeras interacciones, estableciendo contacto',
            'max_sentences': 1,
            'tone': 'reservado, educado, sin asumir',
            'approach': 'preguntas básicas, validación simple'
        },
        2: {
            'name': 'Estableciendo',
            'range': (11, 30),
            'description': 'Empezando a conocerse, recordando detalles',
            'max_sentences': 2,
            'tone': 'cercano, atento, menos formal',
            'approach': 'conexiones simples, recuerda interacciones pasadas'
        },
        3: {
            'name': 'Construyendo',
            'range': (31, 60),
            'description': 'Relación establecida, confianza mutua',
            'max_sentences': 2,
            'tone': 'confidente, observador, sugerente',
            'approach': 'identifica patterns, sugiere conexiones, más proactivo'
        },
        4: {
            'name': 'Consolidado',
            'range': (61, 100),
            'description': 'Amigo cercano que conoce bien al usuario',
            'max_sentences': 2,
            'tone': 'amigo cercano, humor apropiado, honesto',
            'approach': 'lee entre líneas, referencias compartidas, desafía constructivamente'
        },
        5: {
            'name': 'Íntimo',
            'range': (101, float('inf')),
            'description': 'Profundo entendimiento mutuo',
            'max_sentences': 3,
            'tone': 'directo, auténtico, intuitivo',
            'approach': 'anticipa necesidades, honestidad profunda, puede ser retador'
        }
    }

    def calculate_trust_level(self, total_interacciones: int) -> int:
        """
        Calcula el nivel de confianza basado en el número de interacciones.

        Args:
            total_interacciones: Número total de mensajes intercambiados

        Returns:
            Nivel de confianza (1-5)
        """
        if total_interacciones <= 10:
            return 1
        elif total_interacciones <= 30:
            return 2
        elif total_interacciones <= 60:
            return 3
        elif total_interacciones <= 100:
            return 4
        else:
            return 5

    def update_trust_level(self, db: Session, usuario_id: int) -> Dict:
        """
        Actualiza el nivel de confianza del usuario basado en sus interacciones.
        También incrementa el contador de interacciones.

        Args:
            db: Sesión de base de datos
            usuario_id: ID del usuario

        Returns:
            Diccionario con información del nivel de confianza actualizado
        """
        usuario = db.query(Usuario).filter(Usuario.id == usuario_id).first()
        if not usuario:
            return {'error': 'Usuario no encontrado'}

        # Incrementar contador de interacciones
        usuario.total_interacciones += 1

        # Calcular y actualizar nivel de confianza
        nivel_anterior = usuario.nivel_confianza
        nivel_nuevo = self.calculate_trust_level(usuario.total_interacciones)
        usuario.nivel_confianza = nivel_nuevo

        db.commit()

        # Detectar si hubo cambio de nivel (para celebrar o notificar)
        nivel_cambio = nivel_nuevo > nivel_anterior

        return {
            'usuario_id': usuario_id,
            'total_interacciones': usuario.total_interacciones,
            'nivel_confianza': nivel_nuevo,
            'nivel_anterior': nivel_anterior,
            'nivel_cambio': nivel_cambio,
            'nivel_info': self.get_trust_level_info(nivel_nuevo)
        }

    def get_trust_level_info(self, nivel: int) -> Dict:
        """
        Obtiene información detallada sobre un nivel de confianza.

        Args:
            nivel: Nivel de confianza (1-5)

        Returns:
            Diccionario con información del nivel
        """
        return self.TRUST_LEVELS.get(nivel, self.TRUST_LEVELS[1])

    def get_user_trust_info(self, db: Session, usuario_id: int) -> Optional[Dict]:
        """
        Obtiene información completa del nivel de confianza de un usuario.

        Args:
            db: Sesión de base de datos
            usuario_id: ID del usuario

        Returns:
            Diccionario con información completa o None si no existe
        """
        usuario = db.query(Usuario).filter(Usuario.id == usuario_id).first()
        if not usuario:
            return None

        nivel_info = self.get_trust_level_info(usuario.nivel_confianza)

        # Calcular progreso hacia el siguiente nivel
        next_level = min(usuario.nivel_confianza + 1, 5)
        next_level_threshold = self.TRUST_LEVELS[next_level]['range'][0]
        mensajes_hasta_siguiente = max(0, next_level_threshold - usuario.total_interacciones)

        return {
            'usuario_id': usuario_id,
            'total_interacciones': usuario.total_interacciones,
            'nivel_confianza': usuario.nivel_confianza,
            'nivel_nombre': nivel_info['name'],
            'nivel_descripcion': nivel_info['description'],
            'max_sentences': nivel_info['max_sentences'],
            'tone': nivel_info['tone'],
            'approach': nivel_info['approach'],
            'mensajes_hasta_siguiente_nivel': mensajes_hasta_siguiente if next_level > usuario.nivel_confianza else 0,
            'es_nivel_maximo': usuario.nivel_confianza == 5
        }

    def get_forbidden_phrases(self) -> list:
        """
        Retorna lista de frases prohibidas (cursis/terapéuticas) que Loki NO debe usar.

        Returns:
            Lista de frases prohibidas
        """
        return [
            "estoy aquí para ti",
            "recuerda que puedes confiar en mí",
            "siempre que me necesites",
            "tu bienestar es importante",
            "soy tu espacio seguro",
            "no estás solo",
            "no estás sola",
            "estaré aquí siempre",
            "puedes contar conmigo siempre",
            "mi propósito es ayudarte",
            "estoy para apoyarte",
            "esto es un espacio seguro",
            "tu salud mental importa",
            "quiero que sepas que",
            "es importante que recuerdes"
        ]

    def get_allowed_expressions_by_level(self, nivel: int) -> list:
        """
        Retorna expresiones permitidas según el nivel de confianza.

        Args:
            nivel: Nivel de confianza (1-5)

        Returns:
            Lista de expresiones apropiadas para el nivel
        """
        expressions = {
            1: [  # Conociendo
                "cuéntame más",
                "¿cómo fue tu día?",
                "entiendo",
                "¿qué pasó?",
                "¿y eso cómo te hizo sentir?"
            ],
            2: [  # Estableciendo
                "ayer mencionaste X. ¿sigue ahí?",
                "¿esto pasa seguido?",
                "tiene sentido",
                "¿desde cuándo?",
                "noto que..."
            ],
            3: [  # Construyendo
                "veo que cuando X, sueles Y",
                "esto me recuerda a lo de la semana pasada",
                "¿qué crees que lo causa?",
                "he notado un patrón",
                "como la vez que..."
            ],
            4: [  # Consolidado
                "sé que esto te afecta especialmente",
                "¿y si probamos lo que funcionó antes?",
                "conociéndote, creo que...",
                "esto no es típico en ti",
                "¿qué haría el tú del mes pasado?"
            ],
            5: [  # Íntimo
                "esto no es como tú. ¿qué pasa realmente?",
                "ya sabes qué hacer, ¿verdad?",
                "seamos honestos",
                "te estás evadiendo",
                "¿a quién estás engañando?"
            ]
        }

        # Retornar expresiones del nivel actual y anteriores
        allowed = []
        for lvl in range(1, nivel + 1):
            allowed.extend(expressions.get(lvl, []))

        return allowed


# Singleton instance
trust_service = TrustLevelService()
