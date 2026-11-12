"""Camera coverage and box system state. These intervals let answers and
summaries say what *couldn't* be seen (spec/ARCHITECTURE.md §3.5,
spec/RELIABILITY.md §2.1)."""

from enum import StrEnum
from typing import Annotated, Literal, Self

from pydantic import Field, TypeAdapter, model_validator

from maigadi_schemas._base import Model, UtcDateTime, check_interval
from maigadi_schemas.common import CameraId, SiteId


class CameraState(StrEnum):
    ONLINE = "online"
    OFFLINE = "offline"
    DEGRADED = "degraded"
    BLOCKED = "blocked"  # lens covered, view changed, tampering


class Coverage(Model):
    """One camera's state over an interval. ``end_ts=None`` means ongoing."""

    site_id: SiteId
    camera_id: CameraId
    state: CameraState
    start_ts: UtcDateTime
    end_ts: UtcDateTime | None = None
    reason: str | None = Field(default=None, max_length=200)

    @model_validator(mode="after")
    def _interval(self) -> Self:
        check_interval(self.start_ts, self.end_ts)
        return self


class PowerStateName(StrEnum):
    """States of the power state machine (spec/RELIABILITY.md §2.1)."""

    MAINS = "mains"
    ON_BATTERY = "on_battery"
    LOW_BATTERY = "low_battery"
    CRITICAL = "critical"
    SHUTTING_DOWN = "shutting_down"
    OFF = "off"
    BOOTING = "booting"
    WARMING_UP = "warming_up"
    SAFE_MODE = "safe_mode"


class NetworkStateName(StrEnum):
    ONLINE = "online"
    OFFLINE = "offline"


class NetworkLink(StrEnum):
    ETHERNET = "ethernet"
    LTE = "lte"
    NONE = "none"


class PipelineStateName(StrEnum):
    OK = "ok"
    WARMING_UP = "warming_up"
    DEGRADED = "degraded"
    SAFE_MODE = "safe_mode"  # CV-only alerts, no VLM
    DOWN = "down"


class _SystemStateBase(Model):
    site_id: SiteId
    start_ts: UtcDateTime
    end_ts: UtcDateTime | None = None
    reason: str | None = Field(default=None, max_length=200)

    @model_validator(mode="after")
    def _interval(self) -> Self:
        check_interval(self.start_ts, self.end_ts)
        return self


class PowerState(_SystemStateBase):
    kind: Literal["power"] = "power"
    state: PowerStateName
    battery_soc_pct: float | None = Field(default=None, ge=0.0, le=100.0)


class NetworkState(_SystemStateBase):
    kind: Literal["network"] = "network"
    state: NetworkStateName
    link: NetworkLink

    @model_validator(mode="after")
    def _link(self) -> Self:
        if self.state is NetworkStateName.ONLINE and self.link is NetworkLink.NONE:
            raise ValueError("an online network state needs a link")
        return self


class PipelineState(_SystemStateBase):
    kind: Literal["pipeline"] = "pipeline"
    state: PipelineStateName


SystemState = Annotated[PowerState | NetworkState | PipelineState, Field(discriminator="kind")]
"""Box power, network or pipeline state over an interval, discriminated by ``kind``."""

SYSTEM_STATE_ADAPTER: TypeAdapter[PowerState | NetworkState | PipelineState] = TypeAdapter(
    SystemState
)
