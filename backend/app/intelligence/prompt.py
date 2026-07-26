import json

from .schemas import DecisionContext


PROMPT_VERSION = "decision-v1"


def serialize_decision_context(context: DecisionContext) -> str:
    payload = context.model_dump(
        mode="json",
        exclude_none=True,
        exclude={"fallback_action_id"},
    )
    return json.dumps(
        payload,
        separators=(",", ":"),
        sort_keys=True,
    )


SYSTEM_PROMPT = (
    "You select one action for an agent in a deterministic simulation. "
    "Choose exactly one action_id from available_actions. "
    "Do not invent actions or modify their trusted parameters. "
    "Use the agent state, goals, nearby entities, relationships, and "
    "action descriptions when deciding. "
    "Return only data matching the supplied response schema."
)


def build_decision_prompts(
    context: DecisionContext,
) -> tuple[str, str]:
    user_prompt = (
        "Select the single best valid action for this context:\n"
        f"{serialize_decision_context(context)}"
    )
    return SYSTEM_PROMPT, user_prompt


def build_repair_prompts(
    context: DecisionContext,
    invalid_response: str,
    validation_error: str,
) -> tuple[str, str]:
    response_excerpt = invalid_response[:1000]
    error_excerpt = validation_error[:500]

    user_prompt = (
        "Your previous response failed schema validation. "
        "Return one corrected response matching the supplied schema.\n"
        f"Previous response: {response_excerpt}\n"
        f"Validation error: {error_excerpt}\n"
        "Use the same decision context:\n"
        f"{serialize_decision_context(context)}"
    )
    return SYSTEM_PROMPT, user_prompt