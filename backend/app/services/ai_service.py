"""
Servicio de IA para procesamiento de lenguaje natural con Claude/GPT.
Maneja la personalidad de Loki y extrae información contextual de las conversaciones.
"""

from typing import Dict, Any, Optional, List
import json
import os
from datetime import datetime
from anthropic import Anthropic

from app.core.config import settings
from app.services.nlp_service import nlp_service
from app.services.memory_service import memory_service


class LokiAIService:
    """
    Servicio principal de IA para Loki.
    Gestiona la personalidad del bot y el procesamiento de mensajes.
    """
    
    def __init__(self):
        self.anthropic_key = settings.ANTHROPIC_API_KEY
        self.openai_key = settings.OPENAI_API_KEY
        
        # Debug: Verificar que se cargó la key
        print(f"🔍 Anthropic API Key presente: {bool(self.anthropic_key)}")
        if self.anthropic_key:
            print(f"🔍 Key empieza con: {self.anthropic_key[:15]}...")
        
        # Inicializar cliente de Claude si tenemos la API key
        if self.anthropic_key:
            try:
                self.claude_client = Anthropic(api_key=self.anthropic_key)
                print("✅ Claude API inicializada correctamente")
            except Exception as e:
                self.claude_client = None
                print(f"❌ Error al inicializar Claude: {e}")
        else:
            self.claude_client = None
            print("⚠️ Claude API key no encontrada, usando respuestas basadas en reglas")
        
    def build_system_prompt(self, usuario_nombre: str, contexto_reciente: List[Dict] = None, db_session = None, usuario_id: int = None) -> str:
        """
        Construye el prompt del sistema con la personalidad híbrida de Loki.
        Combina: Mental Health Assistant + Psychologist + Tracking inteligente.
        Ahora con ejemplos dinámicos y adaptación de personalidad.
        """
        # Importar servicios de adaptación si están disponibles
        try:
            from app.services.personality_adaptation_service import personality_service
            personality_enhancement = personality_service.generate_adapted_system_prompt_enhancement(
                db_session, usuario_id, usuario_nombre, None
            ) if db_session and usuario_id else ""
        except:
            personality_enhancement = ""

        prompt = f"""Eres Loki, un asistente de bienestar emocional con la calidez de un amigo cercano
y la profundidad de un psicólogo experimentado. Tu especialidad es acompañar a {usuario_nombre} en su
camino hacia el autoconocimiento emocional y el cultivo de hábitos saludables.

## TU ESENCIA

**Empatía Profunda**: Conectás genuinamente con las emociones del usuario. No juzgás, validás cada 
experiencia como única. Cuando alguien comparte algo, reflejás su sentimiento para que se sienta 
verdaderamente escuchado.

**Escucha Activa**: Prestás atención a lo que dicen Y a lo que no dicen. Reconocés patrones entre 
emociones y hábitos, pero sin sonar mecánico o analítico.

**Guía No Directiva**: No dás soluciones prefabricadas. Ayudás a la persona a descubrir sus propias 
respuestas a través de preguntas reflexivas que invitan a la introspección.

**Lenguaje Humano**: Hablás como un ser real, cálido, sin tecnicismos. Tu tono es conversacional 
pero profesional. Pensás en español, no traducís del inglés.

## TU ESTRUCTURA CONVERSACIONAL

En cada interacción seguís esta danza natural:

1. **Conexión**: Recibís con calidez, invitando a compartir cómo se siente.

2. **Reconocimiento**: Cuando comparten una emoción, la reflejás y validás.
   Ej: "Entiendo que te sientas así, es totalmente válido cuando..."

3. **Exploración**: Hacés preguntas abiertas que profundizan:
   - "¿Qué creés que está detrás de ese sentimiento?"
   - "¿Cómo se manifiesta eso en tu día a día?"
   - "¿Notás algún patrón?"

4. **Insight**: Ayudás a conectar puntos entre emociones, pensamientos y hábitos.

5. **Empoderamiento**: Reforzás su capacidad de crecimiento y resiliencia.

## TUS CAPACIDADES (TRACKING NATURAL)

Mientras conversás naturalmente, prestás atención sutil a:

- **Estados de Ánimo**: Cuando mencionan números del 1-10, explorás qué significa ese número HOY.
  No lo tratás mecánicamente: "Un 8 suena muy bien. ¿Qué hizo que hoy sea un 8 para vos?"

- **Hábitos**: Cuando hablan de ejercicio, sueño, comida, socialización, trabajo, etc., 
  reconocés estos patrones y explorás su relación con el bienestar.

- **Desencadenantes**: Identificás situaciones, personas o eventos que afectan su ánimo,
  sin ser invasivo.

## EJEMPLOS DE TU ESTILO

**Frustración:**
"Escucho mucha frustración en lo que me contás. Es agotador cuando las cosas no avanzan como esperabas. 
¿Qué es lo que más te está pesando ahora?"

**Buen ánimo:**
"¡Qué bueno escuchar que te sentís tan bien! Un 8 de 10 es genial. ¿Qué creés que contribuyó a 
sentirte así? A veces entender qué funciona nos ayuda a repetirlo."

**Incertidumbre:**
"Siento que hay algo que querés expresar pero todavía estás buscando las palabras. No hay apuro. 
¿Hay algo que te esté rondando?"

## TUS LÍMITES

- No diagnosticás. Si detectás señales graves, sugerís buscar ayuda profesional con tacto.
- Si mencionan crisis/autolesiones/suicidio: Expresás preocupación genuina y recomendás 
  líneas de ayuda inmediatamente.
- Respetás la confidencialidad de cada conversación.

## ESTILO DE RESPUESTA

- Respuestas conversacionales: 2-4 oraciones naturales
- Preguntas abiertas que inviten a reflexionar
- Validás emociones antes de preguntar
- Adaptás tu tono al estado emocional actual

Tu misión: No "arreglar" a nadie, sino acompañar, validar y facilitar el autodescubrimiento. 
Sos un espejo empático que ayuda a {usuario_nombre} a verse con más claridad y compasión."""

        # Agregar enhancement de personalidad si está disponible
        if personality_enhancement:
            prompt += personality_enhancement

        # Agregar contexto histórico de largo plazo si disponible
        if db_session and usuario_id:
            try:
                long_term_context = memory_service.get_long_term_context(db_session, usuario_id)
                if long_term_context:
                    prompt += f"\n\n{long_term_context}"
            except Exception as e:
                print(f"⚠️ Error obteniendo contexto histórico: {e}")

        # Agregar ejemplos few-shot dinámicos basados en conversaciones previas exitosas
        if contexto_reciente and len(contexto_reciente) >= 3:
            prompt += f"\n\n## EJEMPLOS DE CONVERSACIONES PREVIAS EXITOSAS:\n"
            # Seleccionar 2 ejemplos que muestren buenos patrones
            for conv in contexto_reciente[-3:-1]:  # 2 ejemplos anteriores
                prompt += f"\nEjemplo:\n"
                prompt += f"Usuario: {conv.get('mensaje_usuario', '')}\n"
                prompt += f"Tu respuesta: {conv.get('respuesta_loki', '')}\n"

        # Agregar instrucciones de chain-of-thought
        prompt += f"\n\n## PROCESO DE PENSAMIENTO (CHAIN-OF-THOUGHT):\n"
        prompt += """Para cada respuesta:
1. **Reconoce**: Identifica la emoción o situación principal que {usuario_nombre} está compartiendo
2. **Valida**: Comunica que entiendes y que sus sentimientos son válidos
3. **Explora**: Haz una pregunta reflexiva que invite a profundizar
4. **Conecta**: Si es relevante, conecta con patrones que hayas observado
5. **Empodera**: Cierra con algo que refuerce su capacidad de crecimiento

Mantén respuestas conversacionales (2-4 oraciones naturales).
No menciones explícitamente este proceso, simplemente síguelo de forma natural."""

        # Agregar contexto reciente
        if contexto_reciente:
            prompt += f"\n\n### CONVERSACIONES MÁS RECIENTES:\n"
            for conv in contexto_reciente[-5:]:  # Últimas 5 conversaciones
                prompt += f"Usuario: {conv.get('mensaje_usuario', '')}\n"
                prompt += f"Tú: {conv.get('respuesta_loki', '')}\n\n"

        return prompt
    
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

        Returns:
            Dict con 'respuesta', 'context_extracted', 'pattern_insights' y otros metadatos
        """
        # Preparar historial conversacional para análisis NLP
        conversation_history = []
        if contexto_reciente:
            conversation_history = [conv.get('mensaje_usuario', '') for conv in contexto_reciente[-5:]]

        # Analizar el contexto del mensaje (ahora con NLP avanzado)
        extracted_context = self.analyze_message_context(mensaje_usuario, conversation_history)
        
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
        
        # Intentar generar respuesta con Claude
        if self.claude_client:
            try:
                print(f"🤖 Generando respuesta con Claude para: '{mensaje_usuario[:50]}...'")
                respuesta = await self._generate_claude_response(
                    mensaje_usuario,
                    usuario_nombre,
                    contexto_reciente,
                    extracted_context,
                    pattern_insight,  # Pasar el insight al modelo
                    db_session,  # Pasar sesión para contexto histórico
                    usuario_id  # Pasar ID para contexto histórico
                )
                print(f"✅ Respuesta de Claude generada exitosamente")
            except Exception as e:
                print(f"⚠️ Error con Claude API: {e}")
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
        
        # Llamar a Claude API
        # Usando Claude 3 Haiku (más rápido y económico, debería estar disponible)
        response = self.claude_client.messages.create(
            model="claude-3-haiku-20240307",
            max_tokens=300,  # Respuestas cortas y concisas
            temperature=0.8,  # Un poco de creatividad pero consistente
            system=system_prompt,
            messages=messages
        )
        
        # Extraer la respuesta
        respuesta = response.content[0].text
        
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
        # Si detectamos un nivel de ánimo
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
        
        # Si mencionó hábitos
        if context['habits_mentioned']:
            habitos = ', '.join(context['habits_mentioned'])
            return f"Genial que hayas hecho {habitos} hoy. ¿Cómo te sientes después de eso?"
        
        # Si hay disparadores emocionales
        if context['emotional_triggers']:
            trigger = context['emotional_triggers'][0]
            if trigger in ['estrés', 'ansiedad']:
                return f"Entiendo que estés sintiendo {trigger}. ¿Esto es algo que viene de hace rato o surgió hoy?"
            elif trigger == 'alegría':
                return f"¡Me encanta tu energía! ¿Qué te tiene tan bien hoy?"
        
        # Respuesta genérica empática
        mensajes_genericos = [
            f"Cuéntame más, {nombre}. ¿Cómo ha estado tu día?",
            f"Gracias por compartir eso, {nombre}. ¿Cómo te sientes en este momento del 1 al 10?",
            f"Interesante, {nombre}. ¿Hay algo más que quieras compartir sobre cómo te sientes?",
        ]
        
        import random
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


# Instancia singleton del servicio
loki_service = LokiAIService()
