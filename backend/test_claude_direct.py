"""
Test directo de la integración con Claude API
"""
import asyncio
from app.services.ai_service import loki_service

async def test_claude():
    print("🧪 Probando integración directa con Claude...")
    print(f"✅ Cliente inicializado: {loki_service.claude_client is not None}")
    
    if not loki_service.claude_client:
        print("❌ Claude client no está inicializado")
        return
    
    # Test simple
    try:
        response = await loki_service.generate_response(
            mensaje_usuario="Hola, hoy me siento un 8 de 10",
            usuario_nombre="Diego",
            contexto_reciente=[]
        )
        
        print("\n📝 Respuesta generada:")
        print(f"   {response['respuesta']}")
        print(f"\n📊 Contexto extraído:")
        print(f"   {response['context_extracted']}")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_claude())
