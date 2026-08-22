"""resumes: rename ats_safe template display name to LaTeX

Revision ID: a430c243bb41
Revises: d4c8708b653d
Create Date: 2026-08-23 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op

# revision identifiers, used by Alembic.
revision: str = 'a430c243bb41'
down_revision: Union[str, Sequence[str], None] = 'd4c8708b653d'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.execute("UPDATE resume_templates SET name = 'LaTeX' WHERE slug = 'ats_safe'")


def downgrade() -> None:
    """Downgrade schema."""
    op.execute("UPDATE resume_templates SET name = 'ATS Safe' WHERE slug = 'ats_safe'")
