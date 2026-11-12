"""Enums and id types used across schemas."""

from enum import StrEnum
from typing import Annotated

from pydantic import StringConstraints

from maigadi_schemas._base import Slug


class Priority(StrEnum):
    """Delivery and VLM-scheduling priority (spec/ARCHITECTURE.md §3.4,
    spec/RELIABILITY.md §3.1). P0 is never shed."""

    P0 = "P0"
    P1 = "P1"
    P2 = "P2"
    P3 = "P3"


class ObjectClass(StrEnum):
    """Object classes the box tracks (spec/ARCHITECTURE.md §3.2). Never identities."""

    PERSON = "person"
    CAR = "car"
    TRUCK = "truck"
    BUS = "bus"
    MOTORCYCLE = "motorcycle"
    BICYCLE = "bicycle"


VEHICLE_CLASSES = frozenset(c for c in ObjectClass if c is not ObjectClass.PERSON)


class Role(StrEnum):
    """User roles (spec/SECURITY_AND_PRIVACY.md §A3)."""

    OWNER = "owner"
    MANAGER = "manager"
    VIEWER = "viewer"
    INSTALLER = "installer"
    SUPPORT = "support"


class Weekday(StrEnum):
    MON = "mon"
    TUE = "tue"
    WED = "wed"
    THU = "thu"
    FRI = "fri"
    SAT = "sat"
    SUN = "sun"


class LlmMode(StrEnum):
    """Hybrid: cloud LLM sees text only. Sovereign: everything on the box."""

    HYBRID = "hybrid"
    SOVEREIGN = "sovereign"


SiteId = Slug
TenantId = Slug
CameraId = Slug
UserId = Slug

EventId = Annotated[str, StringConstraints(pattern=r"^E-[1-9][0-9]{0,11}$")]
"""Per-site event id users can type in commands, e.g. ``E-9001``."""

CaptionId = Annotated[str, StringConstraints(pattern=r"^C-[1-9][0-9]{0,11}$")]
"""Per-site caption id the agent cites, e.g. ``C-120``."""
