"""
Servicio de IA para procesamiento de lenguaje natural con Claude/GPT/Gemini.
Maneja la personalidad de Loki y extrae información contextual de las conversaciones.
"""

from typing import Dict, Any, Optional, List
import json
import os
from datetime import datetime
from anthropic import Anthropic
import google.generativeai as genai

from app.core.config import settings
from app.core.logger import setup_logger
from app.services.nlp_service import nlp_service
from app.services.memory_service import memory_service
from app.services.trust_level_service import trust_service
from app.services.emotional_memory_service import emotional_memory_service
from app.services.progress_tracker_service import progress_tracker_service
from app.services.pending_topics_service import pending_topics_service

logger = setup_logger(__name__)


class LokiAIService:
    """
    Servicio principal de IA para Loki.
    Gestiona la personalidad del bot y el procesamiento de mensajes.
    """

    def __init__(self):
        self.anthropic_key = settings.ANTHROPIC_API_KEY
        self.openai_key = settings.OPENAI_API_KEY
        self.google_key = settings.GOOGLE_API_KEY

        # Modo de conversación: 'conciso' (default) o 'profundo'
        self.conversation_mode = 'conciso'

        # Prioridad: Google Gemini > Anthropic Claude > Fallback
        self.ai_provider = None
        
        # 1. Intentar Google Gemini primero (GRATIS)
        if self.google_key:
            try:
                genai.configure(api_key=self.google_key)
                # Usar gemini-2.5-flash (rápido, gratis y muy capaz)
                # Crear modelo SIN system_instruction por ahora
                self.gemini_model = genai.GenerativeModel('gemini-2.5-flash')
                self.ai_provider = 'gemini'
                print("[OK] ✅ Google Gemini (2.5 Flash) inicializado correctamente")
            except Exception as e:
                print(f"[ERROR] Error al inicializar Gemini: {e}")
        
        # 2. Fallback a Claude si Gemini falla
        if not self.ai_provider and self.anthropic_key:
            try:
                self.claude_client = Anthropic(api_key=self.anthropic_key)
                self.ai_provider = 'claude'
                print("[OK] ✅ Claude API inicializada correctamente")
            except Exception as e:
                print(f"[ERROR] Error al inicializar Claude: {e}")
        
        # 3. Si nada funciona, usar reglas
        if not self.ai_provider:
            print("[WARNING] ⚠️ No hay API de IA disponible, usando respuestas basadas en reglas")
        
    def _get_trust_based_system_prompt(self, usuario_nombre: str, nivel_confianza: int, nivel_info: Dict) -> str:
        """
        Prompt adaptado según el nivel de confianza con el usuario.
        Elimina frases cursis y adapta el tono de reservado a cercano.

        Args:
            usuario_nombre: Nombre del usuario
            nivel_confianza: Nivel de confianza (1-5)
            nivel_info: Información del nivel de confianza
        """
        # Frases prohibidas que NUNCA debe usar
        forbidden = trust_service.get_forbidden_phrases()
        forbidden_str = "', '".join(forbidden)

        # Base común para todos los niveles
        base_prompt = f"""Eres Loki, un compañero en el bienestar emocional de {usuario_nombre}.

PERSONALIDAD BASE:
- Natural, conversacional, sin poses terapéuticas
- Curioso pero no invasivo
- Valida sin exagerar
- Pregunta más que explica

PROHIBIDO USAR estas frases cursis:
'{forbidden_str}'

NIVEL DE CONFIANZA ACTUAL: {nivel_info['name']} ({nivel_confianza}/5)
"""

        # Prompts específicos por nivel de confianza
        level_prompts = {
            1: f"""ETAPA: Conociendo a {usuario_nombre} ({nivel_info['description']})

TONO: {nivel_info['tone']}
ENFOQUE: {nivel_info['approach']}
RESPUESTAS: {nivel_info['max_sentences']} oración máximo

GUÍAS:
- Preguntas simples y directas
- No asumas nada sobre la persona
- Educado pero no formal
- NO hagas afirmaciones sobre su vida
- Solo escucha y pregunta para entender

Ejemplos:
✅ "¿Cómo estuvo tu día?"
✅ "Cuéntame más"
✅ "¿Qué pasó?"
❌ "Sé que esto debe ser difícil para ti"
❌ "Entiendo perfectamente cómo te sientes"
""",
            2: f"""ETAPA: Estableciendo relación con {usuario_nombre} ({nivel_info['description']})

TONO: {nivel_info['tone']}
ENFOQUE: {nivel_info['approach']}
RESPUESTAS: Máximo {nivel_info['max_sentences']} oraciones

GUÍAS:
- Empieza a recordar cosas que mencionó antes
- Conecta conversaciones pasadas
- Menos formal, más natural
- Puedes hacer conexiones simples
- Sigue siendo breve

Ejemplos:
✅ "Ayer mencionaste X. ¿Sigue pasando?"
✅ "¿Esto te pasa seguido?"
✅ "Tiene sentido"
❌ "Como siempre, estoy aquí para ti"
❌ "Siento mucho que estés pasando por esto"
""",
            3: f"""ETAPA: Construyendo confianza con {usuario_nombre} ({nivel_info['description']})

TONO: {nivel_info['tone']}
ENFOQUE: {nivel_info['approach']}
RESPUESTAS: Máximo {nivel_info['max_sentences']} oraciones

GUÍAS:
- Identifica y señala patrones
- Sugiere conexiones entre eventos y emociones
- Más proactivo en observaciones
- Recuerda y referencia conversaciones previas
- Puedes ser más directo

Ejemplos:
✅ "Noto que cuando X pasa, sueles sentir Y"
✅ "Esto se parece a lo de la semana pasada"
✅ "¿Ves alguna conexión?"
❌ "Estoy orgulloso de tu progreso"
❌ "Quiero que sepas que valoro tu confianza"
""",
            4: f"""ETAPA: Relación consolidada con {usuario_nombre} ({nivel_info['description']})

TONO: {nivel_info['tone']}
ENFOQUE: {nivel_info['approach']}
RESPUESTAS: Máximo {nivel_info['max_sentences']} oraciones (solo si es necesario)

GUÍAS:
- Lee entre líneas
- Usa humor cuando sea apropiado
- Referencia momentos compartidos
- Puedes desafiar constructivamente
- Sé honesto, no solo validante

Ejemplos:
✅ "Esto no es típico en ti. ¿Qué cambió?"
✅ "¿Y si probamos lo que funcionó la última vez?"
✅ "Conociéndote, sospecho que hay más"
❌ "Siempre admiro tu fortaleza"
❌ "Nuestro vínculo es muy especial"
""",
            5: f"""ETAPA: Confianza profunda con {usuario_nombre} ({nivel_info['description']})

TONO: {nivel_info['tone']}
ENFOQUE: {nivel_info['approach']}
RESPUESTAS: Variable según necesidad (usualmente breve)

GUÍAS:
- Totalmente directo y honesto
- Anticipa lo que no dicen
- Desafía cuando es necesario
- Usa referencias internas (bromas, momentos compartidos)
- Menos es más: a veces una palabra basta

Ejemplos:
✅ "Ya sabes qué hacer, ¿verdad?"
✅ "¿A quién estás tratando de convencer?"
✅ "Seamos honestos"
✅ "Esto no es sobre X. Es sobre Y"
❌ "Nuestra conexión es profunda"
❌ "Me siento honrado de ser tu apoyo"
"""
        }

        return base_prompt + level_prompts.get(nivel_confianza, level_prompts[1])

    def _get_concise_system_prompt(self, usuario_nombre: str) -> str:
        """
        Prompt CONCISO para respuestas breves y directas.
        DEPRECATED: Usar _get_trust_based_system_prompt en su lugar.
        """
        # Fallback al nivel 1 si no tenemos info de confianza
        nivel_info = trust_service.get_trust_level_info(1)
        return self._get_trust_based_system_prompt(usuario_nombre, 1, nivel_info)

    def _get_deep_system_prompt(self, usuario_nombre: str) -> str:
        """
        Prompt PROFUNDO para análisis y exploración detallada.
        DEPRECATED: El sistema de niveles de confianza reemplaza esto.
        """
        # Fallback al nivel 3 para modo profundo
        nivel_info = trust_service.get_trust_level_info(3)
        return self._get_trust_based_system_prompt(usuario_nombre, 3, nivel_info)

    def build_system_prompt(self, usuario_nombre: str, contexto_reciente: List[Dict] = None, db_session = None, usuario_id: int = None) -> str:
        """
        Construye el prompt del sistema basado en el nivel de confianza del usuario.
        Adapta automáticamente la personalidad según la relación.
        
        🆕 Ahora incluye insights de progreso cuando se detectan.
        """
        # Obtener nivel de confianza del usuario
        nivel_confianza = 1
        nivel_info = trust_service.get_trust_level_info(1)

        if db_session and usuario_id:
            trust_info = trust_service.get_user_trust_info(db_session, usuario_id)
            if trust_info:
                nivel_confianza = trust_info['nivel_confianza']
                nivel_info = trust_service.get_trust_level_info(nivel_confianza)
                print(f"🤝 Nivel de confianza con usuario {usuario_id}: {nivel_info['name']} ({nivel_confianza}/5) - {trust_info['total_interacciones']} interacciones")

        # Construir prompt base según nivel de confianza
        prompt = self._get_trust_based_system_prompt(usuario_nombre, nivel_confianza, nivel_info)

        # 📈 NUEVO: Agregar insights de progreso si se detectan
        if db_session and usuario_id and nivel_confianza >= 2:
            try:
                progress_insight = progress_tracker_service.get_progress_insights(
                    db_session,
                    usuario_id,
                    incluir_en_prompt=True
                )
                
                if progress_insight:
                    celebration_context = progress_tracker_service.generate_celebration_context(
                        progress_insight,
                        nivel_confianza
                    )
                    prompt += f"\n\n### PROGRESO DETECTADO:\n{celebration_context}\n"
                    logger.info(f"📈 Progreso incluido en prompt: {progress_insight.tipo}")
            except Exception as e:
                logger.error(f"⚠️ Error obteniendo insights de progreso: {e}")
        
        # 🎯 NUEVO: Agregar sugerencias de seguimiento de temas pendientes
        if db_session and usuario_id and nivel_confianza >= 2:
            try:
                followup_context = pending_topics_service.get_followup_suggestions(
                    db_session,
                    usuario_id,
                    nivel_confianza
                )
                
                if followup_context:
                    prompt += f"\n\n{followup_context}\n"
                    logger.info("🎯 Sugerencia de seguimiento incluida en prompt")
            except Exception as e:
                logger.error(f"⚠️ Error obteniendo seguimientos: {e}")

        # Agregar contexto histórico de largo plazo solo si el nivel de confianza es alto (3+)
        if db_session and usuario_id and nivel_confianza >= 3:
            try:
                long_term_context = memory_service.get_long_term_context(db_session, usuario_id)
                if long_term_context:
                    prompt += f"\n\n{long_term_context}"
            except Exception as e:
                print(f"⚠️ Error obteniendo contexto histórico: {e}")

        # Agregar contexto reciente (últimas conversaciones)
        if contexto_reciente:
            # Cantidad de contexto depende del nivel de confianza
            context_window = min(nivel_confianza + 1, 5)  # Nivel 1: 2 msgs, Nivel 5: 6 msgs
            prompt += f"\n\n### CONVERSACIONES RECIENTES:\n"
            for conv in contexto_reciente[-context_window:]:
                prompt += f"Usuario: {conv.get('mensaje_usuario', '')}\n"
                prompt += f"Tú: {conv.get('respuesta_loki', '')}\n\n"

        return prompt
    
    def _is_asking_for_name(self, usuario_nombre: Optional[str]) -> bool:
        """
        Determina si debemos preguntar el nombre al usuario.
        Returns True si el usuario no tiene nombre registrado.
        """
        return usuario_nombre is None or usuario_nombre.strip() == ""
    
    def _extract_name_from_message(self, mensaje: str) -> Optional[str]:
        """
        Intenta extraer el nombre del usuario de su mensaje.
        Busca patrones como "Soy X", "Me llamo X", "Mi nombre es X", o simplemente "X" si es corto.
        Tolerante a errores de tipeo.
        """
        import re
        
        mensaje = mensaje.strip()
        
        # Lista de palabras comunes que NO son nombres
        palabras_comunes = {
            'hola', 'hi', 'hello', 'hey', 'buenas', 'buenos', 'bien', 'mal', 'gracias',
            'si', 'no', 'ok', 'vale', 'que', 'como', 'cuando', 'donde', 'quien',
            'estoy', 'soy', 'eres', 'estás', 'está', 'tal', 'genial', 'perfecto',
            'regular', 'más', 'menos', 'muy', 'poco', 'mucho', 'nada', 'algo',
            'debes', 'llamarme', 'nombre', 'recordarlo', 'recoerdarlo', 'por',
            'ahora', 'ya', 'ahí', 'aqui', 'aquí', 'entonces', 'luego', 'después'
        }
        
        # Patrones comunes de presentación (con tolerancia a errores de tipeo)
        patterns = [
            # "me llamo", "me yamo", "me allmo" (errores comunes)
            r'(?:me\s+(?:ll[aá]mo|y[aá]mo|[aá]llmo|[aá]lmo))\s+([a-záéíóúñ]+(?:\s+[a-záéíóúñ]+)?)',
            # "mi nombre es" (flexible, permite texto antes)
            r'mi\s+nombre\s+es\s+([a-záéíóúñ]+(?:\s+[a-záéíóúñ]+)?)',
            # "nombre es X" o "nombre, es X"
            r'nombre\s*[,:]?\s*es\s+([a-záéíóúñ]+(?:\s+[a-záéíóúñ]+)?)',
            # "registra mi nombre" seguido de nombre
            r'registra(?:\s+mi)?\s+nombre[,:\s]+(?:es\s+)?([a-záéíóúñ]+)',
            # "cambialo de X a Y" o "cambia de X a Y"
            r'cambia(?:lo|r)?(?:\s+(?:de|mi\s+nombre))?(?:\s+de\s+\w+)?\s+a\s+([a-záéíóúñ]+)',
            # "soy X" (al inicio)
            r'^soy\s+([a-záéíóúñ]+(?:\s+[a-záéíóúñ]+)?)$',
            # "puedes decirme/llamame/dime X"
            r'(?:puedes\s+decirme|dime|ll[áa]mame|llamame)\s+([a-záéíóúñ]+)',
            # "debes llamarme X" o "llamarme X"
            r'(?:debes\s+)?llamarme\s+(?:por\s+mi\s+nombre\s+)?([a-záéíóúñ]+)',
            # Solo nombre (si es una palabra sola y no está en palabras comunes)
            r'^([a-záéíóúñ]{2,20})$',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, mensaje.lower())
            if match:
                nombre = match.group(1).strip()
                
                # Limpiar palabras de parada al final del nombre
                palabras = nombre.split()
                # Remover palabras comunes del final
                while palabras and palabras[-1].lower() in palabras_comunes:
                    palabras.pop()
                
                if not palabras:
                    continue
                
                nombre_limpio = ' '.join(palabras)
                
                # Verificar que no sea una palabra común
                if nombre_limpio.lower() in palabras_comunes:
                    continue
                
                # Capitalizar correctamente
                nombre_capitalizado = ' '.join(word.capitalize() for word in nombre_limpio.split())
                
                # Validar que sea un nombre razonable (2-30 caracteres, solo letras y espacios)
                if 2 <= len(nombre_capitalizado) <= 30 and re.match(r'^[a-záéíóúñA-ZÁÉÍÓÚÑ\s]+$', nombre_capitalizado):
                    return nombre_capitalizado
        
        return None
    
    def _generate_ask_name_response(self) -> str:
        """
        Genera una respuesta natural pidiendo el nombre al usuario.
        """
        responses = [
            "Hola! Soy Loki 🐺 ¿Cómo te llamas?",
            "Hey! Soy Loki. ¿Cómo prefieres que te llame?",
            "Hola! Soy Loki, tu compañero de bienestar. ¿Cuál es tu nombre?",
            "Hola! Me llamo Loki. ¿Y tú?",
        ]
        import random
        return random.choice(responses)
    
    def _generate_greeting_with_name(self, nombre: str) -> str:
        """
        Genera un saludo natural después de conocer el nombre.
        """
        responses = [
            f"Encantado, {nombre}! ¿Cómo estás hoy?",
            f"Genial conocerte, {nombre}. ¿Cómo te sientes?",
            f"Mucho gusto, {nombre}. ¿Qué tal tu día?",
            f"Perfecto, {nombre}. ¿Cómo has estado?",
        ]
        import random
        return random.choice(responses)
    
    def extract_mood_level(self, mensaje: str) -> Optional[int]:
        """
        Extrae el nivel de ánimo del mensaje si está presente.
        Busca patrones como "8/10", "nivel 7", "me siento 6", "un 8 de 10", etc.
        """
        import re
        
        # Patrones comunes para extraer nivel de ánimo (ordenados por especificidad)
        patterns = [
            r'(?:un|una)\s+(\d+)\s+de\s+10',  # "un 8 de 10", "una 7 de 10"
            r'(\d+)\s+de\s+10',                # "8 de 10", "7 de 10"
            r'(\d+)/10',                       # "8/10", "7/10"
            r'nivel\s+(\d+)',                  # "nivel 8", "nivel 7"
            r'me\s+siento\s+(?:un\s+)?(\d+)',  # "me siento 8", "me siento un 8"
            r'estoy\s+(?:en\s+)?(?:un\s+)?(\d+)', # "estoy 8", "estoy en 8", "estoy un 8"
            r'(?:como\s+)?(\d+)\s+(?:de\s+)?(?:10)?(?:\s+hoy)?', # "como 8", "8 hoy"
            r'^(\d+)$',                        # Solo un número
        ]
        
        for pattern in patterns:
            match = re.search(pattern, mensaje.lower())
            if match:
                nivel = int(match.group(1))
                if 1 <= nivel <= 10:
                    return nivel
        
        return None
    
    def extract_habits_mentioned(self, mensaje: str) -> List[str]:
        """
        Extrae hábitos mencionados en el mensaje usando NLP básico.
        """
        habitos_detectados = []
        mensaje_lower = mensaje.lower()
        
        # Diccionario de palabras clave por categoría de hábito
        habitos_keywords = {
            'ejercicio': ['ejercicio', 'gym', 'gimnasio', 'correr', 'corri', 'entrenar', 'entrené', 'deporte', 'caminar', 'caminé', 'yoga'],
            'sueño': ['dormir', 'dormí', 'dormi', 'sueño', 'descansar', 'descansé', 'descanso', 'siesta'],
            'social': ['amigos', 'salir', 'salí', 'sali', 'reunión', 'reunion', 'familia', 'pareja', 'cita'],
            'trabajo': ['trabajo', 'trabajé', 'trabajar', 'oficina', 'reunión de trabajo', 'proyecto', 'deadline'],
            'meditación': ['meditar', 'medité', 'meditación', 'mindfulness', 'respirar'],
            'lectura': ['leer', 'leí', 'lei', 'libro', 'lectura'],
            'alimentación': ['comer', 'comí', 'comida', 'desayuno', 'almuerzo', 'cena', 'cocinar', 'cociné'],
        }
        
        for habito, keywords in habitos_keywords.items():
            for keyword in keywords:
                if keyword in mensaje_lower:
                    habitos_detectados.append(habito)
                    break  # Solo agregamos cada hábito una vez
        
        return habitos_detectados
    
    def extract_emotional_triggers(self, mensaje: str) -> List[str]:
        """
        Identifica posibles disparadores emocionales mencionados.
        """
        triggers = []
        mensaje_lower = mensaje.lower()
        
        # Disparadores comunes
        trigger_keywords = {
            'estrés': ['estrés', 'estres', 'estresado', 'estresada', 'presión', 'agobiado', 'agobiada'],
            'ansiedad': ['ansiedad', 'ansioso', 'ansiosa', 'nervioso', 'nerviosa', 'preocupado', 'preocupada'],
            'cansancio': ['cansado', 'cansada', 'agotado', 'agotada', 'exhausto', 'exhausta', 'fatigado'],
            'conflicto': ['pelea', 'discusión', 'discusion', 'conflicto', 'problema', 'desacuerdo'],
            'soledad': ['solo', 'sola', 'soledad', 'aislado', 'aislada'],
            'alegría': ['feliz', 'alegre', 'contento', 'contenta', 'emocionado', 'emocionada'],
        }
        
        for trigger, keywords in trigger_keywords.items():
            for keyword in keywords:
                if keyword in mensaje_lower:
                    triggers.append(trigger)
                    break
        
        return triggers
    
    def analyze_message_context(self, mensaje: str, conversation_history: List[str] = None) -> Dict[str, Any]:
        """
        Análisis completo del mensaje para extraer toda la información relevante.
        Usa tanto análisis clásicos (mood, hábitos, triggers) como análisis NLP avanzado.

        Args:
            mensaje: El mensaje a analizar
            conversation_history: Historial de mensajes anteriores para análisis de patrones
        """
        # Análisis clásicos (mantener compatibilidad)
        context = {
            'mood_level': self.extract_mood_level(mensaje),
            'habits_mentioned': self.extract_habits_mentioned(mensaje),
            'emotional_triggers': self.extract_emotional_triggers(mensaje),
            'timestamp': datetime.utcnow().isoformat(),
        }

        # Análisis NLP avanzado
        advanced_nlp = nlp_service.analyze_complete_context(
            mensaje,
            conversation_history=conversation_history
        )

        # Enriquecer contexto con análisis avanzado
        context['nlp_analysis'] = {
            'sentiment': advanced_nlp['sentiment'],
            'entities': advanced_nlp['entities'],
            'values_detected': advanced_nlp['values'],
        }

        if 'language_patterns' in advanced_nlp:
            context['language_patterns'] = advanced_nlp['language_patterns']

        return context
    
    async def generate_response(
        self,
        mensaje_usuario: str,
        usuario_nombre: str,
        contexto_reciente: List[Dict] = None,
        user_context: Dict = None,
        db_session = None,  # Nueva: sesión de BD para análisis de patrones
        usuario_id: int = None  # Nueva: ID del usuario para análisis
    ) -> Dict[str, Any]:
        """
        Genera una respuesta de Loki basada en el mensaje del usuario.
        Ahora incluye análisis de patrones personales y análisis NLP avanzado.
        
        🆕 FLUJO DE OBTENCIÓN DE NOMBRE:
        - Si el usuario no tiene nombre, Loki lo pide en la primera interacción
        - Extrae automáticamente el nombre de la respuesta del usuario
        - Actualiza la BD con el nombre detectado

        Returns:
            Dict con 'respuesta', 'context_extracted', 'pattern_insights', 'nombre_detectado' y otros metadatos
        """
        # 🎭 FLUJO: Obtención del nombre del usuario
        if self._is_asking_for_name(usuario_nombre):
            # Primera vez: pedir el nombre
            if not contexto_reciente or len(contexto_reciente) == 0:
                return {
                    'respuesta': self._generate_ask_name_response(),
                    'context_extracted': {},
                    'nombre_detectado': None,
                    'esperando_nombre': True,
                    'needs_followup': False
                }
            
            # Segunda vez: el usuario está respondiendo con su nombre
            nombre_detectado = self._extract_name_from_message(mensaje_usuario)
            
            if nombre_detectado:
                # ✅ Nombre detectado! NO actualizar aquí, dejar que el webhook lo haga
                # Solo retornar el nombre detectado para que el webhook lo guarde
                logger.info(f"✅ Nombre detectado: {nombre_detectado} para usuario {usuario_id}")
                
                # Responder con un saludo personalizado
                return {
                    'respuesta': self._generate_greeting_with_name(nombre_detectado),
                    'context_extracted': {},
                    'nombre_detectado': nombre_detectado,
                    'esperando_nombre': False,
                    'needs_followup': False
                }
            else:
                # No se detectó nombre válido, volver a preguntar amablemente
                return {
                    'respuesta': "No estoy seguro de haber entendido tu nombre. ¿Podrías decírmelo de nuevo?",
                    'context_extracted': {},
                    'nombre_detectado': None,
                    'esperando_nombre': True,
                    'needs_followup': False
                }
        
        # 🎯 FLUJO NORMAL: Usuario ya tiene nombre
        # 🆕 Pero primero verificar si está intentando actualizar su nombre
        nombre_detectado_nuevo = self._extract_name_from_message(mensaje_usuario)
        if nombre_detectado_nuevo and nombre_detectado_nuevo.lower() != usuario_nombre.lower():
            # El usuario está diciendo un nombre diferente al registrado
            logger.info(f"🔄 Usuario intentando actualizar nombre de '{usuario_nombre}' a '{nombre_detectado_nuevo}'")
            
            # NO actualizar en BD aquí, dejar que el webhook lo haga
            # Solo retornar el nombre detectado
            
            # Confirmar el cambio de nombre
            return {
                'respuesta': f"Perfecto, {nombre_detectado_nuevo}! Te recordaré con ese nombre. ¿Cómo estás?",
                'context_extracted': {},
                'nombre_detectado': nombre_detectado_nuevo,
                'esperando_nombre': False,
                'needs_followup': False
            }
        
        # Preparar historial conversacional para análisis NLP
        conversation_history = []
        if contexto_reciente:
            conversation_history = [conv.get('mensaje_usuario', '') for conv in contexto_reciente[-5:]]

        # Analizar el contexto del mensaje (ahora con NLP avanzado)
        extracted_context = self.analyze_message_context(mensaje_usuario, conversation_history)
        
        # 🧠 NUEVA: Extraer y guardar memoria emocional
        emotional_memory = None
        if db_session and usuario_id:
            try:
                emotional_memory = emotional_memory_service.extract_emotional_memory(
                    db_session,
                    usuario_id,
                    mensaje_usuario,
                    mood_level=extracted_context.get('mood_level')
                )
                
                # Guardar si es significativo
                if emotional_memory:
                    emotional_memory_service.save_memory(db_session, usuario_id, emotional_memory)
                    logger.info(f"💭 Memoria emocional guardada: {emotional_memory.tema} - {emotional_memory.sentimiento}")
            except Exception as e:
                logger.error(f"⚠️ Error procesando memoria emocional: {e}")
        
        # 🎯 NUEVA: Detectar y gestionar temas pendientes
        pending_topics_detected = []
        resolved_topics = []
        if db_session and usuario_id:
            try:
                # 1. Verificar si se resolvieron temas pendientes anteriores
                resolved_topics = pending_topics_service.check_topic_resolutions(
                    db_session, usuario_id, mensaje_usuario
                )
                
                # 2. Detectar nuevos temas pendientes mencionados
                pending_topics_detected = pending_topics_service.detect_pending_topics(
                    db_session,
                    usuario_id,
                    mensaje_usuario,
                    mood_score=extracted_context.get('mood_level')
                )
                
                # 3. Guardar nuevos temas pendientes
                if pending_topics_detected:
                    pending_topics_service.save_pending_topics(
                        db_session, usuario_id, pending_topics_detected
                    )
                    logger.info(f"🎯 Detectados {len(pending_topics_detected)} temas pendientes")
                
                if resolved_topics:
                    logger.info(f"✅ Resueltos {len(resolved_topics)} temas pendientes")
                    
            except Exception as e:
                logger.error(f"⚠️ Error procesando temas pendientes: {e}")
        
        # Obtener insights de patrones personales si hay BD disponible
        pattern_insight = ""
        if db_session and usuario_id:
            try:
                from app.services.pattern_analysis import pattern_service
                pattern_insight = pattern_service.get_relevant_insights_for_conversation(
                    db_session, 
                    usuario_id,
                    current_mood=extracted_context.get('mood_level')
                )
            except Exception as e:
                print(f"⚠️ Error obteniendo insights de patrones: {e}")
        
        # Intentar generar respuesta con IA (Gemini o Claude)
        if self.ai_provider:
            try:
                provider_name = "Gemini" if self.ai_provider == 'gemini' else "Claude"
                print(f"🤖 Generando respuesta con {provider_name} para: '{mensaje_usuario[:50]}...'")
                respuesta = await self._generate_claude_response(
                    mensaje_usuario,
                    usuario_nombre,
                    contexto_reciente,
                    extracted_context,
                    pattern_insight,  # Pasar el insight al modelo
                    db_session,  # Pasar sesión para contexto histórico
                    usuario_id  # Pasar ID para contexto histórico
                )
                print(f"✅ Respuesta de {provider_name} generada exitosamente")
            except Exception as e:
                print(f"⚠️ Error con {self.ai_provider.upper()} API: {e}")
                print(f"⚠️ Tipo de error: {type(e).__name__}")
                print("⚠️ Fallback a respuestas basadas en reglas")
                respuesta = self._generate_rule_based_response(
                    mensaje_usuario, 
                    usuario_nombre,
                    extracted_context
                )
        else:
            # Fallback a respuestas basadas en reglas
            print("ℹ️ Usando respuestas basadas en reglas (sin Claude API)")
            respuesta = self._generate_rule_based_response(
                mensaje_usuario, 
                usuario_nombre,
                extracted_context
            )
        
        return {
            'respuesta': respuesta,
            'context_extracted': extracted_context,
            'pattern_insight_used': pattern_insight,
            'needs_followup': self._needs_followup(extracted_context),
        }
    
    async def _generate_claude_response(
        self,
        mensaje_usuario: str,
        usuario_nombre: str,
        contexto_reciente: List[Dict] = None,
        extracted_context: Dict = None,
        pattern_insight: str = "",  # Nuevo parámetro
        db_session = None,  # Para contexto histórico
        usuario_id: int = None  # Para contexto histórico
    ) -> str:
        """
        Genera respuesta usando Claude API.
        Ahora incluye insights de patrones personales cuando están disponibles.
        """
        # Construir el system prompt (con contexto histórico si disponible)
        system_prompt = self.build_system_prompt(usuario_nombre, contexto_reciente, db_session, usuario_id)
        
        # Agregar información del contexto extraído al prompt
        context_info = ""
        if extracted_context:
            # Información clásica
            if extracted_context.get('mood_level'):
                context_info += f"\n[INFO: Usuario mencionó nivel de ánimo {extracted_context['mood_level']}/10]"
            if extracted_context.get('habits_mentioned'):
                context_info += f"\n[INFO: Hábitos detectados: {', '.join(extracted_context['habits_mentioned'])}]"
            if extracted_context.get('emotional_triggers'):
                context_info += f"\n[INFO: Disparadores emocionales: {', '.join(extracted_context['emotional_triggers'])}]"

            # Información NLP avanzada
            nlp_data = extracted_context.get('nlp_analysis', {})
            if nlp_data:
                sentiment_data = nlp_data.get('sentiment', {})
                if sentiment_data.get('dominant_emotion'):
                    context_info += f"\n[SENTIMIENTO: Emoción dominante '{sentiment_data['dominant_emotion']}' (sentimiento general: {sentiment_data.get('overall_sentiment', 0)}, complejidad: {sentiment_data.get('emotional_complexity', 'desconocida')})]"

                entities_data = nlp_data.get('entities', {})
                if entities_data.get('relationships'):
                    context_info += f"\n[CONTEXTO RELACIONAL: Personas/relaciones mencionadas: {', '.join(entities_data['relationships'])}]"
                if entities_data.get('eventos'):
                    context_info += f"\n[EVENTOS: {', '.join(entities_data['eventos'])}]"

                values_data = nlp_data.get('values_detected', {})
                if values_data:
                    top_values = sorted(values_data.items(), key=lambda x: x[1], reverse=True)[:3]
                    values_str = ', '.join([f"{v[0]} ({v[1]})" for v in top_values])
                    context_info += f"\n[VALORES DETECTADOS: {values_str}]"

            # Patrones de lenguaje
            if extracted_context.get('language_patterns'):
                lp = extracted_context['language_patterns']
                context_info += f"\n[ESTILO CONVERSACIONAL: Nivel vocabulario {lp.get('vocabulary_level', 'desconocido')}, estructura de oraciones {lp.get('sentence_structure', 'desconocida')}]"
        
        # Agregar insight de patrones si está disponible
        if pattern_insight:
            context_info += f"\n\n[INSIGHT PERSONALIZADO DISPONIBLE]\n{pattern_insight}\n"
            context_info += "[INSTRUCCIÓN: Incorporá este insight de forma NATURAL y CONVERSACIONAL en tu respuesta si es relevante. "
            context_info += "No lo cites textualmente, sino usalo como base para hacer una sugerencia empática.]"
        
        # Construir mensajes para la conversación
        messages = []
        
        # Agregar contexto reciente si existe
        if contexto_reciente:
            for conv in contexto_reciente[-3:]:  # Últimas 3 conversaciones
                messages.append({
                    "role": "user",
                    "content": conv.get('mensaje_usuario', '')
                })
                messages.append({
                    "role": "assistant",
                    "content": conv.get('respuesta_loki', '')
                })
        
        # Agregar el mensaje actual
        mensaje_completo = mensaje_usuario
        if context_info:
            mensaje_completo += context_info
            
        messages.append({
            "role": "user",
            "content": mensaje_completo
        })
        
        # Para Gemini, guardar el mensaje SIN context_info (causa bloqueos)
        mensaje_sin_context = mensaje_usuario
        
        # Llamar a la API de IA disponible
        if self.ai_provider == 'gemini':
            # Google Gemini API - Usar formato natural sin etiquetas de roleplay
            from google.generativeai.types import HarmCategory, HarmBlockThreshold
            
            # Configuración de seguridad moderada
            safety_settings = {
                HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_ONLY_HIGH,
                HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_ONLY_HIGH,
                HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_ONLY_HIGH,
                HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_ONLY_HIGH,
            }
            
            # Formato natural que evita bloqueos de seguridad
            # IMPORTANTE: Usar mensaje SIN context_info (los corchetes causan bloqueos)
            # Formato simple y directo que no activa filtros
            simple_prompt = f"{usuario_nombre} te dice: '{mensaje_sin_context}'. Responde de forma amigable y breve."
            
            response = self.gemini_model.generate_content(
                simple_prompt,
                generation_config=genai.types.GenerationConfig(
                    max_output_tokens=300,
                    temperature=0.8,
                ),
                safety_settings=safety_settings
            )
            
            # Manejar respuestas bloqueadas
            if not response.candidates or not response.text:
                raise Exception("Respuesta bloqueada o vacía")
            
            respuesta = response.text
            
        elif self.ai_provider == 'claude':
            # Claude API
            response = self.claude_client.messages.create(
                model="claude-3-haiku-20240307",
                max_tokens=300,
                temperature=0.8,
                system=system_prompt,
                messages=messages
            )
            respuesta = response.content[0].text
        else:
            # Fallback a reglas si no hay API
            raise Exception("No AI provider available")
        
        return respuesta
    
    def _generate_rule_based_response(
        self, 
        mensaje: str, 
        nombre: str, 
        context: Dict
    ) -> str:
        """
        Genera respuestas basadas en reglas mientras no tengamos la API configurada.
        """
        import random
        
        mensaje_lower = mensaje.lower().strip()
        
        # 1. Detectar saludos simples
        saludos = ['hola', 'hey', 'hi', 'hello', 'buenas', 'buenos días', 'buenas tardes', 'buenas noches', 'qué tal', 'que tal']
        es_saludo = any(saludo in mensaje_lower for saludo in saludos)
        
        # Si es solo un saludo (sin más contexto)
        if es_saludo and len(mensaje_lower.split()) <= 3:
            respuestas_saludo = [
                f"Hola {nombre}! ¿Cómo estás?",
                f"Hey {nombre}! ¿Qué tal tu día?",
                f"Hola {nombre}! ¿Cómo te va?",
                f"Hey {nombre}! ¿Cómo te sientes hoy?",
            ]
            return random.choice(respuestas_saludo)
        
        # 2. Si detectamos un nivel de ánimo
        if context['mood_level']:
            nivel = context['mood_level']
            if nivel >= 8:
                return f"¡Qué bueno escuchar eso, {nombre}! ¿Qué crees que hizo que te sintieras así de bien hoy?"
            elif nivel >= 6:
                return f"Un {nivel}/10 está bastante bien, {nombre}. ¿Algo en particular que influyó en cómo te sientes?"
            elif nivel >= 4:
                return f"Veo que estás en un {nivel}/10. ¿Hay algo específico que esté afectando tu ánimo hoy?"
            else:
                return f"Lamento que estés pasando por un momento difícil, {nombre}. ¿Quieres contarme qué está pasando?"
        
        # 3. Si mencionó hábitos
        if context['habits_mentioned']:
            habitos = ', '.join(context['habits_mentioned'])
            return f"Genial que hayas hecho {habitos} hoy. ¿Cómo te sientes después de eso?"
        
        # 4. Si hay disparadores emocionales
        if context['emotional_triggers']:
            trigger = context['emotional_triggers'][0]
            if trigger in ['estrés', 'ansiedad']:
                return f"Entiendo que estés sintiendo {trigger}. ¿Esto es algo que viene de hace rato o surgió hoy?"
            elif trigger == 'alegría':
                return f"¡Me encanta tu energía! ¿Qué te tiene tan bien hoy?"
        
        # 5. Respuesta genérica empática (solo si no es saludo)
        mensajes_genericos = [
            f"Cuéntame más, {nombre}. ¿Cómo ha estado tu día?",
            f"¿Qué tal tu día, {nombre}?",
            f"Interesante. ¿Cómo te sientes hoy?",
        ]
        
        return random.choice(mensajes_genericos)
    
    def _needs_followup(self, context: Dict) -> bool:
        """
        Determina si Loki debería hacer una pregunta de seguimiento.
        """
        # Si detectamos un nivel muy bajo de ánimo
        if context['mood_level'] and context['mood_level'] < 4:
            return True

        # Si hay disparadores sin contexto adicional
        if context['emotional_triggers'] and not context['habits_mentioned']:
            return True

        return False

    def set_conversation_mode(self, mode: str):
        """
        Cambia el modo de conversación.
        'conciso': Respuestas breves y directas (default)
        'profundo': Análisis detallado y exploración
        """
        if mode in ['conciso', 'profundo']:
            self.conversation_mode = mode
            print(f"✅ Modo de conversación cambiado a: {mode}")
        else:
            print(f"⚠️ Modo inválido. Usa 'conciso' o 'profundo'")

    def get_conversation_mode(self) -> str:
        """Retorna el modo de conversación actual."""
        return self.conversation_mode


# Instancia singleton del servicio
loki_service = LokiAIService()
