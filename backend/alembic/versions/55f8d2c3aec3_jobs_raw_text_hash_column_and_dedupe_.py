"""jobs: raw_text_hash column and dedupe index

Revision ID: 55f8d2c3aec3
Revises: 75773b28e1ca
Create Date: 2026-08-19 19:54:25.521214

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '55f8d2c3aec3'
down_revision: Union[str, Sequence[str], None] = '75773b28e1ca'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Added nullable first so existing rows can be backfilled -- a straight
    # NOT NULL add_column would fail against the table's current data.
    op.add_column(
        'job_descriptions', sa.Column('raw_text_hash', sa.String(length=64), nullable=True)
    )
    op.execute(
        "UPDATE job_descriptions SET raw_text_hash = encode(sha256(raw_text::bytea), 'hex')"
    )
    op.alter_column('job_descriptions', 'raw_text_hash', nullable=False)
    op.create_index(
        op.f('ix_job_descriptions_raw_text_hash'), 'job_descriptions', ['raw_text_hash']
    )
    op.execute(
        "CREATE UNIQUE INDEX ix_job_descriptions_profile_raw_text_hash "
        "ON job_descriptions (profile_id, raw_text_hash) WHERE deleted_at IS NULL"
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.execute("DROP INDEX ix_job_descriptions_profile_raw_text_hash")
    op.drop_index(op.f('ix_job_descriptions_raw_text_hash'), table_name='job_descriptions')
    op.drop_column('job_descriptions', 'raw_text_hash')
