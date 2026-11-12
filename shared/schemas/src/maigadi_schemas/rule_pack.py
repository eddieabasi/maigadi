"""Rule packs: per-vertical vocabulary of zones, alert types and rules
(spec/ARCHITECTURE.md §3.3). Versioned YAML in ``shared/rule_packs/``."""

from enum import StrEnum
from typing import Self

from pydantic import Field, NonNegativeFloat, PositiveInt, model_validator

from maigadi_schemas._base import Identifier, Model, SemVer, Slug, require_unique
from maigadi_schemas.common import ObjectClass


class Severity(StrEnum):
    HIGH = "high"
    NORMAL = "normal"
    INFO = "info"


class AlertCategory(StrEnum):
    SECURITY = "security"
    LOGISTICS = "logistics"
    CAMERA_HEALTH = "camera_health"
    STAFF_PRESENCE = "staff_presence"  # policy packs may forbid these


class UnverifiedPolicy(StrEnum):
    """What to do when VLM verification fails (timeout or error)."""

    HOLD = "hold"
    SEND_AS_UNVERIFIED = "send_as_unverified"


class Trigger(StrEnum):
    ROI_ENTER = "roi_enter"
    ROI_EXIT = "roi_exit"
    TRIPWIRE_CROSS = "tripwire_cross"
    DWELL = "dwell"
    RESTRICTED_AREA = "restricted_area"
    CAMERA_OFFLINE = "camera_offline"
    CAMERA_TAMPER = "camera_tamper"


CAMERA_TRIGGERS = frozenset({Trigger.CAMERA_OFFLINE, Trigger.CAMERA_TAMPER})


class ArmCondition(StrEnum):
    ARMED = "armed"  # only while the zone is armed (site closed, or always-armed zone)
    ALWAYS = "always"


class ZoneTemplate(Model):
    template: Identifier
    default_name: str = Field(min_length=1, max_length=64)
    default_group: Identifier | None = None


class AlertType(Model):
    name: Identifier
    category: AlertCategory
    severity: Severity
    deliver: bool  # False: logged and summarised, never pushed (e.g. truck arrival)
    verify_with_vlm: bool
    vlm_prompt: str | None = Field(default=None, min_length=1, max_length=2000)
    unverified_policy: UnverifiedPolicy = UnverifiedPolicy.HOLD

    @model_validator(mode="after")
    def _consistent(self) -> Self:
        if self.verify_with_vlm and self.vlm_prompt is None:
            raise ValueError(f"{self.name}: vlm_prompt is required when verify_with_vlm is true")
        if self.category is AlertCategory.CAMERA_HEALTH and self.verify_with_vlm:
            raise ValueError(f"{self.name}: camera_health alert types skip VLM verification")
        if self.unverified_policy is UnverifiedPolicy.SEND_AS_UNVERIFIED and (
            self.severity is not Severity.HIGH or not self.verify_with_vlm
        ):
            raise ValueError(
                f"{self.name}: only high severity VLM-verified types may send unverified"
            )
        return self


class Rule(Model):
    name: Identifier
    trigger: Trigger
    object_classes: list[ObjectClass] = Field(default_factory=list)
    zone_templates: list[Identifier] = Field(default_factory=list)  # empty: any zone
    when: ArmCondition
    emits: Identifier  # name of an AlertType in the same pack
    min_dwell_s: NonNegativeFloat | None = None  # overrides GateDefaults.min_dwell_s

    @model_validator(mode="after")
    def _classes_fit_trigger(self) -> Self:
        if self.trigger in CAMERA_TRIGGERS and self.object_classes:
            raise ValueError(f"{self.name}: camera triggers take no object_classes")
        if self.trigger not in CAMERA_TRIGGERS and not self.object_classes:
            raise ValueError(f"{self.name}: object_classes must not be empty")
        require_unique("object class", self.object_classes)
        return self


class GateDefaults(Model):
    """Rules-gate defaults (spec/ARCHITECTURE.md §3.3)."""

    cooldown_s: PositiveInt = 300
    min_dwell_s: NonNegativeFloat = 3.0
    nightly_alert_budget: PositiveInt = 10  # above this, alerts are batched
    bay_dwell_alert_after_s: PositiveInt | None = None


class CameraHealth(Model):
    offline_alert_after_armed_s: PositiveInt = 600
    offline_alert_after_unarmed_s: PositiveInt = 7200


class RulePack(Model):
    id: Slug
    version: SemVer
    description: str = Field(min_length=1, max_length=500)
    zone_templates: list[ZoneTemplate] = Field(default_factory=list)
    alert_types: list[AlertType] = Field(min_length=1)
    rules: list[Rule] = Field(min_length=1)
    gate: GateDefaults = Field(default_factory=GateDefaults)
    camera_health: CameraHealth = Field(default_factory=CameraHealth)

    @property
    def ref(self) -> str:
        return f"{self.id}@{self.version}"

    @model_validator(mode="after")
    def _references(self) -> Self:
        require_unique("zone template", (t.template for t in self.zone_templates))
        require_unique("alert type", (a.name for a in self.alert_types))
        require_unique("rule", (r.name for r in self.rules))
        alert_types = {a.name for a in self.alert_types}
        templates = {t.template for t in self.zone_templates}
        for rule in self.rules:
            if rule.emits not in alert_types:
                raise ValueError(f"rule {rule.name} emits undeclared alert type {rule.emits}")
            unknown = set(rule.zone_templates) - templates
            if unknown:
                raise ValueError(
                    f"rule {rule.name} uses undeclared zone templates: {', '.join(sorted(unknown))}"
                )
        return self
