"""SiteConfig referential integrity, schedules and v1 capacity caps."""

from datetime import time
from typing import Any

import pytest
from pydantic import ValidationError

from maigadi_schemas import MAX_CAMERAS, LlmMode, Schedule, Shift, SiteConfig, TimeWindow


def _rebuild(site: SiteConfig, **changes: Any) -> SiteConfig:
    data = site.model_dump()
    data.update(changes)
    return SiteConfig.model_validate(data)


def test_zone_must_reference_a_known_camera(site_config: SiteConfig) -> None:
    zones = site_config.model_dump()["zones"]
    zones[0]["camera_id"] = "cam-99"
    with pytest.raises(ValidationError, match="cam-99"):
        _rebuild(site_config, zones=zones)


def test_armed_zones_must_exist(site_config: SiteConfig) -> None:
    schedule = site_config.model_dump()["schedule"]
    schedule["armed_zone_ids"] = ["stockroom"]
    with pytest.raises(ValidationError, match="stockroom"):
        _rebuild(site_config, schedule=schedule)


def test_ids_must_be_unique(site_config: SiteConfig) -> None:
    cameras = site_config.model_dump()["cameras"]
    cameras.append({**cameras[0], "name": "Duplicate"})
    with pytest.raises(ValidationError, match="duplicate"):
        _rebuild(site_config, cameras=cameras)


@pytest.mark.parametrize("mode", list(LlmMode))
def test_camera_cap_depends_on_llm_mode(site_config: SiteConfig, mode: LlmMode) -> None:
    cap = MAX_CAMERAS[mode]
    cameras = [{"camera_id": f"cam-{i:02d}", "name": f"Cam {i}"} for i in range(cap + 1)]
    with pytest.raises(ValidationError, match="at most"):
        _rebuild(site_config, llm_mode=mode, cameras=cameras, zones=[], tripwires=[])


def test_unknown_timezone_is_rejected(site_config: SiteConfig) -> None:
    with pytest.raises(ValidationError, match="timezone"):
        _rebuild(site_config, timezone="Africa/Atlantis")


def test_site_timezone_is_usable(site_config: SiteConfig) -> None:
    assert site_config.tz.key == "Africa/Lagos"


def test_installers_cannot_be_message_recipients(site_config: SiteConfig) -> None:
    recipients = [{"user": {"user_id": "u-tech"}, "role": "installer"}]
    with pytest.raises(ValidationError, match="installer"):
        _rebuild(site_config, recipients=recipients)


def test_night_shift_may_cross_midnight() -> None:
    window = TimeWindow(start=time(19, 0), end=time(7, 0))
    assert window.crosses_midnight
    assert not TimeWindow(start=time(7, 0), end=time(19, 0)).crosses_midnight


def test_zero_length_and_timezone_aware_times_are_rejected() -> None:
    with pytest.raises(ValidationError, match="zero-length"):
        TimeWindow(start=time(7, 0), end=time(7, 0))
    with pytest.raises(ValidationError, match="site-local"):
        TimeWindow.model_validate({"start": "07:00:00Z", "end": "19:00:00"})


def test_open_24h_excludes_opening_hours(site_config: SiteConfig) -> None:
    schedule = site_config.model_dump()["schedule"]
    schedule["open_24h"] = True
    with pytest.raises(ValidationError, match="open_24h"):
        Schedule.model_validate(schedule)


def test_shift_names_must_be_unique() -> None:
    with pytest.raises(ValidationError, match="duplicate"):
        Schedule(
            shifts=[
                Shift(name="day", start=time(7, 0), end=time(19, 0)),
                Shift(name="day", start=time(19, 0), end=time(7, 0)),
            ]
        )
