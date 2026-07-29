from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op


revision: str = "20260727_0003"
down_revision: str | Sequence[str] | None = "20260727_0002"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "agent_relationships",
        sa.Column("database_id", sa.Integer(), nullable=False),
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("world_database_id", sa.Integer(), nullable=False),
        sa.Column("source_agent_database_id", sa.Integer(), nullable=False),
        sa.Column("target_agent_database_id", sa.Integer(), nullable=False),
        sa.Column(
            "trust",
            sa.Integer(),
            server_default="0",
            nullable=False,
        ),
        sa.Column(
            "affection",
            sa.Integer(),
            server_default="0",
            nullable=False,
        ),
        sa.Column(
            "respect",
            sa.Integer(),
            server_default="0",
            nullable=False,
        ),
        sa.Column(
            "interaction_count",
            sa.Integer(),
            server_default="0",
            nullable=False,
        ),
        sa.CheckConstraint(
            "affection BETWEEN -100 AND 100",
            name="ck_agent_relationships_affection_range",
        ),
        sa.CheckConstraint(
            "interaction_count >= 0",
            name="ck_agent_relationships_interactions_nonnegative",
        ),
        sa.CheckConstraint(
            "respect BETWEEN -100 AND 100",
            name="ck_agent_relationships_respect_range",
        ),
        sa.CheckConstraint(
            "source_agent_database_id <> target_agent_database_id",
            name="ck_agent_relationships_distinct_agents",
        ),
        sa.CheckConstraint(
            "trust BETWEEN -100 AND 100",
            name="ck_agent_relationships_trust_range",
        ),
        sa.ForeignKeyConstraint(
            ["source_agent_database_id"],
            ["agents.database_id"],
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["target_agent_database_id"],
            ["agents.database_id"],
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["world_database_id"],
            ["worlds.database_id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("database_id"),
        sa.UniqueConstraint(
            "source_agent_database_id",
            "target_agent_database_id",
            name="uq_agent_relationships_direction",
        ),
    )
    op.create_index(
        "ix_agent_relationships_id",
        "agent_relationships",
        ["id"],
        unique=True,
    )
    op.create_index(
        "ix_agent_relationships_source_agent_database_id",
        "agent_relationships",
        ["source_agent_database_id"],
    )
    op.create_index(
        "ix_agent_relationships_target_agent_database_id",
        "agent_relationships",
        ["target_agent_database_id"],
    )
    op.create_index(
        "ix_agent_relationships_world_database_id",
        "agent_relationships",
        ["world_database_id"],
    )

    op.create_table(
        "conversations",
        sa.Column("database_id", sa.Integer(), nullable=False),
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("world_database_id", sa.Integer(), nullable=False),
        sa.Column("initiator_agent_database_id", sa.Integer(), nullable=False),
        sa.Column(
            "participant_agent_database_id",
            sa.Integer(),
            nullable=False,
        ),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("start_tick", sa.Integer(), nullable=False),
        sa.Column("end_tick", sa.Integer(), nullable=True),
        sa.CheckConstraint(
            "end_tick IS NULL OR end_tick >= start_tick",
            name="ck_conversations_end_tick_valid",
        ),
        sa.CheckConstraint(
            "initiator_agent_database_id <> participant_agent_database_id",
            name="ck_conversations_distinct_agents",
        ),
        sa.CheckConstraint(
            "start_tick >= 0",
            name="ck_conversations_start_tick_nonnegative",
        ),
        sa.CheckConstraint(
            "status IN ('active', 'completed')",
            name="ck_conversations_status_valid",
        ),
        sa.ForeignKeyConstraint(
            ["initiator_agent_database_id"],
            ["agents.database_id"],
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["participant_agent_database_id"],
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
        "ix_conversations_id",
        "conversations",
        ["id"],
        unique=True,
    )
    op.create_index(
        "ix_conversations_initiator_agent_database_id",
        "conversations",
        ["initiator_agent_database_id"],
    )
    op.create_index(
        "ix_conversations_participant_agent_database_id",
        "conversations",
        ["participant_agent_database_id"],
    )
    op.create_index(
        "ix_conversations_world_database_id",
        "conversations",
        ["world_database_id"],
    )

    op.create_table(
        "conversation_outcomes",
        sa.Column("database_id", sa.Integer(), nullable=False),
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("conversation_database_id", sa.Integer(), nullable=False),
        sa.Column("outcome_type", sa.String(length=50), nullable=False),
        sa.Column("actor_agent_database_id", sa.Integer(), nullable=False),
        sa.Column("target_agent_database_id", sa.Integer(), nullable=False),
        sa.Column(
            "confirmed",
            sa.Boolean(),
            server_default="false",
            nullable=False,
        ),
        sa.Column("confirmation_tick", sa.Integer(), nullable=False),
        sa.Column("details", sa.JSON(), nullable=False),
        sa.Column(
            "relationship_applied",
            sa.Boolean(),
            server_default="false",
            nullable=False,
        ),
        sa.CheckConstraint(
            "actor_agent_database_id <> target_agent_database_id",
            name="ck_conversation_outcomes_distinct_agents",
        ),
        sa.CheckConstraint(
            "confirmation_tick >= 0",
            name="ck_conversation_outcomes_tick_nonnegative",
        ),
        sa.CheckConstraint(
            "outcome_type IN "
            "('successful_trade', 'emergency_help', 'refusal', "
            "'promise_fulfilled', 'broken_promise')",
            name="ck_conversation_outcomes_type_valid",
        ),
        sa.CheckConstraint(
            "NOT relationship_applied OR confirmed",
            name="ck_conversation_outcomes_applied_requires_confirmed",
        ),
        sa.ForeignKeyConstraint(
            ["actor_agent_database_id"],
            ["agents.database_id"],
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["conversation_database_id"],
            ["conversations.database_id"],
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["target_agent_database_id"],
            ["agents.database_id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("database_id"),
    )
    op.create_index(
        "ix_conversation_outcomes_actor_agent_database_id",
        "conversation_outcomes",
        ["actor_agent_database_id"],
    )
    op.create_index(
        "ix_conversation_outcomes_conversation_database_id",
        "conversation_outcomes",
        ["conversation_database_id"],
    )
    op.create_index(
        "ix_conversation_outcomes_id",
        "conversation_outcomes",
        ["id"],
        unique=True,
    )
    op.create_index(
        "ix_conversation_outcomes_target_agent_database_id",
        "conversation_outcomes",
        ["target_agent_database_id"],
    )

    op.create_table(
        "conversation_turns",
        sa.Column("database_id", sa.Integer(), nullable=False),
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("conversation_database_id", sa.Integer(), nullable=False),
        sa.Column("turn_number", sa.Integer(), nullable=False),
        sa.Column("speaker_agent_database_id", sa.Integer(), nullable=False),
        sa.Column("listener_agent_database_id", sa.Integer(), nullable=False),
        sa.Column("dialogue_act", sa.String(length=30), nullable=False),
        sa.Column("message", sa.Text(), nullable=False),
        sa.Column("creation_tick", sa.Integer(), nullable=False),
        sa.CheckConstraint(
            "creation_tick >= 0",
            name="ck_conversation_turns_tick_nonnegative",
        ),
        sa.CheckConstraint(
            "dialogue_act IN "
            "('request', 'offer', 'promise', 'inform', "
            "'agree', 'reject', 'thank')",
            name="ck_conversation_turns_dialogue_act_valid",
        ),
        sa.CheckConstraint(
            "speaker_agent_database_id <> listener_agent_database_id",
            name="ck_conversation_turns_distinct_agents",
        ),
        sa.CheckConstraint(
            "turn_number BETWEEN 1 AND 4",
            name="ck_conversation_turns_number_range",
        ),
        sa.ForeignKeyConstraint(
            ["conversation_database_id"],
            ["conversations.database_id"],
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["listener_agent_database_id"],
            ["agents.database_id"],
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["speaker_agent_database_id"],
            ["agents.database_id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("database_id"),
        sa.UniqueConstraint(
            "conversation_database_id",
            "turn_number",
            name="uq_conversation_turns_number",
        ),
    )
    op.create_index(
        "ix_conversation_turns_conversation_database_id",
        "conversation_turns",
        ["conversation_database_id"],
    )
    op.create_index(
        "ix_conversation_turns_id",
        "conversation_turns",
        ["id"],
        unique=True,
    )
    op.create_index(
        "ix_conversation_turns_listener_agent_database_id",
        "conversation_turns",
        ["listener_agent_database_id"],
    )
    op.create_index(
        "ix_conversation_turns_speaker_agent_database_id",
        "conversation_turns",
        ["speaker_agent_database_id"],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_conversation_turns_speaker_agent_database_id",
        table_name="conversation_turns",
    )
    op.drop_index(
        "ix_conversation_turns_listener_agent_database_id",
        table_name="conversation_turns",
    )
    op.drop_index(
        "ix_conversation_turns_id",
        table_name="conversation_turns",
    )
    op.drop_index(
        "ix_conversation_turns_conversation_database_id",
        table_name="conversation_turns",
    )
    op.drop_table("conversation_turns")
    op.drop_index(
        "ix_conversation_outcomes_target_agent_database_id",
        table_name="conversation_outcomes",
    )
    op.drop_index(
        "ix_conversation_outcomes_id",
        table_name="conversation_outcomes",
    )
    op.drop_index(
        "ix_conversation_outcomes_conversation_database_id",
        table_name="conversation_outcomes",
    )
    op.drop_index(
        "ix_conversation_outcomes_actor_agent_database_id",
        table_name="conversation_outcomes",
    )
    op.drop_table("conversation_outcomes")
    op.drop_index(
        "ix_conversations_world_database_id",
        table_name="conversations",
    )
    op.drop_index(
        "ix_conversations_participant_agent_database_id",
        table_name="conversations",
    )
    op.drop_index(
        "ix_conversations_initiator_agent_database_id",
        table_name="conversations",
    )
    op.drop_index(
        "ix_conversations_id",
        table_name="conversations",
    )
    op.drop_table("conversations")
    op.drop_index(
        "ix_agent_relationships_world_database_id",
        table_name="agent_relationships",
    )
    op.drop_index(
        "ix_agent_relationships_target_agent_database_id",
        table_name="agent_relationships",
    )
    op.drop_index(
        "ix_agent_relationships_source_agent_database_id",
        table_name="agent_relationships",
    )
    op.drop_index(
        "ix_agent_relationships_id",
        table_name="agent_relationships",
    )
    op.drop_table("agent_relationships")
