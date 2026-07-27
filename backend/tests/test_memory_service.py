from sqlalchemy.orm import sessionmaker

from backend.app.core.enums import (
    ActionType,
    AgentStatus,
    EventType,
    LocationType,
    MemoryMode,
    Occupation,
)
from backend.app.intelligence.context_builder import (
    build_decision_context,
)
from backend.app.intelligence.client import LLMResponse
from backend.app.intelligence.decision_service import (
    StructuredDecisionService,
)
from backend.app.intelligence.prompt import (
    serialize_decision_context,
)
from backend.app.intelligence.schemas import (
    ActionProposalV1,
    AvailableAction,
    TokenUsage,
)
from backend.app.memory.embedding import EmbeddingResult
from backend.app.memory.repository import MemoryRepository
from backend.app.memory.service import EpisodicMemoryService
from backend.app.repositories.world_repository import WorldRepository
from backend.app.simulation.models import (
    Agent,
    Location,
    SimulationEvent,
    World,
)


class FakeEmbeddingClient:
    model_name = "fake-embedding-v1"
    dimensions = 3

    def __init__(
        self,
        vectors: dict[str, tuple[float, ...]],
    ) -> None:
        self.vectors = vectors
        self.calls: list[str] = []

    def embed(self, text: str) -> EmbeddingResult:
        self.calls.append(text)
        return EmbeddingResult(
            vector=self.vectors.get(text, (1.0, 0.0, 0.0)),
            model=self.model_name,
        )


class FakeDecisionClient:
    provider_name = "fake-provider"
    model_name = "fake-decision-model"

    def __init__(self) -> None:
        self.user_prompts: list[str] = []

    def generate(
        self,
        *,
        system_prompt: str,
        user_prompt: str,
        response_schema: dict[str, object],
    ) -> LLMResponse:
        self.user_prompts.append(user_prompt)
        proposal = ActionProposalV1(
            action_id="rest",
            rationale="Rest is the best available action.",
        )
        return LLMResponse(
            content=proposal.model_dump_json(),
            model=self.model_name,
            token_usage=TokenUsage(
                input_tokens=10,
                output_tokens=5,
            ),
        )


def make_memory_world() -> World:
    summaries = [
        ("elena", "Elena produced food for the town."),
        ("marco", "Marco shared food with Elena."),
        ("elena", "Elena rested after farm work."),
        ("marco", "Marco purchased food at the market."),
        ("elena", "Elena failed to produce food."),
        ("marco", "Marco earned money from work."),
    ]
    return World(
        id="memory-world",
        name="Memory World",
        current_tick=20,
        seed=42,
        locations=[
            Location(
                id="farm",
                name="Farm",
                location_type=LocationType.FARM,
                x=0,
                y=0,
                capacity=5,
            )
        ],
        agents=[
            Agent(
                id="elena",
                name="Elena",
                occupation=Occupation.FARMER,
                location_id="farm",
                status=AgentStatus.IDLE,
                hunger=30,
                energy=80,
                health=100,
                money=5,
            ),
            Agent(
                id="marco",
                name="Marco",
                occupation=Occupation.MERCHANT,
                location_id="farm",
                status=AgentStatus.IDLE,
                hunger=20,
                energy=90,
                health=100,
                money=10,
            ),
        ],
        events=[
            SimulationEvent(
                tick=index + 1,
                event_type=EventType.FARM_WORK_SUCCEEDED,
                agent_id=agent_id,
                location_id="farm",
                summary=summary,
            )
            for index, (agent_id, summary) in enumerate(summaries)
        ],
    )


def make_vectors() -> dict[str, tuple[float, ...]]:
    return {
        "Elena produced food for the town.": (1.0, 0.0, 0.0),
        "Marco shared food with Elena.": (1.0, 0.0, 0.0),
        "Elena rested after farm work.": (0.7, 0.3, 0.0),
        "Marco purchased food at the market.": (0.8, 0.2, 0.0),
        "Elena failed to produce food.": (0.6, 0.4, 0.0),
        "Marco earned money from work.": (0.0, 1.0, 0.0),
        "Elena needs food.": (1.0, 0.0, 0.0),
    }


def test_event_memory_is_persisted_and_creation_is_idempotent(
    database_world_store: None,
    test_session_factory: sessionmaker,
) -> None:
    embedding_client = FakeEmbeddingClient(make_vectors())

    with test_session_factory.begin() as session:
        WorldRepository(session).add(make_memory_world())
        service = EpisodicMemoryService(
            MemoryMode.VECTOR_EPISODIC,
            repository=MemoryRepository(session),
            embedding_client=embedding_client,
        )

        first_memory = service.create_from_event(
            world_id="memory-world",
            owner_agent_id="elena",
            source_event_sequence=0,
            importance=0.9,
            emotional_value=0.6,
            creation_tick=10,
        )
        repeated_memory = service.create_from_event(
            world_id="memory-world",
            owner_agent_id="elena",
            source_event_sequence=0,
            importance=0.1,
            emotional_value=-0.5,
            creation_tick=20,
        )

    assert first_memory is not None
    assert repeated_memory == first_memory
    assert first_memory.content == "Elena produced food for the town."
    assert first_memory.owner_agent_id == "elena"
    assert first_memory.importance == 0.9
    assert first_memory.emotional_value == 0.6
    assert first_memory.creation_tick == 10
    assert first_memory.source_event_sequence == 0
    assert first_memory.embedding == (1.0, 0.0, 0.0)
    assert embedding_client.calls == [
        "Elena produced food for the town."
    ]

    with test_session_factory() as session:
        restored_memory = MemoryRepository(session).get_by_source(
            "memory-world",
            "elena",
            0,
        )

    assert restored_memory == first_memory


def test_retrieval_is_owner_scoped_ranked_and_limited_to_five(
    database_world_store: None,
    test_session_factory: sessionmaker,
) -> None:
    embedding_client = FakeEmbeddingClient(make_vectors())

    with test_session_factory.begin() as session:
        WorldRepository(session).add(make_memory_world())
        service = EpisodicMemoryService(
            MemoryMode.VECTOR_EPISODIC,
            repository=MemoryRepository(session),
            embedding_client=embedding_client,
        )
        elena_memories = [
            service.create_from_event(
                world_id="memory-world",
                owner_agent_id="elena",
                source_event_sequence=sequence,
                importance=0.8,
                emotional_value=0.2,
                creation_tick=10,
            )
            for sequence in range(6)
        ]
        marco_memory = service.create_from_event(
            world_id="memory-world",
            owner_agent_id="marco",
            source_event_sequence=0,
            importance=1.0,
            emotional_value=1.0,
            creation_tick=20,
        )

        result = service.retrieve(
            world_id="memory-world",
            owner_agent_id="elena",
            query_text="Elena needs food.",
            current_tick=20,
            relationship_scores={"marco": 90},
            limit=99,
        )

    assert len(result.memories) == 5
    assert result.mode == MemoryMode.VECTOR_EPISODIC
    assert result.memories[0].source_agent_id == "marco"
    assert result.memories[0].relationship_relevance == 0.9
    assert [
        memory.total_score
        for memory in result.memories
    ] == sorted(
        (
            memory.total_score
            for memory in result.memories
        ),
        reverse=True,
    )
    assert marco_memory is not None
    assert marco_memory.memory_id not in {
        memory.memory_id
        for memory in result.memories
    }
    assert all(memory is not None for memory in elena_memories)


def test_no_memory_mode_neither_stores_nor_retrieves() -> None:
    service = EpisodicMemoryService(MemoryMode.NO_MEMORY)

    memory = service.create_from_event(
        world_id="missing-world",
        owner_agent_id="missing-agent",
        source_event_sequence=0,
        importance=1.0,
        emotional_value=1.0,
        creation_tick=0,
    )
    result = service.retrieve(
        world_id="missing-world",
        owner_agent_id="missing-agent",
        query_text="Remember food.",
        current_tick=0,
    )

    assert memory is None
    assert result.mode == MemoryMode.NO_MEMORY
    assert result.memories == []


def test_retrieved_memories_are_included_in_decision_context(
    database_world_store: None,
    test_session_factory: sessionmaker,
) -> None:
    world = make_memory_world()
    embedding_client = FakeEmbeddingClient(make_vectors())

    with test_session_factory.begin() as session:
        WorldRepository(session).add(world)
        service = EpisodicMemoryService(
            MemoryMode.VECTOR_EPISODIC,
            repository=MemoryRepository(session),
            embedding_client=embedding_client,
        )
        service.create_from_event(
            world_id=world.id,
            owner_agent_id="elena",
            source_event_sequence=0,
            importance=0.9,
            emotional_value=0.6,
            creation_tick=10,
        )
        retrieval = service.retrieve(
            world_id=world.id,
            owner_agent_id="elena",
            query_text="Elena needs food.",
            current_tick=20,
        )

    context = build_decision_context(
        world,
        world.agents[0],
        available_actions=[
            AvailableAction(
                action_id="rest",
                action_type=ActionType.REST,
                description="Rest at the farm.",
            )
        ],
        fallback_action_id="rest",
        memories=retrieval.memories,
    )
    serialized_context = serialize_decision_context(context)

    assert context.memories == retrieval.memories
    assert retrieval.memories[0].memory_id in serialized_context
    assert retrieval.memories[0].content in serialized_context


def test_decision_service_retrieves_and_records_memories(
    database_world_store: None,
    test_session_factory: sessionmaker,
) -> None:
    world = make_memory_world()
    embedding_client = FakeEmbeddingClient(make_vectors())
    decision_client = FakeDecisionClient()

    with test_session_factory.begin() as session:
        WorldRepository(session).add(world)
        memory_service = EpisodicMemoryService(
            MemoryMode.VECTOR_EPISODIC,
            repository=MemoryRepository(session),
            embedding_client=embedding_client,
        )
        memory_service.create_from_event(
            world_id=world.id,
            owner_agent_id="elena",
            source_event_sequence=0,
            importance=0.9,
            emotional_value=0.6,
            creation_tick=10,
        )
        context = build_decision_context(
            world,
            world.agents[0],
            available_actions=[
                AvailableAction(
                    action_id="rest",
                    action_type=ActionType.REST,
                    description="Rest at the farm.",
                )
            ],
            fallback_action_id="rest",
        )

        result = StructuredDecisionService(
            decision_client,
            memory_service=memory_service,
        ).decide(context)

    assert result.selected_action.action_id == "rest"
    assert result.memory_retrieval is not None
    assert len(result.memory_retrieval.memories) == 1
    retrieved_memory = result.memory_retrieval.memories[0]
    assert retrieved_memory.content in decision_client.user_prompts[0]
    assert retrieved_memory.total_score >= 0
