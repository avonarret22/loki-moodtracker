"""
Script de prueba para verificar la integración con Google Gemini.
"""

import sys
from pathlib import Path

# Agregar el directorio raíz al path
root_dir = Path(__file__).parent.parent
sys.path.insert(0, str(root_dir))

from app.services.ai_service import loki_service

print("=" * 60)
print("🧪 PRUEBA DE INTEGRACIÓN CON GOOGLE GEMINI")
print("=" * 60)
print()

# Verificar qué proveedor de IA está activo
print(f"🤖 Proveedor de IA: {loki_service.ai_provider}")
print()

if loki_service.ai_provider == 'gemini':
    print("✅ Google Gemini está configurado")
    print()
    
    # Hacer una prueba simple
    test_message = "Hola, soy Diego"
    print(f"📤 Mensaje de prueba: '{test_message}'")
    print()
    
    try:
        import asyncio
        
        async def test_response():
            response = await loki_service.generate_response(
                mensaje_usuario=test_message,
                usuario_nombre="Diego",
                contexto_reciente=[]
            )
            return response
        
        result = asyncio.run(test_response())
        
        print("📥 Respuesta recibida:")
        print(f"   {result['respuesta']}")
        print()
        
        if result.get('nombre_detectado'):
            print(f"✅ Nombre detectado: {result['nombre_detectado']}")
        
        print()
        print("=" * 60)
        print("✅ PRUEBA EXITOSA - Gemini funcionando correctamente")
        print("=" * 60)
        
    except Exception as e:
        print(f"❌ Error en la prueba: {e}")
        print()
        import traceback
        traceback.print_exc()
        
elif loki_service.ai_provider == 'claude':
    print("⚠️ Usando Claude API (Gemini no configurado)")
    print("   Configura GOOGLE_API_KEY en .env para usar Gemini")
    
else:
    print("❌ No hay proveedor de IA configurado")
    print("   Configura GOOGLE_API_KEY en .env")

print()
