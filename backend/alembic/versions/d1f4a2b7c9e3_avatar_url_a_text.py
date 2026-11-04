"""avatar_url a TEXT para poder guardar fotos subidas desde el dispositivo

Revision ID: d1f4a2b7c9e3
Revises: 878afd394f0b
Create Date: 2026-11-04 17:30:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'd1f4a2b7c9e3'
down_revision: Union[str, Sequence[str], None] = '878afd394f0b'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Antes solo cabia una URL (max 500 caracteres). Ahora tambien guardamos
    # la foto subida desde el dispositivo, ya reducida en el navegador y
    # codificada como texto (data URL), que ocupa bastante mas.
    op.alter_column('usuarios', 'avatar_url',
                    existing_type=sa.String(length=500),
                    type_=sa.Text(),
                    existing_nullable=True)


def downgrade() -> None:
    """Downgrade schema."""
    # las fotos subidas no caben en 500 caracteres: se pierden al volver atras
    op.execute("UPDATE usuarios SET avatar_url = NULL WHERE length(avatar_url) > 500")
    op.alter_column('usuarios', 'avatar_url',
                    existing_type=sa.Text(),
                    type_=sa.String(length=500),
                    existing_nullable=True)
