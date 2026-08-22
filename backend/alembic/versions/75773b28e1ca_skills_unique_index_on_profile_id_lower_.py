"""skills: unique index on profile_id + lower(name)

Revision ID: 75773b28e1ca
Revises: 55318cbc0f55
Create Date: 2026-08-19 19:53:18.181620

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '75773b28e1ca'
down_revision: Union[str, Sequence[str], None] = '55318cbc0f55'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.execute(
        "CREATE UNIQUE INDEX ix_skills_profile_lower_name "
        "ON skills (profile_id, lower(name)) WHERE deleted_at IS NULL"
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.execute("DROP INDEX ix_skills_profile_lower_name")
