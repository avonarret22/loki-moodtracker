"""
Script para corregir el nombre de Diego en la base de datos de Railway.
Actualiza "Diego Recuerdalo" a "Diego" o None para que se vuelva a detectar.
"""

import sys
import os

# Agregar el directorio backend al path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.db.session import get_db
from app.models.mood import Usuario
from sqlalchemy.orm import Session


def fix_diego_name():
    """Corrige el nombre de Diego en la base de datos."""
    db = next(get_db())
    
    try:
        # Buscar usuarios con nombre "Diego Recuerdalo" o similar
        usuarios = db.query(Usuario).filter(
            Usuario.nombre.like("%Recuerdalo%")
        ).all()
        
        if not usuarios:
            print("ℹ️  No se encontraron usuarios con 'Recuerdalo' en el nombre")
            
            # Buscar todos los usuarios para ver qué hay
            todos = db.query(Usuario).all()
            print(f"\n📋 Usuarios en la base de datos ({len(todos)}):")
            for u in todos:
                print(f"   - ID: {u.id} | Nombre: '{u.nombre}' | Tel: {u.telefono}")
            
            return
        
        print(f"🔍 Encontrados {len(usuarios)} usuarios con 'Recuerdalo' en el nombre:\n")
        
        for usuario in usuarios:
            print(f"   ID: {usuario.id}")
            print(f"   Nombre actual: '{usuario.nombre}'")
            print(f"   Teléfono: {usuario.telefono}")
            print(f"   Fecha registro: {usuario.fecha_registro}")
            
            # Opción 1: Cambiar a None para que se vuelva a detectar
            # usuario.nombre = None
            
            # Opción 2: Corregir a "Diego" directamente
            if "Diego" in usuario.nombre:
                nuevo_nombre = "Diego"
                usuario.nombre = nuevo_nombre
                print(f"   ✅ Actualizado a: '{nuevo_nombre}'")
            else:
                usuario.nombre = None
                print(f"   ✅ Nombre eliminado (se volverá a detectar)")
            
            print()
        
        # Guardar cambios
        db.commit()
        print(f"💾 Cambios guardados en la base de datos")
        
        # Verificar cambios
        print("\n📋 Verificación de cambios:")
        for usuario in usuarios:
            db.refresh(usuario)
            print(f"   ID: {usuario.id} | Nombre: '{usuario.nombre}'")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        db.rollback()
        import traceback
        traceback.print_exc()
    finally:
        db.close()


if __name__ == "__main__":
    print("🔧 Script para corregir nombre de Diego en Railway")
    print("="*60)
    fix_diego_name()
