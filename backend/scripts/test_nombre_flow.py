"""
Test para verificar el flujo de cambio de nombre
"""

from app.services.ai_service import LokiAIService

def test_cambio_nombre_flow():
    """
    Simula el flujo completo de cambio de nombre:
    1. Usuario: "cual es mi nombre?"
    2. Loki: "Tu nombre es Diego. ¿Quieres que lo cambie?"
    3. Usuario: "si"
    4. Loki: "¿Cómo quieres que te llame?"
    5. Usuario: "pablo"
    6. Loki: "¡Perfecto, Pablo! Te recordaré con ese nombre..."
    """
    
    loki = LokiAIService()
    
    print("\n=== TEST: Flujo de Cambio de Nombre ===\n")
    
    # 1. Usuario pregunta por su nombre
    print("👤 Usuario: cual es mi nombre?")
    response1 = loki.process_message(
        mensaje_usuario="cual es mi nombre?",
        usuario_nombre="Diego",
        usuario_id=1,
        contexto_reciente=[]
    )
    print(f"🤖 Loki: {response1['respuesta']}")
    print(f"📊 Context: {response1['context_extracted']}")
    
    assert response1['context_extracted'].get('esperando_confirmacion_cambio_nombre') == True
    print("✅ PASO 1: Detectó pregunta de nombre y preguntó si quiere cambiar\n")
    
    # 2. Usuario dice "si"
    print("👤 Usuario: si")
    contexto_1 = [{'entidades_extraidas': response1['context_extracted']}]
    response2 = loki.process_message(
        mensaje_usuario="si",
        usuario_nombre="Diego",
        usuario_id=1,
        contexto_reciente=contexto_1
    )
    print(f"🤖 Loki: {response2['respuesta']}")
    print(f"📊 Context: {response2['context_extracted']}")
    
    assert response2['context_extracted'].get('esperando_nuevo_nombre') == True
    assert "cómo quieres que te llame" in response2['respuesta'].lower()
    print("✅ PASO 2: Entendió 'si' y preguntó el nuevo nombre\n")
    
    # 3. Usuario dice su nuevo nombre
    print("👤 Usuario: pablo")
    contexto_2 = [
        {'entidades_extraidas': response1['context_extracted']},
        {'entidades_extraidas': response2['context_extracted']}
    ]
    response3 = loki.process_message(
        mensaje_usuario="pablo",
        usuario_nombre="Diego",
        usuario_id=1,
        contexto_reciente=contexto_2
    )
    print(f"🤖 Loki: {response3['respuesta']}")
    print(f"📊 Nombre detectado: {response3.get('nombre_detectado')}")
    
    assert response3.get('nombre_detectado') == "Pablo"
    assert "pablo" in response3['respuesta'].lower()
    print("✅ PASO 3: Detectó el nuevo nombre y confirmó el cambio\n")
    
    print("🎉 ¡TODOS LOS TESTS PASARON!\n")

def test_rechazar_cambio_nombre():
    """
    Flujo cuando el usuario NO quiere cambiar el nombre
    """
    loki = LokiAIService()
    
    print("\n=== TEST: Rechazar Cambio de Nombre ===\n")
    
    # 1. Usuario pregunta por su nombre
    print("👤 Usuario: cual es mi nombre?")
    response1 = loki.process_message(
        mensaje_usuario="cual es mi nombre?",
        usuario_nombre="Diego",
        usuario_id=1,
        contexto_reciente=[]
    )
    print(f"🤖 Loki: {response1['respuesta']}")
    
    # 2. Usuario dice "no"
    print("👤 Usuario: no")
    contexto_1 = [{'entidades_extraidas': response1['context_extracted']}]
    response2 = loki.process_message(
        mensaje_usuario="no",
        usuario_nombre="Diego",
        usuario_id=1,
        contexto_reciente=contexto_1
    )
    print(f"🤖 Loki: {response2['respuesta']}")
    
    assert response2.get('nombre_detectado') is None
    assert "perfecto" in response2['respuesta'].lower() or "diego" in response2['respuesta'].lower()
    print("✅ Entendió 'no' y mantuvo el nombre actual\n")
    
    print("🎉 TEST PASÓ!\n")

if __name__ == "__main__":
    test_cambio_nombre_flow()
    test_rechazar_cambio_nombre()
