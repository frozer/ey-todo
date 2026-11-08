"""todos_removed_at_modified_at_none

Revision ID: 35d648cf23d4
Revises: b3f7f13c8ddb
Create Date: 2026-11-08 12:57:20.029208
"""

from collections.abc import Sequence

revision: str = '35d648cf23d4'
down_revision: str | None = 'b3f7f13c8ddb'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
