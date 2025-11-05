"""add_topics_pendientes_to_perfil

Revision ID: 72a2ee5be4c7
Revises: make_nombre_nullable
Create Date: 2025-11-05 14:32:34.655639

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '72a2ee5be4c7'
down_revision: Union[str, None] = 'make_nombre_nullable'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Agregar columna topics_pendientes a perfil_usuario
    op.add_column('perfil_usuario', sa.Column('topics_pendientes', sa.Text(), nullable=True))


def downgrade() -> None:
    # Eliminar columna topics_pendientes de perfil_usuario
    op.drop_column('perfil_usuario', 'topics_pendientes')
