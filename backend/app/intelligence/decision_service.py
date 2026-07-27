from time import perf_counter

from pydantic import ValidationError

from ..memory.schemas import MemoryRetrievalResult
from ..memory.service import EpisodicMemoryService
from .client import (
    LLMClient,
    LLMProviderError,
    LLMResponse,
    LLMTimeoutError,
)
from .prompt import (
    PROMPT_VERSION,
    build_decision_prompts,
    build_repair_prompts,
    serialize_decision_context,
)
from .schemas import (
    ActionProposalV1,
    AvailableAction,
    DecisionContext,
    DecisionResult,
    DecisionTelemetry,
    DecisionValidationResult,
    TokenUsage,
)


class StructuredDecisionService:
    def __init__(
        self,
        client: LLMClient,
        *,
        memory_service: EpisodicMemoryService | None = None,
    ) -> None:
        self.client = client
        self.memory_service = memory_service

    @staticmethod
    def _find_action(
        context: DecisionContext,
        action_id: str,
    ) -> AvailableAction | None:
        return next(
            (
                action
                for action in context.available_actions
                if action.action_id == action_id
            ),
            None,
        )

    def _request_response(
        self,
        system_prompt: str,
        user_prompt: str,
    ) -> LLMResponse:
        return self.client.generate(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            response_schema=ActionProposalV1.model_json_schema(),
        )

    def _get_fallback_action(
        self,
        context: DecisionContext,
    ) -> AvailableAction:
        fallback_action = self._find_action(
            context,
            context.fallback_action_id,
        )
        if fallback_action is None:
            raise RuntimeError(
                "Decision context has no valid fallback action."
            )
        return fallback_action

    def _build_result(
        self,
        *,
        selected_action: AvailableAction,
        proposal: ActionProposalV1 | None,
        model: str,
        token_usage: TokenUsage,
        validation_result: DecisionValidationResult,
        attempt_count: int,
        fallback_used: bool,
        started_at: float,
        memory_retrieval: MemoryRetrievalResult | None,
    ) -> DecisionResult:
        telemetry = DecisionTelemetry(
            provider=self.client.provider_name,
            model=model,
            prompt_version=PROMPT_VERSION,
            latency_ms=(perf_counter() - started_at) * 1000,
            token_usage=token_usage,
            validation_result=validation_result,
            attempt_count=attempt_count,
            fallback_used=fallback_used,
        )
        return DecisionResult(
            selected_action=selected_action,
            proposal=proposal,
            telemetry=telemetry,
            memory_retrieval=memory_retrieval,
        )

    def _build_fallback_result(
        self,
        *,
        context: DecisionContext,
        model: str,
        token_usage: TokenUsage,
        validation_result: DecisionValidationResult,
        attempt_count: int,
        started_at: float,
        proposal: ActionProposalV1 | None = None,
        memory_retrieval: MemoryRetrievalResult | None = None,
    ) -> DecisionResult:
        return self._build_result(
            selected_action=self._get_fallback_action(context),
            proposal=proposal,
            model=model,
            token_usage=token_usage,
            validation_result=validation_result,
            attempt_count=attempt_count,
            fallback_used=True,
            started_at=started_at,
            memory_retrieval=memory_retrieval,
        )

    def decide(self, context: DecisionContext) -> DecisionResult:
        started_at = perf_counter()
        memory_retrieval: MemoryRetrievalResult | None = None
        if self.memory_service is not None:
            memory_query = serialize_decision_context(
                context.model_copy(update={"memories": []})
            )[:4000]
            memory_retrieval = self.memory_service.retrieve(
                world_id=context.world_id,
                owner_agent_id=context.agent.agent_id,
                query_text=memory_query,
                current_tick=context.tick,
                relationship_scores={
                    relationship.other_agent_id: relationship.score
                    for relationship in context.relationships
                },
            )
            context = context.model_copy(
                update={"memories": memory_retrieval.memories}
            )

        system_prompt, user_prompt = build_decision_prompts(context)

        try:
            response = self._request_response(
                system_prompt,
                user_prompt,
            )
        except LLMTimeoutError:
            return self._build_fallback_result(
                context=context,
                model=self.client.model_name,
                token_usage=TokenUsage(),
                validation_result="timeout",
                attempt_count=1,
                started_at=started_at,
                memory_retrieval=memory_retrieval,
            )
        except LLMProviderError:
            return self._build_fallback_result(
                context=context,
                model=self.client.model_name,
                token_usage=TokenUsage(),
                validation_result="provider_error",
                attempt_count=1,
                started_at=started_at,
                memory_retrieval=memory_retrieval,
            )

        token_usage = response.token_usage
        attempt_count = 1
        validation_result: DecisionValidationResult = "valid"

        try:
            proposal = ActionProposalV1.model_validate_json(
                response.content
            )
        except ValidationError as validation_error:
            repair_system_prompt, repair_user_prompt = (
                build_repair_prompts(
                    context,
                    response.content,
                    str(validation_error),
                )
            )
            try:
                retry_response = self._request_response(
                    repair_system_prompt,
                    repair_user_prompt,
                )
            except LLMTimeoutError:
                return self._build_fallback_result(
                    context=context,
                    model=self.client.model_name,
                    token_usage=token_usage,
                    validation_result="timeout",
                    attempt_count=2,
                    started_at=started_at,
                    memory_retrieval=memory_retrieval,
                )
            except LLMProviderError:
                return self._build_fallback_result(
                    context=context,
                    model=self.client.model_name,
                    token_usage=token_usage,
                    validation_result="provider_error",
                    attempt_count=2,
                    started_at=started_at,
                    memory_retrieval=memory_retrieval,
                )

            token_usage = TokenUsage(
                input_tokens=(
                    response.token_usage.input_tokens
                    + retry_response.token_usage.input_tokens
                ),
                output_tokens=(
                    response.token_usage.output_tokens
                    + retry_response.token_usage.output_tokens
                ),
            )
            response = retry_response
            attempt_count = 2

            try:
                proposal = ActionProposalV1.model_validate_json(
                    response.content
                )
            except ValidationError:
                return self._build_fallback_result(
                    context=context,
                    model=response.model,
                    token_usage=token_usage,
                    validation_result="invalid_format",
                    attempt_count=attempt_count,
                    started_at=started_at,
                    memory_retrieval=memory_retrieval,
                )

            validation_result = "valid_after_retry"

        selected_action = self._find_action(
            context,
            proposal.action_id,
        )

        if selected_action is None:
            return self._build_fallback_result(
                context=context,
                proposal=proposal,
                model=response.model,
                token_usage=token_usage,
                validation_result="impossible_action",
                attempt_count=attempt_count,
                started_at=started_at,
                memory_retrieval=memory_retrieval,
            )

        return self._build_result(
            selected_action=selected_action,
            proposal=proposal,
            model=response.model,
            token_usage=token_usage,
            validation_result=validation_result,
            attempt_count=attempt_count,
            fallback_used=False,
            started_at=started_at,
            memory_retrieval=memory_retrieval,
        )
