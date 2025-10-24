"""
Script de prueba para Loki MoodTracker
"""
import requests
import json
import time

BASE_URL = "http://localhost:8000/api/v1"

def test_loki():
    print("🎭 Iniciando pruebas de Loki MoodTracker...\n")
    
    # 1. Crear o obtener usuario
    print("📝 Paso 1: Creando usuario Diego...")
    usuario_data = {
        "nombre": "Diego",
        "telefono": "+541165992142",
        "timezone": "America/Argentina/Buenos_Aires"
    }
    
    try:
        response = requests.post(f"{BASE_URL}/usuarios/", json=usuario_data)
        if response.status_code == 400 and "ya está registrado" in response.text:
            print("ℹ️  Usuario ya existe, obteniendo información...")
            # Obtener lista de usuarios y buscar por teléfono
            response = requests.get(f"{BASE_URL}/usuarios/")
            usuarios = response.json()
            usuario = next((u for u in usuarios if u['telefono'] == usuario_data['telefono']), None)
            if not usuario:
                print("❌ No se pudo encontrar el usuario existente")
                return
        elif response.status_code != 200:
            print(f"❌ Error {response.status_code}: {response.text}")
            return
        else:
            usuario = response.json()
            print(f"✅ Usuario creado exitosamente!")
        
        print(f"   ID: {usuario['id']}")
        print(f"   Nombre: {usuario['nombre']}")
        print(f"   Teléfono: {usuario['telefono']}")
        print(f"   Timezone: {usuario['timezone']}\n")
        
        usuario_id = usuario['id']
        
    except requests.exceptions.ConnectionError:
        print("❌ Error: No se puede conectar al servidor.")
        print("   Asegúrate de que el servidor esté corriendo en otra terminal con:")
        print("   cd C:\\Users\\Diego\\Desktop\\programacion\\experimentos\\moodtracker\\backend")
        print("   python -m uvicorn app.main:app --reload\n")
        return
    except Exception as e:
        print(f"❌ Error creando usuario: {e}\n")
        return
    
    # 2. Enviar mensaje a Loki
    print("💬 Paso 2: Enviando mensaje a Loki...")
    mensaje_data = {
        "usuario_id": usuario_id,
        "mensaje": "Hola Loki, hoy me siento muy bien, un 8 de 10. Hice ejercicio y dormí bien."
    }
    
    try:
        response = requests.post(f"{BASE_URL}/chat/", json=mensaje_data)
        response.raise_for_status()
        chat_response = response.json()
        
        print(f"✅ Mensaje enviado!")
        print(f"\n🎭 Respuesta de Loki:")
        print(f"   {chat_response['respuesta']}\n")
        
        if chat_response.get('mood_registrado'):
            print(f"😊 Estado de ánimo registrado exitosamente!\n")
        
        if chat_response.get('habitos_detectados'):
            print(f"✅ Hábitos detectados: {', '.join(chat_response['habitos_detectados'])}\n")
            
    except Exception as e:
        print(f"❌ Error enviando mensaje: {e}\n")
        return
    
    # 3. Ver historial
    print("📜 Paso 3: Consultando historial de conversaciones...")
    try:
        response = requests.get(f"{BASE_URL}/chat/history/{usuario_id}")
        response.raise_for_status()
        historial_data = response.json()
        
        conversaciones = historial_data['conversaciones']
        print(f"✅ Historial recuperado ({historial_data['total_conversaciones']} conversaciones):\n")
        for conv in conversaciones:
            print(f"   📅 {conv['timestamp']}")
            print(f"   👤 Tú: {conv['mensaje']}")
            print(f"   🎭 Loki: {conv['respuesta']}\n")
            
    except Exception as e:
        print(f"❌ Error consultando historial: {e}\n")
        return
    
    # 4. Consultar estados de ánimo
    print("📊 Paso 4: Consultando estados de ánimo registrados...")
    try:
        response = requests.get(f"{BASE_URL}/usuarios/{usuario_id}/estados_animo/")
        response.raise_for_status()
        estados = response.json()
        
        print(f"✅ Estados de ánimo registrados: {len(estados)}")
        for estado in estados:
            print(f"   📅 {estado['timestamp']}: Nivel {estado['nivel']}/10")
            if estado['nota']:
                print(f"      Nota: {estado['nota']}")
        print()
            
    except Exception as e:
        print(f"❌ Error consultando estados: {e}\n")
    
    print("🎉 ¡Pruebas completadas exitosamente!")
    print("\n💡 Próximos pasos:")
    print("   - Envía más mensajes con diferentes estados de ánimo")
    print("   - Menciona diferentes hábitos (meditación, lectura, alimentación, etc.)")
    print("   - Explora la API en http://localhost:8000/docs")

if __name__ == "__main__":
    test_loki()
