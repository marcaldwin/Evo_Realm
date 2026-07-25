import pytest
from sqlalchemy import select
from sqlalchemy.orm import sessionmaker

from backend.app.core.enums import (
    AgentStatus,
    EventType,
    LocationType,
    Occupation,
    ResourceType,
)
from backend.app.db.models import AgentRecord, WorldRecord
from backend.app.repositories.world_repository import WorldRepository
from backend.app.services import world_service
from backend.app.simulation.models import (
    Agent,
    Location,
    SimulationEvent,
    World,
)


pytestmark = pytest.mark.usefixtures("database_world_store")


def build_world() -> World:
    return World(
        id="00000000-0000-4000-8000-000000000001",
        name="Persistent Haven",
        current_tick=4,
        seed=81,
        locations=[
            Location(
                id="farm-1",
                name="North Farm",
                location_type=LocationType.FARM,
                x=0,
                y=0,
                capacity=2,
                inventory={
                    ResourceType.FOOD: 12,
                    ResourceType.WOOD: 3,
                },
            )
        ],
        agents=[
            Agent(
                id="agent-1",
                name="Elena",
                occupation=Occupation.FARMER,
                location_id="farm-1",
                status=AgentStatus.IDLE,
                hunger=68,
                energy=90,
                health=100,
                money=5,
                inventory={
                    ResourceType.FOOD: 2,
                    ResourceType.MEDICINE: 1,
                },
            )
        ],
        events=[
            SimulationEvent(
                tick=3,
                event_type=EventType.RESTED,
                agent_id="agent-1",
                location_id="farm-1",
                summary="Tick 3: Elena rested and recovered 30 energy.",
            )
        ],
    )


def test_complete_world_persists_across_fresh_sessions(
    test_session_factory: sessionmaker,
) -> None:
    world = build_world()
    with test_session_factory.begin() as session:
        WorldRepository(session).add(world)

    with test_session_factory() as session:
        restored_world = WorldRepository(session).get(world.id)

    assert restored_world == world


def test_step_persists_state_inventory_tick_and_events(
    test_session_factory: sessionmaker,
) -> None:
    world = build_world()
    with test_session_factory.begin() as session:
        WorldRepository(session).add(world)

    stepped_world = world_service.step_world(world.id)

    with test_session_factory() as session:
        restored_world = WorldRepository(session).get(world.id)

    assert stepped_world is not None
    assert restored_world == stepped_world
    assert restored_world.current_tick == 5
    assert restored_world.agents[0].hunger == 40
    assert restored_world.agents[0].energy == 89
    assert restored_world.agents[0].inventory == {
        ResourceType.FOOD: 1,
        ResourceType.MEDICINE: 1,
    }
    assert restored_world.locations[0].inventory == {
        ResourceType.FOOD: 12,
        ResourceType.WOOD: 3,
    }
    assert len(restored_world.events) == 2
    assert restored_world.events[-1].event_type == EventType.FOOD_CONSUMED


def test_failed_step_rolls_back_flushed_changes(
    monkeypatch: pytest.MonkeyPatch,
    test_session_factory: sessionmaker,
) -> None:
    world = build_world()
    with test_session_factory.begin() as session:
        WorldRepository(session).add(world)

    def fail_after_partial_flush(
        repository: WorldRepository,
        updated_world: World,
    ) -> None:
        world_record = repository.session.scalar(
            select(WorldRecord).where(WorldRecord.id == updated_world.id)
        )
        agent_record = repository.session.scalar(
            select(AgentRecord).where(
                AgentRecord.world_database_id
                == world_record.database_id
            )
        )
        world_record.current_tick = updated_world.current_tick
        agent_record.hunger = updated_world.agents[0].hunger
        repository.session.flush()
        raise RuntimeError("Simulated persistence failure")

    monkeypatch.setattr(
        WorldRepository,
        "save",
        fail_after_partial_flush,
    )

    with pytest.raises(RuntimeError, match="Simulated persistence failure"):
        world_service.step_world(world.id)

    restored_world = world_service.get_world(world.id)

    assert restored_world == world
