"""
Script para probar el nuevo Loki mejorado con personalidad híbrida.
Combina Mental Health Assistant + Psychologist + Tracking inteligente.
"""
import asyncio
import sys
import os

# Agregar el directorio actual al path
sys.path.insert(0, os.path.dirname(__file__))

from app.services.ai_service import LokiAIService

async def test_new_loki():
    """Prueba el nuevo Loki con diferentes escenarios."""
    
    print("🧪 Probando el NUEVO Loki mejorado...\n")
    print("="*70)
    
    loki_service = LokiAIService()
    
    if not loki_service.claude_client:
        print("❌ Claude no está disponible. Verifica tu API key.")
        return
    
    print(f"✅ Cliente inicializado: {bool(loki_service.claude_client)}\n")
    
    # Escenarios de prueba
    scenarios = [
        {
            "name": "Estado de ánimo alto con hábitos",
            "message": "Hola Loki! Hoy me siento un 8 de 10 porque dormí muy bien y hice ejercicio",
            "context": []
        },
        {
            "name": "Frustración emocional",
            "message": "Estoy muy frustrado, siento que nada sale como quiero",
            "context": []
        },
        {
            "name": "Exploración de patrones",
            "message": "He notado que cuando hago ejercicio por la mañana, mi día es mejor",
            "context": []
        },
        {
            "name": "Estado de ánimo bajo",
            "message": "hoy estoy como un 3, no tengo ganas de nada",
            "context": []
        }
    ]
    
    for i, scenario in enumerate(scenarios, 1):
        print(f"\n{'='*70}")
        print(f"Escenario {i}: {scenario['name']}")
        print(f"{'='*70}")
        print(f"📨 Usuario dice: \"{scenario['message']}\"")
        print(f"\nGenerando respuesta de Loki...\n")
        
        try:
            respuesta = await loki_service.generate_response(
                mensaje_usuario=scenario['message'],
                usuario_nombre="Diego",
                contexto_reciente=scenario['context']
            )
            
            print(f"🤖 Loki responde:")
            print(f"   {respuesta}")
            
            # Extraer nivel de ánimo
            mood_level = loki_service.extract_mood_level(scenario['message'])
            if mood_level:
                print(f"\n📊 Nivel de ánimo detectado: {mood_level}/10")
            
            # Detectar hábitos
            habits = loki_service.detect_habits(scenario['message'])
            if habits:
                print(f"✅ Hábitos detectados: {', '.join(habits)}")
                
        except Exception as e:
            print(f"❌ Error: {e}")
            import traceback
            traceback.print_exc()
    
    print(f"\n{'='*70}")
    print("✅ Prueba completada!")
    print(f"{'='*70}\n")

if __name__ == "__main__":
    asyncio.run(test_new_loki())
