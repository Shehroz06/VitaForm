"""resumes: add render_engine, set ats_safe to latex

Revision ID: 51d20bd33ee5
Revises: 55f8d2c3aec3
Create Date: 2026-08-20 12:04:58.037396

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '51d20bd33ee5'
down_revision: Union[str, Sequence[str], None] = '55f8d2c3aec3'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Unlike the enum columns in other migrations, this one is added to an
    # existing table via add_column rather than created inline as part of
    # create_table -- SQLAlchemy only auto-creates the Postgres ENUM type
    # for the latter, so it needs an explicit create() here.
    sa.Enum('html', 'latex', name='render_engine').create(op.get_bind(), checkfirst=True)
    op.add_column(
        'resume_templates',
        sa.Column(
            'render_engine',
            sa.Enum('html', 'latex', name='render_engine'),
            nullable=False,
            server_default='html',
        ),
    )
    op.alter_column('resume_templates', 'render_engine', server_default=None)
    op.execute("UPDATE resume_templates SET render_engine = 'latex' WHERE slug = 'ats_safe'")


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column('resume_templates', 'render_engine')
    # Postgres does not drop named ENUM types when the last column using them
    # is dropped -- without this, re-running upgrade() after this downgrade
    # fails with "type already exists".
    sa.Enum(name='render_engine').drop(op.get_bind(), checkfirst=True)
