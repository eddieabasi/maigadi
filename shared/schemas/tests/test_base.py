"""Cross-cutting rules: UTC timestamps, strictness, immutability, egress stripping."""

from datetime import UTC, datetime, timedelta, timezone

import pytest
from hypothesis import given
from hypothesis import strategies as st
from pydantic import ValidationError

from maigadi_schemas import Coverage, Event, cloud_dump

WAT = timezone(timedelta(hours=1))  # West Africa Time, no DST


def _event_payload(**overrides: object) -> dict[str, object]:
    payload: dict[str, object] = {
        "id": "E-1",
        "site_id": "ng-lag-agbara-01",
        "camera_id": "cam-01",
        "type": "truck_arrival",
        "start_ts": "2026-11-07T08:00:00Z",
        "source": "behavior_analytics",
    }
    payload.update(overrides)
    return payload


def test_naive_datetimes_are_rejected() -> None:
    with pytest.raises(ValidationError, match="timezone"):
        Event.model_validate(_event_payload(start_ts=datetime(2026, 11, 7, 8, 0)))  # noqa: DTZ001


def test_aware_datetimes_are_normalised_to_utc() -> None:
    event = Event.model_validate(_event_payload(start_ts=datetime(2026, 11, 7, 9, 0, tzinfo=WAT)))
    assert event.start_ts == datetime(2026, 11, 7, 8, 0, tzinfo=UTC)
    assert event.start_ts.tzinfo is UTC
    assert event.model_dump(mode="json")["start_ts"] == "2026-11-07T08:00:00Z"


@given(st.datetimes(timezones=st.timezones()))
def test_any_aware_datetime_keeps_its_instant_and_becomes_utc(ts: datetime) -> None:
    event = Event.model_validate(_event_payload(start_ts=ts))
    # Compare instants, not datetimes: PEP 495 makes ambiguous (DST-fold) times
    # never equal across zones, which hypothesis finds quickly.
    assert event.start_ts.timestamp() == ts.timestamp()
    assert event.start_ts.utcoffset() == timedelta(0)


def test_interval_end_before_start_is_rejected() -> None:
    with pytest.raises(ValidationError, match="end_ts"):
        Event.model_validate(_event_payload(end_ts="2026-11-07T07:59:59Z"))


def test_unknown_fields_are_rejected() -> None:
    with pytest.raises(ValidationError, match="extra"):
        Event.model_validate(_event_payload(face_id="abc"))


def test_models_are_immutable(coverage: Coverage) -> None:
    with pytest.raises(ValidationError, match="frozen"):
        coverage.reason = "edited"  # type: ignore[misc]


@pytest.mark.parametrize("bad_id", ["9001", "E-", "E-0", "e-12", "E-12a"])
def test_event_ids_are_human_typable(bad_id: str) -> None:
    with pytest.raises(ValidationError, match="id"):
        Event.model_validate(_event_payload(id=bad_id))


def test_cloud_dump_drops_local_only_media(event: Event) -> None:
    assert event.media is not None
    local = event.model_dump(mode="json")
    cloud = cloud_dump(event)
    assert "media" in local
    assert "media" not in cloud
    assert {k: v for k, v in local.items() if k != "media"} == cloud


def test_media_refs_must_be_local_vios_uris() -> None:
    with pytest.raises(ValidationError, match="clip_local"):
        Event.model_validate(
            _event_payload(media={"clip_local": "https://bucket.example/clip.mp4"})
        )
