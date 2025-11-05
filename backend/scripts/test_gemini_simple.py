"""
Script simple para probar Gemini directamente.
"""

import google.generativeai as genai
import os
from dotenv import load_dotenv

load_dotenv()

google_key = os.getenv('GOOGLE_API_KEY')

if not google_key:
    print("❌ GOOGLE_API_KEY no encontrada")
    exit(1)

genai.configure(api_key=google_key)

# Safety settings permisivos
from google.generativeai.types import HarmCategory, HarmBlockThreshold

safety_settings = {
    HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
    HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
    HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_NONE,
    HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE,
}

model = genai.GenerativeModel('gemini-2.5-flash')

print("🧪 PRUEBA DIRECTA DE GEMINI")
print("=" * 60)

# Prueba simple
prompt = """Hola! ¿Cómo estás?"""

print(f"📤 Enviando: {prompt}")
print()

try:
    # Sin safety settings primero
    response = model.generate_content(
        prompt,
        generation_config=genai.types.GenerationConfig(
            max_output_tokens=100,
            temperature=0.8,
        )
    )
    
    print(f"✅ Respuesta:")
    print(f"   {response.text}")
    print()
    print(f"Finish reason: {response.candidates[0].finish_reason}")
    
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()

print("=" * 60)
