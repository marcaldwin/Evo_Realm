from datetime import datetime
from typing import Annotated, Literal

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    JsonValue,
    field_validator,
)

from ..core.enums import StreamEventType


RequiredIdentifier = Annotated[str, Field(min_length=1, max_length=100)]
NonNegativeInteger = Annotated[int, Field(ge=0)]


class RealtimeSchema(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        frozen=True,
        str_strip_whitespace=True,
    )


class StreamEventEnvelope(RealtimeSchema):
    version: Literal["1.0"] = "1.0"
    sequence: NonNegativeInteger
    world_id: RequiredIdentifier
    tick: NonNegativeInteger
    event_type: StreamEventType
    timestamp: datetime
    payload: dict[str, JsonValue] = Field(default_factory=dict)

    @field_validator("timestamp")
    @classmethod
    def require_timezone(cls, value: datetime) -> datetime:
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError(
                "Stream event timestamp must include a timezone."
            )
        return value


class SnapshotLoadedMessage(RealtimeSchema):
    type: Literal["snapshot_loaded"]
    snapshot_tick: NonNegativeInteger
