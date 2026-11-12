"""Building blocks shared by every schema: strict base model, UTC timestamps, id
types, and the egress helpers that keep local-only data on the box."""

import re
from collections import Counter
from collections.abc import Iterable
from datetime import UTC, datetime, time
from typing import Annotated, Any, Final

from pydantic import (
    AfterValidator,
    AwareDatetime,
    BaseModel,
    ConfigDict,
    StringConstraints,
)
from pydantic.fields import FieldInfo


class Model(BaseModel):
    """Base for every maigadi schema: unknown fields are rejected and instances
    are immutable. Build a new instance instead of editing one."""

    model_config = ConfigDict(extra="forbid", frozen=True, validate_default=True)


# --------------------------------------------------------------------- time


def _to_utc(value: datetime) -> datetime:
    return value.astimezone(UTC)


UtcDateTime = Annotated[AwareDatetime, AfterValidator(_to_utc)]
"""Timezone-aware timestamp normalised to UTC. Naive datetimes are rejected
(CLAUDE.md: store UTC, convert to site time only at the edges)."""


def _site_local_time(value: time) -> time:
    if value.tzinfo is not None:
        raise ValueError("times of day are site-local wall-clock times; drop the UTC offset")
    return value


LocalTime = Annotated[time, AfterValidator(_site_local_time)]
"""Wall-clock time of day in the site's timezone (e.g. opening hours)."""


def require_unique(kind: str, values: Iterable[str]) -> None:
    """Raise listing any duplicated values, e.g. two cameras with one id."""
    duplicates = sorted(v for v, n in Counter(values).items() if n > 1)
    if duplicates:
        raise ValueError(f"duplicate {kind}: {', '.join(duplicates)}")


def check_interval(start: datetime, end: datetime | None) -> None:
    """Raise if an interval ends before it starts. ``end=None`` means ongoing."""
    if end is not None and end < start:
        raise ValueError("end_ts must not be earlier than start_ts")


# ---------------------------------------------------------------- id types

Slug = Annotated[str, StringConstraints(pattern=r"^[a-z0-9][a-z0-9-]{0,62}$")]
"""Lowercase id with hyphens, e.g. ``ng-lag-agbara-01``, ``cam-07``."""

Identifier = Annotated[str, StringConstraints(pattern=r"^[a-z0-9][a-z0-9_-]{0,62}$")]
"""Lowercase id that may contain underscores, e.g. ``loading_bay``."""

SemVer = Annotated[str, StringConstraints(pattern=r"^\d+\.\d+\.\d+$")]

PackRef = Annotated[str, StringConstraints(pattern=r"^[a-z0-9][a-z0-9-]{0,62}@\d+\.\d+\.\d+$")]
"""Versioned pack reference, e.g. ``warehouse-v1@1.0.0``."""

LocalMediaRef = Annotated[str, StringConstraints(pattern=r"^vios://\S+$")]
"""Reference to footage stored on the box (VIOS). Never valid off the box."""


# ------------------------------------------------------------------ egress

LOCAL_ONLY: Final[dict[str, Any]] = {"x-maigadi-local-only": True}
"""Pass as ``json_schema_extra`` on fields that must never leave the box."""


def is_local_only(field: FieldInfo) -> bool:
    extra = field.json_schema_extra
    return isinstance(extra, dict) and extra.get("x-maigadi-local-only") is True


def _exclusions(value: object) -> Any:
    """Build a pydantic ``exclude`` spec covering every local-only field in ``value``."""
    if isinstance(value, BaseModel):
        spec: dict[Any, Any] = {}
        for name, field in type(value).model_fields.items():
            if is_local_only(field):
                spec[name] = True
            elif child := _exclusions(getattr(value, name)):
                spec[name] = child
        return spec
    if isinstance(value, list | tuple):
        return {i: child for i, item in enumerate(value) if (child := _exclusions(item))}
    if isinstance(value, dict):
        return {k: child for k, v in value.items() if (child := _exclusions(v))}
    return None


def cloud_dump(model: BaseModel) -> dict[str, Any]:
    """JSON-ready dict for anything that leaves the box. Local-only fields are
    dropped at every nesting level (e.g. ``Event.media``)."""
    return model.model_dump(mode="json", exclude=_exclusions(model) or None)


_LOCAL_REFERENCE = re.compile(r"(?i)\b(?:rtsps?|vios)://|data:(?:image|video)/")


def _no_local_references(text: str) -> str:
    if _LOCAL_REFERENCE.search(text):
        raise ValueError(
            "text must not contain camera URLs, local media references or inline media"
        )
    return text


CloudText = Annotated[str, AfterValidator(_no_local_references)]
"""Text that may leave the box: no RTSP URLs (they can embed camera
credentials), no ``vios://`` refs, no inline image or video data."""
