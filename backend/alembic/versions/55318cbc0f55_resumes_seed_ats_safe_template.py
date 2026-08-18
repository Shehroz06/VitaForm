"""resumes seed ats safe template

Revision ID: 55318cbc0f55
Revises: 873cc6148914
Create Date: 2026-08-15 14:56:59.723751

"""
import uuid
from datetime import UTC, datetime
from typing import Sequence, Union

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID

from alembic import op
from features.resumes.constants import ATS_SAFE_TEMPLATES

# revision identifiers, used by Alembic.
revision: str = '55318cbc0f55'
down_revision: Union[str, Sequence[str], None] = '873cc6148914'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

resume_templates_table = sa.table(
    "resume_templates",
    sa.column("id", UUID(as_uuid=True)),
    sa.column("slug", sa.String),
    sa.column("name", sa.String),
    sa.column("description", sa.String),
    sa.column("is_active", sa.Boolean),
    sa.column("created_at", sa.DateTime(timezone=True)),
    sa.column("updated_at", sa.DateTime(timezone=True)),
)


def upgrade() -> None:
    now = datetime.now(UTC)
    op.bulk_insert(
        resume_templates_table,
        [
            {
                "id": uuid.uuid4(),
                "slug": slug,
                "name": name,
                "description": description,
                "is_active": True,
                "created_at": now,
                "updated_at": now,
            }
            for slug, name, description in ATS_SAFE_TEMPLATES
        ],
    )


def downgrade() -> None:
    slugs = [slug for slug, _, _ in ATS_SAFE_TEMPLATES]
    op.execute(resume_templates_table.delete().where(resume_templates_table.c.slug.in_(slugs)))
