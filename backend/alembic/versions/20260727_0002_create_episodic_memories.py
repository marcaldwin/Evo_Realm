from collections.abc import Sequence

from pgvector.sqlalchemy import VECTOR
import sqlalchemy as sa

from alembic import op


revision: str = "20260727_0002"
down_revision: str | Sequence[str] | None = "8b362d185ef0"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "episodic_memories",
        sa.Column("database_id", sa.Integer(), nullable=False),
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("world_database_id", sa.Integer(), nullable=False),
        sa.Column("owner_agent_database_id", sa.Integer(), nullable=False),
        sa.Column("source_event_database_id", sa.Integer(), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("importance", sa.Float(), nullable=False),
        sa.Column("emotional_value", sa.Float(), nullable=False),
        sa.Column("creation_tick", sa.Integer(), nullable=False),
        sa.Column("embedding", VECTOR(), nullable=False),
        sa.Column("embedding_model", sa.String(length=100), nullable=False),
        sa.Column("embedding_dimensions", sa.Integer(), nullable=False),
        sa.CheckConstraint(
            "creation_tick >= 0",
            name="ck_episodic_memories_creation_tick_nonnegative",
        ),
        sa.CheckConstraint(
            "embedding_dimensions > 0",
            name="ck_episodic_memories_embedding_dimensions_positive",
        ),
        sa.CheckConstraint(
            "emotional_value BETWEEN -1 AND 1",
            name="ck_episodic_memories_emotional_value_range",
        ),
        sa.CheckConstraint(
            "importance BETWEEN 0 AND 1",
            name="ck_episodic_memories_importance_range",
        ),
        sa.ForeignKeyConstraint(
            ["owner_agent_database_id"],
            ["agents.database_id"],
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["source_event_database_id"],
            ["simulation_events.database_id"],
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["world_database_id"],
            ["worlds.database_id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("database_id"),
        sa.UniqueConstraint(
            "owner_agent_database_id",
            "source_event_database_id",
            name="uq_episodic_memories_owner_source_event",
        ),
    )
    op.create_index(
        "ix_episodic_memories_id",
        "episodic_memories",
        ["id"],
        unique=True,
    )
    op.create_index(
        "ix_episodic_memories_owner_agent_database_id",
        "episodic_memories",
        ["owner_agent_database_id"],
    )
    op.create_index(
        "ix_episodic_memories_source_event_database_id",
        "episodic_memories",
        ["source_event_database_id"],
    )
    op.create_index(
        "ix_episodic_memories_world_database_id",
        "episodic_memories",
        ["world_database_id"],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_episodic_memories_world_database_id",
        table_name="episodic_memories",
    )
    op.drop_index(
        "ix_episodic_memories_source_event_database_id",
        table_name="episodic_memories",
    )
    op.drop_index(
        "ix_episodic_memories_owner_agent_database_id",
        table_name="episodic_memories",
    )
    op.drop_index(
        "ix_episodic_memories_id",
        table_name="episodic_memories",
    )
    op.drop_table("episodic_memories")
