"""
Script para listar los modelos disponibles en Google Gemini.
"""

import google.generativeai as genai
import os
from dotenv import load_dotenv

load_dotenv()

google_key = os.getenv('GOOGLE_API_KEY')

if not google_key:
    print("❌ GOOGLE_API_KEY no encontrada en .env")
    exit(1)

genai.configure(api_key=google_key)

print("=" * 60)
print("📋 MODELOS DISPONIBLES EN GOOGLE GEMINI")
print("=" * 60)
print()

for model in genai.list_models():
    if 'generateContent' in model.supported_generation_methods:
        print(f"✅ {model.name}")
        print(f"   Display Name: {model.display_name}")
        print(f"   Métodos: {', '.join(model.supported_generation_methods)}")
        print()

print("=" * 60)
