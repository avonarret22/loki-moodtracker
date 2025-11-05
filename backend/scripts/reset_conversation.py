"""
Script para reiniciar conversación con Loki desde la línea de comandos.

Uso:
    python scripts/reset_conversation.py <usuario_id> [--tipo=suave|completo]

Ejemplos:
    python scripts/reset_conversation.py 1
    python scripts/reset_conversation.py 1 --tipo=suave
    python scripts/reset_conversation.py 1 --tipo=completo
"""

import sys
import argparse
from pathlib import Path

# Agregar el directorio raíz al path
root_dir = Path(__file__).parent.parent
sys.path.insert(0, str(root_dir))

from app.db.session import SessionLocal
from app.models.mood import (
    Usuario, ConversacionContexto, EstadoAnimo, Habito, 
    RegistroHabito, PerfilUsuario, ResumenConversacion, Correlacion
)


def reset_suave(db, usuario_id: int):
    """Borra solo el historial de conversaciones."""
    db.query(ConversacionContexto).filter(
        ConversacionContexto.usuario_id == usuario_id
    ).delete()
    
    db.query(ResumenConversacion).filter(
        ResumenConversacion.usuario_id == usuario_id
    ).delete()
    
    db.commit()
    print("✅ Reset suave completado: Historial de conversaciones borrado.")


def reset_completo(db, usuario_id: int):
    """Borra TODO excepto el usuario."""
    # Conversaciones
    db.query(ConversacionContexto).filter(
        ConversacionContexto.usuario_id == usuario_id
    ).delete()
    
    db.query(ResumenConversacion).filter(
        ResumenConversacion.usuario_id == usuario_id
    ).delete()
    
    # Hábitos
    db.query(RegistroHabito).filter(
        RegistroHabito.usuario_id == usuario_id
    ).delete()
    
    db.query(Habito).filter(
        Habito.usuario_id == usuario_id
    ).delete()
    
    # Estados de ánimo
    db.query(EstadoAnimo).filter(
        EstadoAnimo.usuario_id == usuario_id
    ).delete()
    
    # Correlaciones
    db.query(Correlacion).filter(
        Correlacion.usuario_id == usuario_id
    ).delete()
    
    # Resetear perfil
    perfil = db.query(PerfilUsuario).filter(
        PerfilUsuario.usuario_id == usuario_id
    ).first()
    
    if perfil:
        perfil.nivel_confianza = 1
        perfil.total_interacciones = 0
        perfil.interacciones_positivas = 0
        perfil.ultima_interaccion = None
        perfil.temas_conversacion = None
        perfil.patrones_detectados = None
        perfil.memorias_emocionales = None
        perfil.topics_pendientes = None
    
    db.commit()
    print("✅ Reset completo realizado: TODO ha sido reiniciado.")


def main():
    parser = argparse.ArgumentParser(
        description="Reinicia la conversación con Loki"
    )
    parser.add_argument(
        "usuario_id",
        type=int,
        help="ID del usuario a reiniciar"
    )
    parser.add_argument(
        "--tipo",
        choices=["suave", "completo"],
        default="suave",
        help="Tipo de reset: suave (solo conversaciones) o completo (todo)"
    )
    
    args = parser.parse_args()
    
    # Conectar a la base de datos
    db = SessionLocal()
    
    try:
        # Verificar que el usuario existe
        usuario = db.query(Usuario).filter(Usuario.id == args.usuario_id).first()
        if not usuario:
            print(f"❌ Error: Usuario con ID {args.usuario_id} no encontrado.")
            sys.exit(1)
        
        print(f"\n{'='*60}")
        print(f"🔄 Reiniciando conversación de: {usuario.nombre} (ID: {usuario.id})")
        print(f"📋 Tipo de reset: {args.tipo.upper()}")
        print(f"{'='*60}\n")
        
        # Confirmación
        if args.tipo == "completo":
            respuesta = input("⚠️  ADVERTENCIA: Esto borrará TODO (ánimo, hábitos, perfil). ¿Continuar? (s/n): ")
            if respuesta.lower() != 's':
                print("❌ Operación cancelada.")
                sys.exit(0)
        
        # Ejecutar reset
        if args.tipo == "suave":
            reset_suave(db, args.usuario_id)
        else:
            reset_completo(db, args.usuario_id)
        
        print(f"\n✅ Reset completado exitosamente para {usuario.nombre}!")
        
    except Exception as e:
        db.rollback()
        print(f"\n❌ Error: {str(e)}")
        sys.exit(1)
    finally:
        db.close()


if __name__ == "__main__":
    main()
