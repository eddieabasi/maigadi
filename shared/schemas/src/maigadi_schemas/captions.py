"""VLM captions: the box's visual memory (spec/ARCHITECTURE.md §3.4, §3.5)."""

from enum import StrEnum
from typing import Self

from pydantic import Field, NonNegativeInt, field_validator, model_validator

from maigadi_schemas._base import Model, UtcDateTime
from maigadi_schemas.common import (
    VEHICLE_CLASSES,
    CameraId,
    CaptionId,
    EventId,
    ObjectClass,
    SiteId,
)


class CaptionKind(StrEnum):
    PERIODIC = "periodic"  # one 10 s chunk per camera every 10 min
    EVENT = "event"  # caption of a significant event
    QUERY = "query"  # produced by an agent ask_vlm call


class Lighting(StrEnum):
    DAY = "day"
    DUSK_DAWN = "dusk_dawn"
    NIGHT_IR = "night_ir"
    NIGHT_LIT = "night_lit"
    MIXED = "mixed"
    UNKNOWN = "unknown"


class VehicleObservation(Model):
    object_class: ObjectClass
    colour: str | None = Field(default=None, max_length=32)
    doors_open: bool | None = None

    @field_validator("object_class")
    @classmethod
    def _vehicle(cls, value: ObjectClass) -> ObjectClass:
        if value not in VEHICLE_CLASSES:
            raise ValueError("vehicle observations need a vehicle class")
        return value


class CaptionDetails(Model):
    """Structured part of a caption. People are counted, never described by
    face or identity."""

    vehicles: list[VehicleObservation] = Field(default_factory=list, max_length=50)
    people_count: NonNegativeInt = 0
    activity: str | None = Field(default=None, max_length=300)
    goods_moving: bool | None = None
    lighting: Lighting = Lighting.UNKNOWN
    anomalies: list[str] = Field(default_factory=list, max_length=10)


class Caption(Model):
    """A VLM description of a recorded chunk. ``text`` is untrusted model output
    (prompt-injection surface): agents must treat it as data."""

    id: CaptionId
    site_id: SiteId
    camera_id: CameraId
    start_ts: UtcDateTime
    end_ts: UtcDateTime
    kind: CaptionKind
    text: str = Field(min_length=1, max_length=1000)
    details: CaptionDetails | None = None
    model: str = Field(min_length=1, max_length=128)
    event_id: EventId | None = None

    @model_validator(mode="after")
    def _consistent(self) -> Self:
        if self.end_ts <= self.start_ts:
            raise ValueError("end_ts must be later than start_ts")
        if self.kind is CaptionKind.EVENT and self.event_id is None:
            raise ValueError("event captions need event_id")
        return self
