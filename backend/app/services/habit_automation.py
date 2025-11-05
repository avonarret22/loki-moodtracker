"""
Helper functions for automatic habit creation and management
"""
from sqlalchemy.orm import Session
from app import crud, schemas
from app.core.logger import setup_logger
from typing import List, Dict, Optional
import re

logger = setup_logger(__name__)


def extract_habit_name_from_mention(habit_mention: str) -> str:
    """
    Extrae el nombre limpio del hábito desde una mención.
    Por ejemplo: "ejercicio hoy" -> "ejercicio", "dormí bien" -> "dormir bien"
    """
    # Remover palabras temporales comunes
    temporal_words = ['hoy', 'ayer', 'mañana', 'tarde', 'esta', 'este', 'ese', 'esa']
    words = habit_mention.lower().split()
    cleaned_words = [w for w in words if w not in temporal_words]
    
    habit_name = ' '.join(cleaned_words).strip()
    
    # Normalizar verbos comunes a infinitivo
    verb_mappings = {
        'hice': 'hacer',
        'hago': 'hacer',
        'corrí': 'correr',
        'corro': 'correr',
        'dormí': 'dormir',
        'duermo': 'dormir',
        'medité': 'meditar',
        'medito': 'meditar',
        'leí': 'leer',
        'leo': 'leer',
        'estudié': 'estudiar',
        'estudio': 'estudiar',
    }
    
    first_word = habit_name.split()[0] if habit_name else ''
    if first_word in verb_mappings:
        habit_name = habit_name.replace(first_word, verb_mappings[first_word], 1)
    
    return habit_name


def categorize_habit(habit_name: str) -> str:
    """
    Categoriza automáticamente un hábito basándose en palabras clave.
    """
    habit_lower = habit_name.lower()
    
    # Categorías predefinidas con palabras clave
    categories = {
        'ejercicio': ['ejercicio', 'gym', 'correr', 'caminar', 'yoga', 'entrenar', 'deporte', 'natación', 'bici'],
        'sueño': ['dormir', 'descansar', 'siesta', 'sueño', 'acostarse'],
        'social': ['amigos', 'familia', 'llamar', 'visitar', 'reunión', 'salir', 'socializar'],
        'trabajo': ['trabajo', 'estudiar', 'proyecto', 'tarea', 'reunión trabajo', 'productividad'],
        'salud': ['agua', 'vitaminas', 'medicamento', 'doctor', 'terapia', 'medicina'],
        'alimentación': ['comer', 'desayunar', 'almorzar', 'cenar', 'cocinar', 'comida'],
        'mindfulness': ['meditar', 'respirar', 'mindfulness', 'relajación', 'meditación'],
        'hobbies': ['leer', 'música', 'pintar', 'escribir', 'hobby', 'pasatiempo'],
    }
    
    for category, keywords in categories.items():
        for keyword in keywords:
            if keyword in habit_lower:
                return category
    
    return 'otro'


async def create_or_update_habits_from_mentions(
    db: Session,
    usuario_id: int,
    habits_mentioned: List[str]
) -> Dict[str, List]:
    """
    Crea o actualiza hábitos basándose en las menciones detectadas en la conversación.
    
    Args:
        db: Sesión de base de datos
        usuario_id: ID del usuario
        habits_mentioned: Lista de hábitos mencionados (puede incluir texto adicional)
    
    Returns:
        Dict con 'created', 'updated', y 'registered' habits
    """
    result = {
        'created': [],
        'updated': [],
        'registered': []
    }
    
    if not habits_mentioned:
        return result
    
    # Obtener todos los hábitos existentes del usuario
    existing_habits = crud.get_habitos_by_usuario(db, usuario_id=usuario_id)
    existing_habits_map = {h.nombre_habito.lower(): h for h in existing_habits}
    
    for mention in habits_mentioned:
        try:
            # Extraer nombre limpio del hábito
            habit_name = extract_habit_name_from_mention(mention)
            
            if not habit_name or len(habit_name) < 2:
                logger.warning(f"Hábito mencionado muy corto o vacío: '{mention}'")
                continue
            
            habit_name_lower = habit_name.lower()
            
            # Verificar si ya existe
            if habit_name_lower in existing_habits_map:
                # Hábito ya existe, registrar el cumplimiento
                habito = existing_habits_map[habit_name_lower]
                
                # Crear registro de cumplimiento
                registro_data = schemas.RegistroHabitoCreate(
                    habito_id=habito.id,
                    completado=True,
                    notas=f"Auto-registrado desde conversación: {mention}"
                )
                crud.create_registro_habito(db, registro_habito=registro_data, usuario_id=usuario_id)
                
                result['registered'].append({
                    'id': habito.id,
                    'nombre': habito.nombre_habito,
                    'action': 'registered'
                })
                
                logger.info(f"✅ Registrado hábito existente: {habito.nombre_habito} para usuario {usuario_id}")
                
            else:
                # Hábito no existe, crearlo
                categoria = categorize_habit(habit_name)
                
                habito_data = schemas.HabitoCreate(
                    nombre_habito=habit_name.title(),  # Capitalizar primera letra
                    categoria=categoria,
                    objetivo_semanal=3,  # Default: 3 veces por semana
                    activo=True
                )
                
                nuevo_habito = crud.create_habito(db, habito=habito_data, usuario_id=usuario_id)
                
                # Crear también el registro de cumplimiento
                registro_data = schemas.RegistroHabitoCreate(
                    habito_id=nuevo_habito.id,
                    completado=True,
                    notas=f"Auto-creado y registrado desde conversación: {mention}"
                )
                crud.create_registro_habito(db, registro_habito=registro_data, usuario_id=usuario_id)
                
                result['created'].append({
                    'id': nuevo_habito.id,
                    'nombre': nuevo_habito.nombre_habito,
                    'categoria': nuevo_habito.categoria,
                    'action': 'created_and_registered'
                })
                
                logger.info(f"✅ Creado nuevo hábito: {nuevo_habito.nombre_habito} (categoría: {categoria}) para usuario {usuario_id}")
                
        except Exception as e:
            logger.error(f"Error procesando hábito '{mention}': {e}")
            continue
    
    return result


def get_habit_summary(habits_result: Dict[str, List]) -> str:
    """
    Genera un resumen legible de las acciones realizadas con hábitos.
    """
    parts = []
    
    if habits_result['created']:
        habit_names = [h['nombre'] for h in habits_result['created']]
        parts.append(f"Creé {len(habit_names)} nuevo(s) hábito(s): {', '.join(habit_names)}")
    
    if habits_result['registered']:
        habit_names = [h['nombre'] for h in habits_result['registered']]
        parts.append(f"Registré {len(habit_names)} hábito(s) que ya tenías: {', '.join(habit_names)}")
    
    if not parts:
        return ""
    
    return " | ".join(parts)
