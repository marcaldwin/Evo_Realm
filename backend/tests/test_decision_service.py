from collections.abc import Sequence

import pytest

from backend.app.core.enums import (
    ActionType,
    AgentStatus,
    Occupation,
)
from backend.app.intelligence.client import (
    LLMProviderError,
    LLMResponse,
    LLMTimeoutError,
)
from backend.app.intelligence.decision_service import (
    StructuredDecisionService,
)
from backend.app.intelligence.prompt import PROMPT_VERSION
from backend.app.intelligence.schemas import (
    ActionProposalV1,
    AgentDecisionState,
    AvailableAction,
    DecisionContext,
    TokenUsage,
)


class FakeLLMClient:
    provider_name = "fake-provider"
    model_name = "fake-model"

    def __init__(
        self,
        outcomes: Sequence[LLMResponse | Exception],
    ) -> None:
        self.outcomes = list(outcomes)
        self.calls: list[dict[str, object]] = []

    def generate(
        self,
        *,
        system_prompt: str,
        user_prompt: str,
        response_schema: dict[str, object],
    ) -> LLMResponse:
        self.calls.append(
            {
                "system_prompt": system_prompt,
                "user_prompt": user_prompt,
                "response_schema": response_schema,
            }
        )
        outcome = self.outcomes.pop(0)
        if isinstance(outcome, Exception):
            raise outcome
        return outcome


def make_context() -> DecisionContext:
    return DecisionContext(
        world_id="world-1",
        tick=12,
        agent=AgentDecisionState(
            agent_id="agent-1",
            name="Elena",
            occupation=Occupation.FARMER,
            status=AgentStatus.IDLE,
            location_id="farm-1",
            hunger=40,
            energy=80,
            health=100,
            money=5,
        ),
        available_actions=[
            AvailableAction(
                action_id="rest",
                action_type=ActionType.REST,
                description="Rest at the current location.",
            ),
            AvailableAction(
                action_id="work-farm",
                action_type=ActionType.WORK,
                description="Produce food at the farm.",
                target_id="farm-1",
            ),
        ],
        fallback_action_id="rest",
    )


def make_response(
    action_id: str,
    *,
    input_tokens: int = 10,
    output_tokens: int = 5,
) -> LLMResponse:
    proposal = ActionProposalV1(
        action_id=action_id,
        rationale="This action best matches the current state.",
    )
    return LLMResponse(
        content=proposal.model_dump_json(),
        model="fake-model-v1",
        token_usage=TokenUsage(
            input_tokens=input_tokens,
            output_tokens=output_tokens,
        ),
    )


def test_valid_proposal_returns_trusted_available_action() -> None:
    context = make_context()
    client = FakeLLMClient([make_response("work-farm")])
    service = StructuredDecisionService(client)
    original_context = context.model_dump()

    result = service.decide(context)

    assert result.selected_action == context.available_actions[1]
    assert result.proposal is not None
    assert result.proposal.action_id == "work-farm"
    assert result.telemetry.provider == "fake-provider"
    assert result.telemetry.model == "fake-model-v1"
    assert result.telemetry.prompt_version == PROMPT_VERSION
    assert result.telemetry.validation_result == "valid"
    assert result.telemetry.attempt_count == 1
    assert result.telemetry.fallback_used is False
    assert result.telemetry.token_usage == TokenUsage(
        input_tokens=10,
        output_tokens=5,
    )
    assert result.telemetry.latency_ms >= 0
    assert client.calls[0]["response_schema"] == (
        ActionProposalV1.model_json_schema()
    )
    assert context.model_dump() == original_context


def test_invalid_response_is_repaired_once() -> None:
    context = make_context()
    first_response = LLMResponse(
        content="not-json",
        model="fake-model-v1",
        token_usage=TokenUsage(
            input_tokens=4,
            output_tokens=2,
        ),
    )
    client = FakeLLMClient(
        [
            first_response,
            make_response(
                "work-farm",
                input_tokens=6,
                output_tokens=3,
            ),
        ]
    )

    result = StructuredDecisionService(client).decide(context)

    assert result.selected_action.action_id == "work-farm"
    assert result.telemetry.validation_result == "valid_after_retry"
    assert result.telemetry.attempt_count == 2
    assert result.telemetry.fallback_used is False
    assert result.telemetry.token_usage == TokenUsage(
        input_tokens=10,
        output_tokens=5,
    )
    assert len(client.calls) == 2
    assert "not-json" in str(client.calls[1]["user_prompt"])
    assert "failed schema validation" in str(
        client.calls[1]["user_prompt"]
    )


def test_two_invalid_responses_use_fallback() -> None:
    context = make_context()
    client = FakeLLMClient(
        [
            LLMResponse(
                content="not-json",
                model="fake-model-v1",
                token_usage=TokenUsage(
                    input_tokens=4,
                    output_tokens=2,
                ),
            ),
            LLMResponse(
                content='{"schema_version":"2.0"}',
                model="fake-model-v1",
                token_usage=TokenUsage(
                    input_tokens=6,
                    output_tokens=3,
                ),
            ),
        ]
    )

    result = StructuredDecisionService(client).decide(context)

    assert result.selected_action.action_id == "rest"
    assert result.proposal is None
    assert result.telemetry.validation_result == "invalid_format"
    assert result.telemetry.attempt_count == 2
    assert result.telemetry.fallback_used is True
    assert result.telemetry.token_usage == TokenUsage(
        input_tokens=10,
        output_tokens=5,
    )
    assert len(client.calls) == 2


def test_impossible_action_uses_fallback() -> None:
    context = make_context()
    client = FakeLLMClient([make_response("invented-action")])

    result = StructuredDecisionService(client).decide(context)

    assert result.selected_action.action_id == "rest"
    assert result.proposal is not None
    assert result.proposal.action_id == "invented-action"
    assert result.telemetry.validation_result == "impossible_action"
    assert result.telemetry.attempt_count == 1
    assert result.telemetry.fallback_used is True


@pytest.mark.parametrize(
    ("error", "validation_result"),
    [
        (LLMTimeoutError("request timed out"), "timeout"),
        (LLMProviderError("provider unavailable"), "provider_error"),
    ],
)
def test_initial_provider_failure_uses_fallback(
    error: Exception,
    validation_result: str,
) -> None:
    context = make_context()
    client = FakeLLMClient([error])

    result = StructuredDecisionService(client).decide(context)

    assert result.selected_action.action_id == "rest"
    assert result.proposal is None
    assert result.telemetry.model == "fake-model"
    assert result.telemetry.validation_result == validation_result
    assert result.telemetry.attempt_count == 1
    assert result.telemetry.fallback_used is True
    assert result.telemetry.token_usage == TokenUsage()


@pytest.mark.parametrize(
    ("error", "validation_result"),
    [
        (LLMTimeoutError("repair timed out"), "timeout"),
        (LLMProviderError("repair failed"), "provider_error"),
    ],
)
def test_repair_provider_failure_preserves_first_attempt_usage(
    error: Exception,
    validation_result: str,
) -> None:
    context = make_context()
    client = FakeLLMClient(
        [
            LLMResponse(
                content="not-json",
                model="fake-model-v1",
                token_usage=TokenUsage(
                    input_tokens=7,
                    output_tokens=3,
                ),
            ),
            error,
        ]
    )

    result = StructuredDecisionService(client).decide(context)

    assert result.selected_action.action_id == "rest"
    assert result.telemetry.validation_result == validation_result
    assert result.telemetry.attempt_count == 2
    assert result.telemetry.fallback_used is True
    assert result.telemetry.token_usage == TokenUsage(
        input_tokens=7,
        output_tokens=3,
    )
    assert len(client.calls) == 2
