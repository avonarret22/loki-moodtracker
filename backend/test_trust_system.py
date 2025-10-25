"""
Script de prueba para el sistema de niveles de confianza.
Simula la evolución de Loki con un usuario a través de diferentes niveles.
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.db.session import SessionLocal
from app.services.trust_level_service import trust_service
from app import crud
from app.schemas import UsuarioCreate
from app.models.mood import Usuario


def test_trust_evolution():
    """Prueba la evolución del nivel de confianza."""
    db = SessionLocal()

    try:
        # Crear usuario de prueba
        print(">> Creando usuario de prueba...")
        usuario_data = UsuarioCreate(
            nombre="Test User",
            telefono="+99999999999",
            timezone="UTC"
        )

        # Verificar si ya existe
        existing = db.query(Usuario).filter(
            Usuario.telefono == usuario_data.telefono
        ).first()

        if existing:
            print(f">> Usuario ya existe (ID: {existing.id}), usando existente...")
            usuario = existing
        else:
            usuario = crud.create_usuario(db, usuario=usuario_data)
            print(f">> Usuario creado (ID: {usuario.id})")

        print(f"\n>> Estado inicial:")
        print(f"   - Nivel de confianza: {usuario.nivel_confianza}")
        print(f"   - Total interacciones: {usuario.total_interacciones}")

        # Simular evolución a través de los niveles
        print("\n>> Simulando evolución de niveles...\n")

        milestones = [1, 5, 10, 11, 20, 30, 31, 50, 60, 61, 80, 100, 101, 120]

        for target in milestones:
            # Actualizar interacciones hasta el target
            while usuario.total_interacciones < target:
                trust_update = trust_service.update_trust_level(db, usuario.id)

                if trust_update.get('nivel_cambio'):
                    print(f"   [{usuario.total_interacciones:3d} mensajes] -> NIVEL UP! Ahora: {trust_update['nivel_info']['name']} (Nivel {trust_update['nivel_confianza']})")
                    print(f"      Tono: {trust_update['nivel_info']['tone']}")
                    print(f"      Max oraciones: {trust_update['nivel_info']['max_sentences']}")
                    print()

                # Refrescar usuario
                db.refresh(usuario)

        print(f"\n>> Estado final:")
        final_info = trust_service.get_user_trust_info(db, usuario.id)
        print(f"   - Nivel de confianza: {final_info['nivel_confianza']} ({final_info['nivel_nombre']})")
        print(f"   - Total interacciones: {final_info['total_interacciones']}")
        print(f"   - Descripción: {final_info['nivel_descripcion']}")
        print(f"   - Tono: {final_info['tone']}")
        print(f"   - Enfoque: {final_info['approach']}")
        print(f"   - Es nivel máximo: {final_info['es_nivel_maximo']}")

        print("\n>> Prueba completada exitosamente!")

    except Exception as e:
        print(f">> Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()


if __name__ == "__main__":
    test_trust_evolution()
