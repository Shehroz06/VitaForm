"""auth: seed default roles

Revision ID: 0d4429791ac3
Revises: d55859feeece
Create Date: 2026-08-04 13:33:07.170772

"""
import uuid
from datetime import UTC, datetime
from typing import Sequence, Union

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID

from alembic import op
from features.auth.constants import DEFAULT_ROLES

# revision identifiers, used by Alembic.
revision: str = '0d4429791ac3'
down_revision: Union[str, Sequence[str], None] = 'd55859feeece'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

roles_table = sa.table(
    "roles",
    sa.column("id", UUID(as_uuid=True)),
    sa.column("name", sa.String),
    sa.column("description", sa.String),
    sa.column("created_at", sa.DateTime(timezone=True)),
    sa.column("updated_at", sa.DateTime(timezone=True)),
)


def upgrade() -> None:
    now = datetime.now(UTC)
    op.bulk_insert(
        roles_table,
        [
            {
                "id": uuid.uuid4(),
                "name": name,
                "description": description,
                "created_at": now,
                "updated_at": now,
            }
            for name, description in DEFAULT_ROLES
        ],
    )


def downgrade() -> None:
    role_names = [name for name, _ in DEFAULT_ROLES]
    op.execute(roles_table.delete().where(roles_table.c.name.in_(role_names)))
