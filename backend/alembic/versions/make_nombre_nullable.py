"""make nombre nullable

Revision ID: make_nombre_nullable
Revises: 14ca635a9395
Create Date: 2025-11-05 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'make_nombre_nullable'
down_revision = '14ca635a9395'
branch_labels = None
depends_on = None


def upgrade():
    # Hacer el campo nombre nullable para permitir que Loki lo pregunte en la primera interacción
    op.alter_column('usuarios', 'nombre',
                    existing_type=sa.String(),
                    nullable=True)


def downgrade():
    # Revertir a nullable=False
    # Nota: Esto fallará si hay usuarios sin nombre
    op.alter_column('usuarios', 'nombre',
                    existing_type=sa.String(),
                    nullable=False)
