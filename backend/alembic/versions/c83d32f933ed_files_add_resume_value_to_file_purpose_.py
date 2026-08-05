"""files: add resume value to file_purpose enum

Revision ID: c83d32f933ed
Revises: 6118d4c804ee
Create Date: 2026-08-05 17:25:07.671420

"""
from typing import Sequence, Union

from alembic import op

# revision identifiers, used by Alembic.
revision: str = 'c83d32f933ed'
down_revision: Union[str, Sequence[str], None] = '6118d4c804ee'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("ALTER TYPE file_purpose ADD VALUE 'resume'")


def downgrade() -> None:
    # Postgres has no DROP VALUE for enums -- rebuild the type without
    # 'resume'. Any files with purpose='resume' must be removed first or
    # this will fail (a downgrade can't represent data the old schema
    # didn't support).
    op.execute("ALTER TYPE file_purpose RENAME TO file_purpose_old")
    op.execute("CREATE TYPE file_purpose AS ENUM ('avatar', 'certificate', 'achievement')")
    op.execute(
        "ALTER TABLE files ALTER COLUMN purpose TYPE file_purpose "
        "USING purpose::text::file_purpose"
    )
    op.execute("DROP TYPE file_purpose_old")
