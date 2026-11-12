"""Canonical event (spec/ARCHITECTURE.md §9 and §3.5)."""

from enum import StrEnum
from typing import Self

from pydantic import Field, JsonValue, NonNegativeInt, model_validator

from maigadi_schemas._base import (
    LOCAL_ONLY,
    Identifier,
    LocalMediaRef,
    Model,
    UtcDateTime,
    check_interval,
)
from maigadi_schemas.common import CameraId, EventId, ObjectClass, SiteId


class EventSource(StrEnum):
    BEHAVIOR_ANALYTICS = "behavior_analytics"
    RULES_GATE = "rules_gate"
    ALERT_BRIDGE = "alert_bridge"
    COVERAGE_MONITOR = "coverage_monitor"
    VISUAL_MEMORY = "visual_memory"


class Verdict(StrEnum):
    """VLM verification outcome. VSS Alert Bridge's ``verification-failed`` maps
    to ``verification_failed``."""

    CONFIRMED = "confirmed"
    REJECTED = "rejected"
    VERIFICATION_FAILED = "verification_failed"


class AlertState(StrEnum):
    NONE = "none"  # log-only event (e.g. truck arrival)
    SUPPRESSED = "suppressed"  # filtered by the rules gate (unarmed, cooldown, budget)
    VERIFYING = "verifying"
    REJECTED = "rejected"  # VLM said no: stored, never sent
    HELD = "held"  # verification failed on a non-high-severity type
    QUEUED = "queued"  # in the outbox
    DELIVERED = "delivered"


class VlmResult(Model):
    """Output of a VLM look at an event. ``text`` is untrusted model output:
    treat it as data, never as instructions."""

    verdict: Verdict | None = None
    text: str | None = Field(default=None, max_length=2000)
    model: str = Field(min_length=1, max_length=128)
    latency_ms: NonNegativeInt


class EventMedia(Model):
    clip_local: LocalMediaRef | None = None
    thumb_local: LocalMediaRef | None = None


class Event(Model):
    """Something that happened on one camera. ``type`` comes from the active
    rule pack's vocabulary, so verticals can add types without schema changes."""

    id: EventId
    site_id: SiteId
    camera_id: CameraId
    zone_ids: list[Identifier] = Field(default_factory=list, max_length=16)
    type: Identifier
    object_class: ObjectClass | None = None
    track_id: str | None = Field(default=None, min_length=1, max_length=64)
    start_ts: UtcDateTime
    end_ts: UtcDateTime | None = None
    source: EventSource
    confidence: float | None = Field(default=None, ge=0.0, le=1.0)
    vlm: VlmResult | None = None
    alert_state: AlertState = AlertState.NONE
    media: EventMedia | None = Field(default=None, json_schema_extra=LOCAL_ONLY)
    attrs: dict[str, JsonValue] = Field(default_factory=dict)

    @model_validator(mode="after")
    def _consistent(self) -> Self:
        check_interval(self.start_ts, self.end_ts)
        if self.alert_state is AlertState.REJECTED and (
            self.vlm is None or self.vlm.verdict is not Verdict.REJECTED
        ):
            raise ValueError("alert_state 'rejected' requires a VLM verdict of 'rejected'")
        return self
