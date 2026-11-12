"""Every schema survives a JSON round trip, and the spec's own examples validate."""

import json
from pathlib import Path

import pytest
import yaml
from pydantic import BaseModel

from maigadi_schemas import SYSTEM_STATE_ADAPTER, Event, PolicyPack, PowerState

FIXTURES = Path(__file__).parent / "fixtures"

MODEL_FIXTURES = [
    "event",
    "caption",
    "coverage",
    "outbound_alert",
    "clip_message",
    "inbound_event",
    "inbox_message",
    "site_config",
    "rule_pack",
    "policy_pack",
]


@pytest.mark.parametrize("fixture_name", MODEL_FIXTURES)
def test_json_round_trip(fixture_name: str, request: pytest.FixtureRequest) -> None:
    original = request.getfixturevalue(fixture_name)
    assert isinstance(original, BaseModel)
    restored = type(original).model_validate_json(original.model_dump_json())
    assert restored == original


def test_system_state_round_trips_through_discriminated_union(power_state: PowerState) -> None:
    payload = SYSTEM_STATE_ADAPTER.dump_json(power_state)
    restored = SYSTEM_STATE_ADAPTER.validate_json(payload)
    assert isinstance(restored, PowerState)
    assert restored == power_state


def test_spec_canonical_event_example_validates() -> None:
    """spec/ARCHITECTURE.md §9 must stay a valid Event."""
    raw = json.loads((FIXTURES / "spec_event.json").read_text(encoding="utf-8"))
    event = Event.model_validate(raw)
    assert event.id == "E-9001"
    assert event.zone_ids == ["yard"]
    assert event.model_dump(mode="json")["start_ts"] == "2026-11-07T01:14:05Z"


def test_spec_policy_pack_example_validates() -> None:
    """spec/SECURITY_AND_PRIVACY.md §B4 must stay a valid PolicyPack."""
    raw = yaml.safe_load((FIXTURES / "ng-ndpa.yaml").read_text(encoding="utf-8"))
    pack = PolicyPack.model_validate(raw)
    assert pack.ref == "ng-ndpa@1.0.0"
    assert pack.retention.continuous_recording_days == 7
