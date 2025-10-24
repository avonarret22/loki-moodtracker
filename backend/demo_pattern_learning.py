"""
Demo: Sistema de Aprendizaje de Patrones de Loki
Simula varios días de datos para demostrar cómo Loki aprende patrones personales.
"""
import asyncio
import sys
import os
from datetime import datetime, timedelta
import random

sys.path.insert(0, os.path.dirname(__file__))

from app.db.session import SessionLocal
from app import crud, schemas
from app.services.ai_service import loki_service
from app.services.pattern_analysis import pattern_service


async def demo_pattern_learning():
    """
    Demuestra el aprendizaje de patrones de Loki.
    """
    print("\n" + "="*70)
    print("🧠 DEMO: Sistema de Aprendizaje de Patrones de Loki")
    print("="*70 + "\n")
    
    db = SessionLocal()
    
    try:
        # 1. Crear usuario de prueba
        print("👤 Creando usuario de prueba...")
        usuario = crud.get_usuario_by_telefono(db, telefono="+5491177777777")
        
        if not usuario:
            usuario_data = schemas.UsuarioCreate(
                nombre="Test Pattern User",
                telefono="+5491177777777"
            )
            usuario = crud.create_usuario(db, usuario=usuario_data)
        
        print(f"   Usuario ID: {usuario.id} - {usuario.nombre}\n")
        
        # 2. Simular 20 días de datos con patrones claros
        print("📊 Simulando 20 días de datos...")
        print("   Patrón: Cuando hace ejercicio → Ánimo alto (7-9)")
        print("   Patrón: Cuando NO hace ejercicio → Ánimo bajo (3-5)")
        print("   Patrón: Dormir bien → Ánimo mejorado (+1)\n")
        
        for day in range(20):
            date = datetime.now() - timedelta(days=20-day)
            
            # 70% de días hace ejercicio
            did_exercise = random.random() < 0.7
            slept_well = random.random() < 0.6
            
            # Calcular ánimo basado en hábitos
            if did_exercise:
                base_mood = random.randint(7, 9)
            else:
                base_mood = random.randint(3, 5)
            
            if slept_well:
                base_mood = min(10, base_mood + 1)
            
            # Registrar estado de ánimo
            estado_data = schemas.EstadoAnimoCreate(
                nivel=base_mood,
                notas_texto=f"Día {day+1} de simulación",
                contexto_extraido="{}",
                disparadores_detectados="[]"
            )
            estado = crud.create_estado_animo(db, estado_animo=estado_data, usuario_id=usuario.id)
            estado.timestamp = date  # Ajustar fecha
            db.commit()
            
            # Registrar hábitos
            if did_exercise:
                # Crear/obtener hábito de ejercicio
                habitos = crud.get_habitos_by_usuario(db, usuario_id=usuario.id)
                exercise_habit = next((h for h in habitos if h.nombre_habito == "ejercicio"), None)
                
                if not exercise_habit:
                    habit_data = schemas.HabitoCreate(
                        nombre_habito="ejercicio",
                        categoria="ejercicio",
                        objetivo_semanal=5
                    )
                    exercise_habit = crud.create_habito(db, habito=habit_data, usuario_id=usuario.id)
                
                # Registrar que hizo ejercicio
                registro_data = schemas.RegistroHabitoCreate(
                    habito_id=exercise_habit.id,
                    completado=True,
                    notas=f"Ejercicio día {day+1}"
                )
                registro = crud.create_registro_habito(db, registro=registro_data, usuario_id=usuario.id)
                registro.timestamp = date
                db.commit()
            
            if slept_well:
                # Crear/obtener hábito de sueño
                habitos = crud.get_habitos_by_usuario(db, usuario_id=usuario.id)
                sleep_habit = next((h for h in habitos if h.nombre_habito == "sueño"), None)
                
                if not sleep_habit:
                    habit_data = schemas.HabitoCreate(
                        nombre_habito="sueño",
                        categoria="sueño",
                        objetivo_semanal=7
                    )
                    sleep_habit = crud.create_habito(db, habito=habit_data, usuario_id=usuario.id)
                
                # Registrar que durmió bien
                registro_data = schemas.RegistroHabitoCreate(
                    habito_id=sleep_habit.id,
                    completado=True,
                    notas=f"Buen sueño día {day+1}"
                )
                registro = crud.create_registro_habito(db, registro=registro_data, usuario_id=usuario.id)
                registro.timestamp = date
                db.commit()
        
        print("✅ Datos simulados correctamente\n")
        
        # 3. Analizar patrones
        print("🔍 Analizando patrones personales...\n")
        analysis = pattern_service.analyze_user_patterns(db, usuario.id, days_lookback=30)
        
        if not analysis.get('has_enough_data'):
            print("❌ No hay suficientes datos")
            return
        
        print(f"📈 Análisis completado:")
        print(f"   • Puntos de datos: {analysis['data_points']}")
        print(f"   • Ánimo promedio: {analysis['average_mood']:.1f}/10")
        print(f"   • Estabilidad (desv. est.): {analysis['mood_stability']:.2f}\n")
        
        # 4. Mostrar correlaciones
        correlations = analysis.get('correlations', [])
        if correlations:
            print("🎯 Correlaciones Detectadas:\n")
            for i, corr in enumerate(correlations, 1):
                emoji = "📈" if corr['impact'] > 0 else "📉"
                print(f"{emoji} {i}. {corr['habit'].upper()}")
                print(f"      Impacto: {corr['impact']:+.3f} (confianza: {corr['confidence']:.0%})")
                print(f"      Ánimo CON hábito: {corr['avg_mood_with']:.1f}/10")
                print(f"      Ánimo SIN hábito: {corr['avg_mood_without']:.1f}/10")
                print(f"      Ocurrencias: {corr['occurrences']}")
                print(f"      💡 {corr['interpretation']}\n")
        
        # 5. Mostrar insights
        insights = analysis.get('insights', [])
        if insights:
            print("💡 Insights Generados:\n")
            for i, insight in enumerate(insights, 1):
                print(f"   {i}. {insight}\n")
        
        # 6. Demostrar uso en conversación
        print("\n" + "="*70)
        print("💬 Demostración de Uso en Conversación")
        print("="*70 + "\n")
        
        # Simular usuario diciendo que se siente mal
        print("Usuario: Me siento mal hoy, como un 3\n")
        
        # Loki debería sugerir ejercicio basado en patrones
        insight = pattern_service.get_relevant_insights_for_conversation(
            db, usuario.id, current_mood=3
        )
        
        if insight:
            print(f"🤖 Loki (con análisis de patrones):")
            print(f"   {insight}\n")
        else:
            print("⚠️ No se generó insight específico\n")
        
        # Generar respuesta completa con Claude
        print("Generando respuesta completa de Loki...\n")
        ai_response = await loki_service.generate_response(
            mensaje_usuario="Me siento mal hoy, como un 3",
            usuario_nombre=usuario.nombre,
            contexto_reciente=[],
            db_session=db,
            usuario_id=usuario.id
        )
        
        print(f"🤖 Loki responde:")
        print(f"   {ai_response['respuesta']}\n")
        
        if ai_response.get('pattern_insight_used'):
            print(f"📊 Insight usado: {ai_response['pattern_insight_used']}\n")
        
        print("="*70)
        print("✅ Demo completada exitosamente!")
        print("="*70 + "\n")
        
    finally:
        db.close()


if __name__ == "__main__":
    asyncio.run(demo_pattern_learning())
