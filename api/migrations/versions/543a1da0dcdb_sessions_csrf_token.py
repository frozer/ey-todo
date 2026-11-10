"""sessions_csrf_token

Revision ID: 543a1da0dcdb
Revises: 037028b4fb4c
Create Date: 2026-11-09 23:33:27.086024
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = '543a1da0dcdb'
down_revision: str | None = '037028b4fb4c'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # existing sessions get NULL and fail the CSRF check, so those users log in again
    with op.batch_alter_table('sessions', schema=None) as batch_op:
        batch_op.add_column(sa.Column('csrf_token', sa.String(length=64), nullable=True))


def downgrade() -> None:
    with op.batch_alter_table('sessions', schema=None) as batch_op:
        batch_op.drop_column('csrf_token')
