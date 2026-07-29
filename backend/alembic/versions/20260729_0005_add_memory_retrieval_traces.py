from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op


revision: str = "20260729_0005"
down_revision: str | Sequence[str] | None = "20260729_0004"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "memory_retrievals",
        sa.Column("database_id", sa.Integer(), nullable=False),
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("world_database_id", sa.Integer(), nullable=False),
        sa.Column("owner_agent_database_id", sa.Integer(), nullable=False),
        sa.Column("query_text", sa.Text(), nullable=False),
        sa.Column("current_tick", sa.Integer(), nullable=False),
        sa.Column("mode", sa.String(length=30), nullable=False),
        sa.CheckConstraint(
            "current_tick >= 0",
            name="ck_memory_retrievals_tick_nonnegative",
        ),
        sa.ForeignKeyConstraint(
            ["owner_agent_database_id"],
            ["agents.database_id"],
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["world_database_id"],
            ["worlds.database_id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("database_id"),
    )
    op.create_index(
        "ix_memory_retrievals_id",
        "memory_retrievals",
        ["id"],
        unique=True,
    )
    op.create_index(
        "ix_memory_retrievals_owner_agent_database_id",
        "memory_retrievals",
        ["owner_agent_database_id"],
    )
    op.create_index(
        "ix_memory_retrievals_world_database_id",
        "memory_retrievals",
        ["world_database_id"],
    )

    op.create_table(
        "memory_retrieval_items",
        sa.Column("database_id", sa.Integer(), nullable=False),
        sa.Column("retrieval_database_id", sa.Integer(), nullable=False),
        sa.Column("memory_database_id", sa.Integer(), nullable=False),
        sa.Column("position", sa.Integer(), nullable=False),
        sa.Column("semantic_similarity", sa.Float(), nullable=False),
        sa.Column("importance_score", sa.Float(), nullable=False),
        sa.Column("recency_score", sa.Float(), nullable=False),
        sa.Column("relationship_relevance", sa.Float(), nullable=False),
        sa.Column("total_score", sa.Float(), nullable=False),
        sa.CheckConstraint(
            "position >= 0",
            name="ck_memory_retrieval_items_position_nonnegative",
        ),
        sa.ForeignKeyConstraint(
            ["memory_database_id"],
            ["episodic_memories.database_id"],
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["retrieval_database_id"],
            ["memory_retrievals.database_id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("database_id"),
        sa.UniqueConstraint(
            "retrieval_database_id",
            "position",
            name="uq_memory_retrieval_items_position",
        ),
    )
    op.create_index(
        "ix_memory_retrieval_items_memory_database_id",
        "memory_retrieval_items",
        ["memory_database_id"],
    )
    op.create_index(
        "ix_memory_retrieval_items_retrieval_database_id",
        "memory_retrieval_items",
        ["retrieval_database_id"],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_memory_retrieval_items_retrieval_database_id",
        table_name="memory_retrieval_items",
    )
    op.drop_index(
        "ix_memory_retrieval_items_memory_database_id",
        table_name="memory_retrieval_items",
    )
    op.drop_table("memory_retrieval_items")
    op.drop_index(
        "ix_memory_retrievals_world_database_id",
        table_name="memory_retrievals",
    )
    op.drop_index(
        "ix_memory_retrievals_owner_agent_database_id",
        table_name="memory_retrievals",
    )
    op.drop_index(
        "ix_memory_retrievals_id",
        table_name="memory_retrievals",
    )
    op.drop_table("memory_retrievals")
