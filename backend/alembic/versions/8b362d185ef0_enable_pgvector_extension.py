"""enable pgvector extension

Revision ID: 8b362d185ef0
Revises: 5645d198987f
Create Date: 2026-07-27 13:32:50.565796

"""
from typing import Sequence, Union

from alembic import op


# revision identifiers, used by Alembic.
revision: str = '8b362d185ef0'
down_revision: Union[str, Sequence[str], None] = '5645d198987f'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")


def downgrade() -> None:
    """Downgrade schema."""
    op.execute("DROP EXTENSION IF EXISTS vector")
