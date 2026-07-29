from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op


revision: str = "20260729_0004"
down_revision: str | Sequence[str] | None = "20260727_0003"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "agents",
        sa.Column(
            "personality_traits",
            sa.JSON(),
            server_default=sa.text("'{}'::json"),
            nullable=False,
        ),
    )
    op.add_column(
        "agents",
        sa.Column("active_goal", sa.String(length=300), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("agents", "active_goal")
    op.drop_column("agents", "personality_traits")
