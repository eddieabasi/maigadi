"""Policy packs: per-jurisdiction privacy settings (spec/SECURITY_AND_PRIVACY.md
§B4). Versioned YAML in ``shared/policy_packs/``; exactly one per site.

Identification features are typed ``Literal["forbidden"]``, so no pack can
enable them (PRD P4). Clip egress always requires a PIN (CLAUDE.md invariant).
"""

from enum import StrEnum
from typing import Annotated, Final, Literal, Self

from pydantic import Field, PositiveInt, StringConstraints, model_validator

from maigadi_schemas._base import Identifier, Model, SemVer, Slug, require_unique
from maigadi_schemas.common import LlmMode, Role

Forbidden = Literal["forbidden"]
LanguageCode = Annotated[str, StringConstraints(pattern=r"^[a-z]{2,3}$")]  # ISO 639
CLIP_ROLES: Final = frozenset({Role.OWNER, Role.MANAGER})


class LegalReview(StrEnum):
    PENDING = "pending"  # blocks GA in that jurisdiction
    APPROVED = "approved"


class OptIn(StrEnum):
    FORBIDDEN = "forbidden"
    ALLOWED_OPT_IN = "allowed_opt_in"


class Requirement(StrEnum):
    REQUIRED = "required"
    RECOMMENDED = "recommended"
    NOT_REQUIRED = "not_required"


class Features(Model):
    face_recognition: Forbidden
    person_reid: Forbidden
    plate_recognition: Forbidden
    audio: Forbidden
    emotion_or_behaviour_scoring: Forbidden
    staff_presence_rules: OptIn


class LlmPolicy(Model):
    allowed_modes: list[LlmMode] = Field(min_length=1)
    inference_geo: Identifier  # "any", or a provider geography such as "us"
    provider_zdr_required: bool

    @model_validator(mode="after")
    def _unique(self) -> Self:
        require_unique("llm mode", self.allowed_modes)
        return self


class Retention(Model):
    continuous_recording_days: PositiveInt = Field(le=3650)
    event_clips_days: PositiveInt = Field(le=3650)
    events_and_captions_days: PositiveInt = Field(le=3650)
    conversations_days: PositiveInt = Field(le=3650)
    audit_days: PositiveInt = Field(le=3650)


class ClipEgress(Model):
    roles: list[Role] = Field(min_length=1)
    require_pin: Literal[True]
    max_seconds: PositiveInt = Field(le=60)
    max_per_user_per_day: int = Field(ge=0, le=100)
    watermark: bool = True

    @model_validator(mode="after")
    def _roles(self) -> Self:
        require_unique("role", self.roles)
        for role in self.roles:
            if role not in CLIP_ROLES:
                raise ValueError(f"role {role.value} may not request clips")
        return self


class Signage(Model):
    template: Slug
    languages: list[LanguageCode] = Field(min_length=1)
    photo_required: bool


class CommissioningRequirements(Model):
    dpia: Requirement
    lia: Requirement
    staff_notice: Requirement


class Dsar(Model):
    response_days: PositiveInt = Field(le=365)
    third_party_blur: bool


class PolicyPack(Model):
    id: Slug
    version: SemVer
    jurisdiction: str = Field(pattern=r"^[A-Z]{2}(-[A-Z0-9]{1,3})?$")  # e.g. NG, EU, US-IL
    legal_review: LegalReview
    features: Features
    llm: LlmPolicy
    retention: Retention
    clip_egress: ClipEgress
    signage: Signage
    commissioning_requirements: CommissioningRequirements
    dsar: Dsar

    @property
    def ref(self) -> str:
        return f"{self.id}@{self.version}"
