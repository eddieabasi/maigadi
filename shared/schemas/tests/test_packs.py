"""Rule packs and policy packs: invariants that no pack may weaken."""

from typing import Any

import pytest
from pydantic import ValidationError

from maigadi_schemas import AlertCategory, PolicyPack, RulePack, Severity, Trigger


def _pack(pack: PolicyPack, section: str, **changes: Any) -> dict[str, Any]:
    data = pack.model_dump(mode="json")
    data[section] = {**data[section], **changes}
    return data


@pytest.mark.parametrize(
    "feature",
    [
        "face_recognition",
        "person_reid",
        "plate_recognition",
        "audio",
        "emotion_or_behaviour_scoring",
    ],
)
def test_identification_features_cannot_be_enabled(policy_pack: PolicyPack, feature: str) -> None:
    with pytest.raises(ValidationError, match=feature):
        PolicyPack.model_validate(_pack(policy_pack, "features", **{feature: "allowed_opt_in"}))


def test_clip_egress_always_requires_a_pin(policy_pack: PolicyPack) -> None:
    with pytest.raises(ValidationError, match="require_pin"):
        PolicyPack.model_validate(_pack(policy_pack, "clip_egress", require_pin=False))


def test_only_owners_and_managers_may_request_clips(policy_pack: PolicyPack) -> None:
    with pytest.raises(ValidationError, match="viewer"):
        PolicyPack.model_validate(_pack(policy_pack, "clip_egress", roles=["owner", "viewer"]))


def test_rules_must_emit_a_declared_alert_type(rule_pack: RulePack) -> None:
    data = rule_pack.model_dump()
    data["rules"][0]["emits"] = "teleportation"
    with pytest.raises(ValidationError, match="teleportation"):
        RulePack.model_validate(data)


def test_rules_must_use_declared_zone_templates(rule_pack: RulePack) -> None:
    data = rule_pack.model_dump()
    data["rules"][1]["zone_templates"] = ["helipad"]
    with pytest.raises(ValidationError, match="helipad"):
        RulePack.model_validate(data)


def test_unverified_sending_is_only_for_high_severity(rule_pack: RulePack) -> None:
    data = rule_pack.model_dump()
    data["alert_types"][0]["severity"] = Severity.NORMAL
    with pytest.raises(ValidationError, match="high"):
        RulePack.model_validate(data)


def test_vlm_verified_alert_types_need_a_prompt(rule_pack: RulePack) -> None:
    data = rule_pack.model_dump()
    data["alert_types"][0]["vlm_prompt"] = None
    with pytest.raises(ValidationError, match="vlm_prompt"):
        RulePack.model_validate(data)


def test_camera_health_alerts_skip_the_vlm(rule_pack: RulePack) -> None:
    data = rule_pack.model_dump()
    camera = next(a for a in data["alert_types"] if a["category"] == AlertCategory.CAMERA_HEALTH)
    camera.update(verify_with_vlm=True, vlm_prompt="Is the camera working?")
    with pytest.raises(ValidationError, match="camera_health"):
        RulePack.model_validate(data)


def test_object_classes_match_the_trigger(rule_pack: RulePack) -> None:
    data = rule_pack.model_dump()
    data["rules"][0]["object_classes"] = []
    with pytest.raises(ValidationError, match="object_classes"):
        RulePack.model_validate(data)
    data = rule_pack.model_dump()
    camera_rule = next(r for r in data["rules"] if r["trigger"] == Trigger.CAMERA_OFFLINE)
    camera_rule["object_classes"] = ["person"]
    with pytest.raises(ValidationError, match="object_classes"):
        RulePack.model_validate(data)


def test_pack_refs_combine_id_and_version(rule_pack: RulePack, policy_pack: PolicyPack) -> None:
    assert rule_pack.ref == "warehouse-v1@1.0.0"
    assert policy_pack.ref == "ng-ndpa@1.0.0"
