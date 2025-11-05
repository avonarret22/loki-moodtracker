"""
Debug para ver qué está bloqueando Gemini
"""

import google.generativeai as genai
import os
from dotenv import load_dotenv

load_dotenv()

google_key = os.getenv('GOOGLE_API_KEY')
genai.configure(api_key=google_key)

from google.generativeai.types import HarmCategory, HarmBlockThreshold

safety_settings = {
    HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_ONLY_HIGH,
    HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_ONLY_HIGH,
    HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_ONLY_HIGH,
    HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_ONLY_HIGH,
}

model = genai.GenerativeModel('gemini-2.5-flash')

# Prompt super simple
simple_prompt = "Un usuario llamado Diego te saluda diciendo 'Hola, soy Diego'. Responde de forma amigable y breve."

print("=" * 80)
print("🔍 DEBUG: ¿Qué está bloqueando Gemini?")
print("=" * 80)
print()
print("📤 PROMPT:")
print(simple_prompt)
print()
print("=" * 80)

response = model.generate_content(
    simple_prompt,
    generation_config=genai.types.GenerationConfig(
        max_output_tokens=300,
        temperature=0.8,
    ),
    safety_settings=safety_settings
)

print()
print("📥 RESPUESTA COMPLETA:")
print(f"Candidates: {len(response.candidates) if response.candidates else 0}")

if response.candidates:
    candidate = response.candidates[0]
    print(f"Finish reason: {candidate.finish_reason}")
    print(f"Safety ratings: {candidate.safety_ratings}")
    print()
    
    if candidate.content and candidate.content.parts:
        print(f"✅ TEXTO: {response.text}")
    else:
        print("❌ No hay partes en la respuesta")
        print(f"Content: {candidate.content}")

print("=" * 80)
