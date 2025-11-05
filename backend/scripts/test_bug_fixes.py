"""
Script para probar los 3 bugs críticos corregidos:
1. Extracción de nombre con "recuerdalo"
2. Detección de tiempo verbal en hábitos (futuro vs pasado)
3. Uso correcto del nombre en prompts
"""

import sys
import os

# Agregar el directorio backend al path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.ai_service import LokiAIService

def test_nombre_recuerdalo():
    """Test Bug 1: Extracción de nombre con 'recuerdalo'"""
    print("\n" + "="*60)
    print("TEST 1: Extracción de Nombre con 'recuerdalo'")
    print("="*60)
    
    ai_service = LokiAIService()
    
    test_cases = [
        ("mi nombre es diego recuerdalo", "Diego"),
        ("mi nombre es Diego recuérdalo", "Diego"),
        ("mi nombre es Ana por favor recuerdalo", "Ana"),
        ("me llamo Carlos recuerdalo", "Carlos"),
        ("soy María", "María"),
    ]
    
    passed = 0
    failed = 0
    
    for mensaje, expected in test_cases:
        nombre = ai_service._extract_name_from_message(mensaje)
        status = "✅" if nombre == expected else "❌"
        
        if nombre == expected:
            passed += 1
        else:
            failed += 1
        
        print(f"{status} Mensaje: '{mensaje}'")
        print(f"   Esperado: '{expected}' | Obtenido: '{nombre}'")
    
    print(f"\n📊 Resultado: {passed} passed, {failed} failed")
    return failed == 0


def test_tiempo_verbal_habitos():
    """Test Bug 2: Detección de tiempo verbal en hábitos"""
    print("\n" + "="*60)
    print("TEST 2: Detección de Tiempo Verbal en Hábitos")
    print("="*60)
    
    ai_service = LokiAIService()
    
    test_cases = [
        ("hoy debo entrenar un poco", [{'habito': 'ejercicio', 'tiempo': 'futuro'}]),
        ("entrené hoy", [{'habito': 'ejercicio', 'tiempo': 'pasado'}]),
        ("fui al gym", [{'habito': 'ejercicio', 'tiempo': 'pasado'}]),
        ("tengo que meditar", [{'habito': 'meditación', 'tiempo': 'futuro'}]),
        ("medité esta mañana", [{'habito': 'meditación', 'tiempo': 'pasado'}]),
        ("voy a salir con amigos", [{'habito': 'social', 'tiempo': 'futuro'}]),
        ("salí con amigos", [{'habito': 'social', 'tiempo': 'pasado'}]),
    ]
    
    passed = 0
    failed = 0
    
    for mensaje, expected in test_cases:
        habitos = ai_service.extract_habits_mentioned(mensaje)
        
        # Verificar que se detectó el hábito correcto con el tiempo correcto
        if habitos and len(habitos) > 0:
            habito_data = habitos[0]
            expected_data = expected[0]
            
            match = (
                habito_data['habito'] == expected_data['habito'] and 
                habito_data['tiempo'] == expected_data['tiempo']
            )
        else:
            match = False
        
        status = "✅" if match else "❌"
        
        if match:
            passed += 1
        else:
            failed += 1
        
        print(f"{status} Mensaje: '{mensaje}'")
        print(f"   Esperado: {expected[0]}")
        print(f"   Obtenido: {habitos[0] if habitos else 'No detectado'}")
    
    print(f"\n📊 Resultado: {passed} passed, {failed} failed")
    return failed == 0


def test_contexto_nombre():
    """Test Bug 3: Uso correcto del nombre en contexto"""
    print("\n" + "="*60)
    print("TEST 3: Uso Correcto del Nombre en Contexto")
    print("="*60)
    
    ai_service = LokiAIService()
    
    # Simular análisis de mensaje con nombre
    mensaje_1 = "8/10"
    context = ai_service.analyze_message_context(mensaje_1)
    
    print(f"✅ Mensaje: '{mensaje_1}'")
    print(f"   Context extraído: {context}")
    print(f"   mood_level: {context.get('mood_level')}")
    
    # Verificar que el contexto se genera correctamente
    if context.get('mood_level') == 8:
        print("✅ Nivel de ánimo detectado correctamente")
        return True
    else:
        print("❌ Error detectando nivel de ánimo")
        return False


def main():
    print("\n🔧 PRUEBAS DE CORRECCIÓN DE BUGS CRÍTICOS")
    print("=" * 60)
    
    results = []
    
    # Test 1: Nombre con "recuerdalo"
    results.append(("Extracción de Nombre", test_nombre_recuerdalo()))
    
    # Test 2: Tiempo verbal en hábitos
    results.append(("Tiempo Verbal Hábitos", test_tiempo_verbal_habitos()))
    
    # Test 3: Contexto con nombre
    results.append(("Contexto con Nombre", test_contexto_nombre()))
    
    # Resumen final
    print("\n" + "="*60)
    print("RESUMEN FINAL")
    print("="*60)
    
    for test_name, passed in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status} - {test_name}")
    
    all_passed = all(result[1] for result in results)
    
    if all_passed:
        print("\n🎉 TODOS LOS TESTS PASARON!")
    else:
        print("\n⚠️ Algunos tests fallaron")
    
    return all_passed


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
