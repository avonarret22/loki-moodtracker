"""
Script de prueba para verificar la detección de nombres.
"""

import sys
from pathlib import Path

# Agregar el directorio raíz al path
root_dir = Path(__file__).parent.parent
sys.path.insert(0, str(root_dir))

from app.services.ai_service import loki_service

# Casos de prueba
test_cases = [
    "me llamo Diego",
    "me allmo diego",  # Error de tipeo
    "me yamo Diego",   # Error de tipeo
    "debes llamarme Diego",
    "debes llamarme por mi nombre diego",
    "mi nombre es Diego",
    "soy Diego",
    "Diego",
    # NUEVOS CASOS
    "registra mi nombre, es Diego",
    "cambialo de usuario a Diego",
    "registra mi nombre Diego",
    "cambia mi nombre a Diego",
    "mi nombre es Diego ahora",
]

print("=" * 60)
print("🧪 PRUEBA DE DETECCIÓN DE NOMBRES")
print("=" * 60)

for i, mensaje in enumerate(test_cases, 1):
    nombre = loki_service._extract_name_from_message(mensaje)
    status = "✅" if nombre == "Diego" else "❌"
    print(f"{status} Test {i}: '{mensaje}'")
    print(f"   → Nombre detectado: {nombre}")
    print()

print("=" * 60)
print("✅ Pruebas completadas")
print("=" * 60)
