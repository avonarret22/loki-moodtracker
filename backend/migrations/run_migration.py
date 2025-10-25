"""
Script para ejecutar la migración de nivel de confianza.
Agrega los campos necesarios a la tabla de usuarios.
"""
import sys
import os

# Agregar el directorio parent al path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import text
from app.db.session import engine


def run_migration():
    """Ejecuta la migración de base de datos."""
    print(">> Ejecutando migracion: Agregar campos de nivel de confianza...")

    # Leer el archivo SQL
    sql_file = os.path.join(os.path.dirname(__file__), "add_trust_level_fields.sql")

    with open(sql_file, 'r', encoding='utf-8') as f:
        sql_content = f.read()

    # Ejecutar la migración
    try:
        with engine.connect() as conn:
            # Ejecutar cada statement por separado
            statements = [s.strip() for s in sql_content.split(';') if s.strip() and not s.strip().startswith('--')]

            for statement in statements:
                if statement:
                    print(f">> Ejecutando: {statement[:60]}...")
                    conn.execute(text(statement))

            conn.commit()
            print(">> Migracion completada exitosamente!")
            print("\n>> Campos agregados:")
            print("  - usuarios.nivel_confianza (INTEGER, default 1)")
            print("  - usuarios.total_interacciones (INTEGER, default 0)")

    except Exception as e:
        print(f">> Error ejecutando migracion: {e}")
        raise


if __name__ == "__main__":
    run_migration()
