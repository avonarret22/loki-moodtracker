"""add_composite_indexes_optimization

Revision ID: 14ca635a9395
Revises: 7dfb4597f6c4
Create Date: 2025-11-05 11:37:43.637625

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '14ca635a9395'
down_revision: Union[str, None] = '7dfb4597f6c4'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """
    Agrega índices compuestos para optimizar queries frecuentes.
    """
    # Índices para RespuestaExitosa (búsqueda de respuestas efectivas)
    op.create_index(
        'ix_respuestas_usuario_patron',
        'respuestas_exitosas',
        ['usuario_id', 'patron_pregunta'],
        unique=False
    )
    op.create_index(
        'ix_respuestas_usuario_utilidad',
        'respuestas_exitosas',
        ['usuario_id', 'utilidad_promedio'],
        unique=False
    )
    
    # Índice para fecha_ultima_uso en RespuestaExitosa
    op.create_index(
        'ix_respuestas_exitosas_fecha_ultima_uso',
        'respuestas_exitosas',
        ['fecha_ultima_uso'],
        unique=False
    )


def downgrade() -> None:
    """
    Remueve índices compuestos.
    """
    op.drop_index('ix_respuestas_exitosas_fecha_ultima_uso', table_name='respuestas_exitosas')
    op.drop_index('ix_respuestas_usuario_utilidad', table_name='respuestas_exitosas')
    op.drop_index('ix_respuestas_usuario_patron', table_name='respuestas_exitosas')
