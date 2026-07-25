from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op


revision: str = "20260725_0001"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "worlds",
        sa.Column("database_id", sa.Integer(), nullable=False),
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("current_tick", sa.Integer(), nullable=False),
        sa.Column("seed", sa.Integer(), nullable=False),
        sa.CheckConstraint(
            "current_tick >= 0",
            name="ck_worlds_current_tick_nonnegative",
        ),
        sa.PrimaryKeyConstraint("database_id"),
    )
    op.create_index("ix_worlds_id", "worlds", ["id"], unique=True)

    op.create_table(
        "locations",
        sa.Column("database_id", sa.Integer(), nullable=False),
        sa.Column("world_database_id", sa.Integer(), nullable=False),
        sa.Column("id", sa.String(length=100), nullable=False),
        sa.Column("position", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("location_type", sa.String(length=50), nullable=False),
        sa.Column("x", sa.Integer(), nullable=False),
        sa.Column("y", sa.Integer(), nullable=False),
        sa.Column("capacity", sa.Integer(), nullable=False),
        sa.CheckConstraint(
            "capacity >= 0",
            name="ck_locations_capacity_nonnegative",
        ),
        sa.ForeignKeyConstraint(
            ["world_database_id"],
            ["worlds.database_id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("database_id"),
        sa.UniqueConstraint(
            "world_database_id",
            "id",
            name="uq_locations_world_id",
        ),
        sa.UniqueConstraint(
            "world_database_id",
            "position",
            name="uq_locations_world_position",
        ),
    )
    op.create_index(
        "ix_locations_world_database_id",
        "locations",
        ["world_database_id"],
    )

    op.create_table(
        "location_inventory",
        sa.Column("location_database_id", sa.Integer(), nullable=False),
        sa.Column("resource_type", sa.String(length=50), nullable=False),
        sa.Column("quantity", sa.Integer(), nullable=False),
        sa.CheckConstraint(
            "quantity >= 0",
            name="ck_location_inventory_quantity_nonnegative",
        ),
        sa.ForeignKeyConstraint(
            ["location_database_id"],
            ["locations.database_id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint(
            "location_database_id",
            "resource_type",
        ),
    )

    op.create_table(
        "agents",
        sa.Column("database_id", sa.Integer(), nullable=False),
        sa.Column("world_database_id", sa.Integer(), nullable=False),
        sa.Column("location_database_id", sa.Integer(), nullable=False),
        sa.Column("id", sa.String(length=100), nullable=False),
        sa.Column("position", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("occupation", sa.String(length=50), nullable=False),
        sa.Column("status", sa.String(length=50), nullable=False),
        sa.Column("hunger", sa.Integer(), nullable=False),
        sa.Column("energy", sa.Integer(), nullable=False),
        sa.Column("health", sa.Integer(), nullable=False),
        sa.Column("money", sa.Integer(), nullable=False),
        sa.CheckConstraint(
            "energy BETWEEN 0 AND 100",
            name="ck_agents_energy_range",
        ),
        sa.CheckConstraint(
            "health BETWEEN 0 AND 100",
            name="ck_agents_health_range",
        ),
        sa.CheckConstraint(
            "hunger BETWEEN 0 AND 100",
            name="ck_agents_hunger_range",
        ),
        sa.CheckConstraint(
            "money >= 0",
            name="ck_agents_money_nonnegative",
        ),
        sa.ForeignKeyConstraint(
            ["location_database_id"],
            ["locations.database_id"],
        ),
        sa.ForeignKeyConstraint(
            ["world_database_id"],
            ["worlds.database_id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("database_id"),
        sa.UniqueConstraint(
            "world_database_id",
            "id",
            name="uq_agents_world_id",
        ),
        sa.UniqueConstraint(
            "world_database_id",
            "position",
            name="uq_agents_world_position",
        ),
    )
    op.create_index(
        "ix_agents_location_database_id",
        "agents",
        ["location_database_id"],
    )
    op.create_index(
        "ix_agents_world_database_id",
        "agents",
        ["world_database_id"],
    )

    op.create_table(
        "agent_inventory",
        sa.Column("agent_database_id", sa.Integer(), nullable=False),
        sa.Column("resource_type", sa.String(length=50), nullable=False),
        sa.Column("quantity", sa.Integer(), nullable=False),
        sa.CheckConstraint(
            "quantity >= 0",
            name="ck_agent_inventory_quantity_nonnegative",
        ),
        sa.ForeignKeyConstraint(
            ["agent_database_id"],
            ["agents.database_id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint(
            "agent_database_id",
            "resource_type",
        ),
    )

    op.create_table(
        "simulation_events",
        sa.Column("database_id", sa.Integer(), nullable=False),
        sa.Column("world_database_id", sa.Integer(), nullable=False),
        sa.Column("sequence", sa.Integer(), nullable=False),
        sa.Column("tick", sa.Integer(), nullable=False),
        sa.Column("event_type", sa.String(length=100), nullable=False),
        sa.Column("agent_id", sa.String(length=100), nullable=False),
        sa.Column("location_id", sa.String(length=100), nullable=False),
        sa.Column("summary", sa.String(), nullable=False),
        sa.CheckConstraint(
            "tick >= 0",
            name="ck_simulation_events_tick_nonnegative",
        ),
        sa.ForeignKeyConstraint(
            ["world_database_id"],
            ["worlds.database_id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("database_id"),
        sa.UniqueConstraint(
            "world_database_id",
            "sequence",
            name="uq_simulation_events_world_sequence",
        ),
    )
    op.create_index(
        "ix_simulation_events_world_database_id",
        "simulation_events",
        ["world_database_id"],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_simulation_events_world_database_id",
        table_name="simulation_events",
    )
    op.drop_table("simulation_events")
    op.drop_table("agent_inventory")
    op.drop_index(
        "ix_agents_world_database_id",
        table_name="agents",
    )
    op.drop_index(
        "ix_agents_location_database_id",
        table_name="agents",
    )
    op.drop_table("agents")
    op.drop_table("location_inventory")
    op.drop_index(
        "ix_locations_world_database_id",
        table_name="locations",
    )
    op.drop_table("locations")
    op.drop_index("ix_worlds_id", table_name="worlds")
    op.drop_table("worlds")
