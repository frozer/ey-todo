"""todos_text_nullable

Revision ID: 037028b4fb4c
Revises: a426c5518ab7
Create Date: 2026-11-09 23:13:55.182529
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = '037028b4fb4c'
down_revision: str | None = 'a426c5518ab7'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    with op.batch_alter_table('todos', schema=None) as batch_op:
        batch_op.alter_column('text', existing_type=sa.String(length=200), nullable=True)
    op.execute("UPDATE todos SET text = NULL WHERE trim(text) = ''")


def downgrade() -> None:
    op.execute("UPDATE todos SET text = '' WHERE text IS NULL")
    with op.batch_alter_table('todos', schema=None) as batch_op:
        batch_op.alter_column('text', existing_type=sa.String(length=200), nullable=False)
