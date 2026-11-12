"""Site configuration: the desired state the control plane syncs to a box
(spec/ARCHITECTURE.md §8). Camera credentials and stream URLs are deliberately
absent: they live only in the box's local vault."""

from collections.abc import Mapping
from datetime import date
from types import MappingProxyType
from typing import Final, Self
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from pydantic import Field, PositiveInt, field_validator, model_validator

from maigadi_schemas._base import Identifier, LocalTime, Model, PackRef, Slug, require_unique
from maigadi_schemas.common import CameraId, LlmMode, Role, SiteId, TenantId, Weekday
from maigadi_schemas.messages import UserRef

MAX_CAMERAS: Final[Mapping[LlmMode, int]] = MappingProxyType(
    {LlmMode.HYBRID: 16, LlmMode.SOVEREIGN: 12}
)
"""v1 cameras per box (spec/HARDWARE_AND_DEPLOYMENT.md §4). ASSUMPTION until
the M0 capacity benchmark (T0.4a/b) confirms or changes these caps."""

RECIPIENT_ROLES: Final = frozenset({Role.OWNER, Role.MANAGER, Role.VIEWER})


class Point(Model):
    """Point in normalised frame coordinates (0..1, origin top-left)."""

    x: float = Field(ge=0.0, le=1.0)
    y: float = Field(ge=0.0, le=1.0)


class CameraConfig(Model):
    camera_id: CameraId
    name: str = Field(min_length=1, max_length=64)
    enabled: bool = True


class ZoneConfig(Model):
    zone_id: Identifier
    name: str = Field(min_length=1, max_length=64)
    camera_id: CameraId
    polygon: list[Point] = Field(min_length=3, max_length=32)
    template: Identifier | None = None  # rule-pack zone template, e.g. "loading_bay"
    group: Identifier | None = None  # zone group used by summaries


class TripwireConfig(Model):
    tripwire_id: Identifier
    name: str = Field(min_length=1, max_length=64)
    camera_id: CameraId
    line: tuple[Point, Point]


class TimeWindow(Model):
    """Daily window in site-local time. ``end < start`` crosses midnight."""

    start: LocalTime
    end: LocalTime

    @model_validator(mode="after")
    def _non_empty(self) -> Self:
        if self.start == self.end:
            raise ValueError("zero-length window: start and end are equal")
        return self

    @property
    def crosses_midnight(self) -> bool:
        return self.end < self.start


class Shift(TimeWindow):
    name: Identifier  # e.g. "day", "night"


class OpeningWindow(Model):
    days: list[Weekday] = Field(min_length=1, max_length=7)
    open: LocalTime
    close: LocalTime

    @model_validator(mode="after")
    def _valid(self) -> Self:
        require_unique("weekday", self.days)
        if self.open == self.close:
            raise ValueError("zero-length opening window; use Schedule.open_24h for 24 h sites")
        return self


class Schedule(Model):
    """When the site is open, its shifts, and which zones are armed.

    ``armed_zone_ids`` are armed whenever the site is closed (outside opening
    hours and on holidays). ``always_armed_zone_ids`` are armed around the clock.
    """

    opening_hours: list[OpeningWindow] = Field(default_factory=list, max_length=14)
    open_24h: bool = False
    shifts: list[Shift] = Field(min_length=1, max_length=6)
    armed_zone_ids: list[Identifier] = Field(default_factory=list)
    always_armed_zone_ids: list[Identifier] = Field(default_factory=list)
    holidays: list[date] = Field(default_factory=list, max_length=100)

    @model_validator(mode="after")
    def _consistent(self) -> Self:
        if self.open_24h and self.opening_hours:
            raise ValueError("open_24h and opening_hours are mutually exclusive")
        require_unique("shift name", (s.name for s in self.shifts))
        both = set(self.armed_zone_ids) & set(self.always_armed_zone_ids)
        if both:
            raise ValueError(f"zones both armed and always armed: {', '.join(sorted(both))}")
        return self


class Recipient(Model):
    user: UserRef
    role: Role
    alerts: bool = True
    summaries: bool = True


class SiteConfig(Model):
    site_id: SiteId
    tenant_id: TenantId
    name: str = Field(min_length=1, max_length=64)
    country: str = Field(pattern=r"^[A-Z]{2}$")  # ISO 3166-1 alpha-2
    timezone: str = Field(min_length=1, max_length=64)  # IANA, e.g. "Africa/Lagos"
    data_region: Slug
    config_version: PositiveInt
    llm_mode: LlmMode
    policy_pack: PackRef
    rule_pack: PackRef
    cameras: list[CameraConfig] = Field(min_length=1)
    zones: list[ZoneConfig] = Field(default_factory=list)
    tripwires: list[TripwireConfig] = Field(default_factory=list)
    schedule: Schedule
    recipients: list[Recipient] = Field(default_factory=list)

    @field_validator("timezone")
    @classmethod
    def _known_timezone(cls, value: str) -> str:
        try:
            ZoneInfo(value)
        except (ZoneInfoNotFoundError, ValueError) as exc:
            raise ValueError(f"unknown IANA timezone: {value}") from exc
        return value

    @property
    def tz(self) -> ZoneInfo:
        return ZoneInfo(self.timezone)

    @model_validator(mode="after")
    def _referential_integrity(self) -> Self:
        cap = MAX_CAMERAS[self.llm_mode]
        if len(self.cameras) > cap:
            raise ValueError(f"{self.llm_mode.value} mode supports at most {cap} cameras per box")
        require_unique("camera_id", (c.camera_id for c in self.cameras))
        require_unique("zone_id", (z.zone_id for z in self.zones))
        require_unique("tripwire_id", (t.tripwire_id for t in self.tripwires))
        require_unique("recipient", (r.user.user_id for r in self.recipients))

        cameras = {c.camera_id for c in self.cameras}
        placed: list[ZoneConfig | TripwireConfig] = [*self.zones, *self.tripwires]
        for item in placed:
            if item.camera_id not in cameras:
                raise ValueError(f"{item.name!r} references unknown camera {item.camera_id}")

        zones = {z.zone_id for z in self.zones}
        unknown = (
            set(self.schedule.armed_zone_ids) | set(self.schedule.always_armed_zone_ids)
        ) - zones
        if unknown:
            raise ValueError(f"schedule references unknown zones: {', '.join(sorted(unknown))}")

        for recipient in self.recipients:
            if recipient.role not in RECIPIENT_ROLES:
                raise ValueError(f"role {recipient.role.value} cannot receive site messages")
        return self
