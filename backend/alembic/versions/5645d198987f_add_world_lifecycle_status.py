from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op


revision: str = "5645d198987f"
down_revision: str | Sequence[str] | None = "20260725_0001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "worlds",
        sa.Column(
            "status",
            sa.String(length=20),
            server_default="created",
            nullable=False,
        ),
    )
    op.create_check_constraint(
        "ck_worlds_status_valid",
        "worlds",
        "status IN ('created', 'running', 'paused')",
    )


def downgrade() -> None:
    op.drop_constraint(
        "ck_worlds_status_valid",
        "worlds",
        type_="check",
    )
    op.drop_column("worlds", "status")
