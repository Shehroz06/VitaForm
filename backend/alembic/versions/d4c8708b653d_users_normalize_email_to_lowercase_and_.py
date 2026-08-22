"""users: normalize email to lowercase and enforce case-insensitive uniqueness

Revision ID: d4c8708b653d
Revises: 51d20bd33ee5
Create Date: 2026-08-22 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'd4c8708b653d'
down_revision: Union[str, Sequence[str], None] = '51d20bd33ee5'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Normalize any existing mixed-case rows before the unique index below
    # would otherwise reject them as duplicates of each other.
    op.execute("UPDATE users SET email = lower(email)")
    op.drop_index(op.f('ix_users_email'), table_name='users')
    op.execute("CREATE UNIQUE INDEX ix_users_lower_email ON users (lower(email))")


def downgrade() -> None:
    """Downgrade schema."""
    op.execute("DROP INDEX ix_users_lower_email")
    op.create_index(op.f('ix_users_email'), 'users', ['email'], unique=True)
