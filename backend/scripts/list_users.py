"""
Script para listar todos los usuarios y sus nombres.
"""

import sys
from pathlib import Path

# Agregar el directorio raíz al path
root_dir = Path(__file__).parent.parent
sys.path.insert(0, str(root_dir))

from app.db.session import SessionLocal
from app.models.mood import Usuario


def list_users():
    """Lista todos los usuarios."""
    db = SessionLocal()
    
    try:
        usuarios = db.query(Usuario).all()
        
        if not usuarios:
            print("No hay usuarios registrados.")
            return
        
        print(f"\n{'='*80}")
        print(f"{'ID':<5} | {'Nombre':<30} | {'Teléfono':<20} | {'Creado':<20}")
        print(f"{'='*80}")
        
        for u in usuarios:
            created = u.created_at.strftime("%Y-%m-%d %H:%M") if u.created_at else "N/A"
            print(f"{u.id:<5} | {u.nombre:<30} | {u.telefono or 'N/A':<20} | {created:<20}")
        
        print(f"{'='*80}")
        print(f"Total de usuarios: {len(usuarios)}\n")
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")
    finally:
        db.close()


if __name__ == "__main__":
    list_users()
