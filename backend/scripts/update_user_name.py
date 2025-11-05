"""
Script para actualizar manualmente el nombre de un usuario.
Útil cuando el nombre no se guardó correctamente.
"""

import sys
from pathlib import Path

# Agregar el directorio raíz al path
root_dir = Path(__file__).parent.parent
sys.path.insert(0, str(root_dir))

from app.db.session import SessionLocal
from app.models.mood import Usuario


def update_user_name(usuario_id: int, nuevo_nombre: str):
    """Actualiza el nombre de un usuario."""
    db = SessionLocal()
    
    try:
        usuario = db.query(Usuario).filter(Usuario.id == usuario_id).first()
        if not usuario:
            print(f"❌ Error: Usuario con ID {usuario_id} no encontrado.")
            return False
        
        nombre_anterior = usuario.nombre
        usuario.nombre = nuevo_nombre
        db.commit()
        
        print(f"✅ Nombre actualizado exitosamente!")
        print(f"   Anterior: '{nombre_anterior}'")
        print(f"   Nuevo: '{nuevo_nombre}'")
        print(f"   Usuario ID: {usuario_id}")
        print(f"   Teléfono: {usuario.telefono}")
        
        return True
        
    except Exception as e:
        db.rollback()
        print(f"❌ Error: {str(e)}")
        return False
    finally:
        db.close()


def main():
    if len(sys.argv) < 3:
        print("Uso: python scripts/update_user_name.py <usuario_id> <nuevo_nombre>")
        print("\nEjemplo:")
        print("  python scripts/update_user_name.py 1 Diego")
        sys.exit(1)
    
    usuario_id = int(sys.argv[1])
    nuevo_nombre = " ".join(sys.argv[2:])  # Permitir nombres con espacios
    
    print(f"\n{'='*60}")
    print(f"🔄 Actualizando nombre de usuario")
    print(f"{'='*60}\n")
    
    success = update_user_name(usuario_id, nuevo_nombre)
    
    if success:
        print(f"\n✅ Ahora Loki te llamará '{nuevo_nombre}' en los próximos mensajes.")
    else:
        print(f"\n❌ No se pudo actualizar el nombre.")
        sys.exit(1)


if __name__ == "__main__":
    main()
