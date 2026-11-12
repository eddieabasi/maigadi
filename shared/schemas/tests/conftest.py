"""Valid example instances of every schema, shared by the schema tests."""

from datetime import UTC, date, datetime, time, timedelta
from pathlib import Path

import pytest
import yaml

from maigadi_schemas import (
    AlertCategory,
    AlertState,
    AlertType,
    ArmCondition,
    CameraConfig,
    CameraState,
    Caption,
    CaptionDetails,
    CaptionKind,
    Channel,
    ClipRef,
    CommandName,
    Coverage,
    Event,
    EventMedia,
    EventSource,
    InboundEvent,
    InboxMessage,
    Lighting,
    LlmMode,
    MessageKind,
    ObjectClass,
    OpeningWindow,
    OutboundMessage,
    Point,
    PolicyPack,
    PowerState,
    PowerStateName,
    Priority,
    QuickAction,
    Recipient,
    Role,
    Rule,
    RulePack,
    Schedule,
    Severity,
    Shift,
    SiteConfig,
    Trigger,
    UnverifiedPolicy,
    UserRef,
    VehicleObservation,
    Verdict,
    VlmResult,
    Weekday,
    ZoneConfig,
    ZoneTemplate,
)

FIXTURES = Path(__file__).parent / "fixtures"
T0 = datetime(2026, 11, 7, 1, 14, 5, tzinfo=UTC)
OWNER = UserRef(user_id="u-ada")


@pytest.fixture
def event() -> Event:
    return Event(
        id="E-9001",
        site_id="ng-lag-agbara-01",
        camera_id="cam-07",
        zone_ids=["yard"],
        type="after_hours_person",
        object_class=ObjectClass.PERSON,
        track_id="t-7-55120",
        start_ts=T0,
        end_ts=T0 + timedelta(seconds=36),
        source=EventSource.ALERT_BRIDGE,
        confidence=0.87,
        vlm=VlmResult(
            verdict=Verdict.CONFIRMED,
            text="One person climbing the perimeter wall near the generator house.",
            model="cosmos3-nano-reasoner:bf16",
            latency_ms=9120,
        ),
        alert_state=AlertState.DELIVERED,
        media=EventMedia(clip_local="vios://clips/e-9001.mp4", thumb_local="vios://snap/e-9001"),
        attrs={"armed": True, "rule_pack": "warehouse-v1@1.0.0"},
    )


@pytest.fixture
def caption() -> Caption:
    return Caption(
        id="C-120",
        site_id="ng-lag-agbara-01",
        camera_id="cam-02",
        start_ts=T0,
        end_ts=T0 + timedelta(seconds=10),
        kind=CaptionKind.PERIODIC,
        text="One truck at bay 2 with doors open; two people moving cartons into it.",
        details=CaptionDetails(
            vehicles=[
                VehicleObservation(object_class=ObjectClass.TRUCK, colour="white", doors_open=True)
            ],
            people_count=2,
            activity="loading cartons",
            goods_moving=True,
            lighting=Lighting.NIGHT_LIT,
            anomalies=[],
        ),
        model="cosmos3-nano-reasoner:bf16",
    )


@pytest.fixture
def coverage() -> Coverage:
    return Coverage(
        site_id="ng-lag-agbara-01",
        camera_id="cam-11",
        state=CameraState.OFFLINE,
        start_ts=T0,
        end_ts=T0 + timedelta(hours=2),
        reason="no frames from DVR channel 11",
    )


@pytest.fixture
def power_state() -> PowerState:
    return PowerState(
        site_id="ng-lag-agbara-01",
        state=PowerStateName.ON_BATTERY,
        battery_soc_pct=62.5,
        start_ts=T0,
    )


@pytest.fixture
def outbound_alert() -> OutboundMessage:
    return OutboundMessage(
        idempotency_key="ng-lag-agbara-01:alert:E-9001",
        kind=MessageKind.ALERT,
        priority=Priority.P0,
        site_id="ng-lag-agbara-01",
        recipient=OWNER,
        created_at=T0 + timedelta(seconds=12),
        occurred_at=T0,
        text="Agbara DC: Person in Yard (after hours) at 2:14 AM. Verified. [E-9001]",
        actions=[
            QuickAction(command=CommandName.CLIP, args=["E-9001"], label="Send clip"),
            QuickAction(command=CommandName.MUTE, args=["1H"]),
            QuickAction(command=CommandName.FALSE, args=["E-9001"], label="False alarm"),
        ],
        citations=["E-9001"],
        template_hint="alert_after_hours_v1",
    )


@pytest.fixture
def clip_message() -> OutboundMessage:
    return OutboundMessage(
        idempotency_key="ng-lag-agbara-01:clip:wamid-123",
        kind=MessageKind.CLIP,
        priority=Priority.P1,
        site_id="ng-lag-agbara-01",
        recipient=OWNER,
        created_at=T0 + timedelta(minutes=3),
        in_reply_to="wamid-123",
        text="Clip for E-9001 (20 s, watermarked).",
        media=ClipRef(
            object_key="clips/ng-lag-agbara-01/e-9001-a1b2.mp4",
            sha256="0" * 64,
            duration_s=20.0,
            size_bytes=1_450_000,
            request_id="wamid-123",
            requested_by=OWNER,
            source_event_id="E-9001",
            expires_at=T0 + timedelta(hours=24),
        ),
        citations=["E-9001"],
    )


@pytest.fixture
def inbound_event() -> InboundEvent:
    return InboundEvent(
        channel=Channel.WHATSAPP,
        message_id="wamid-123",
        sender_address="+2348012345678",
        text="was anyone in the stockroom after closing?",
        received_at=T0,
    )


@pytest.fixture
def inbox_message() -> InboxMessage:
    return InboxMessage(
        message_id="wamid-123",
        site_id="ng-lag-agbara-01",
        user=OWNER,
        role=Role.OWNER,
        channel=Channel.WHATSAPP,
        text="was anyone in the stockroom after closing?",
        received_at=T0,
    )


def _square(x: float, y: float, size: float = 0.2) -> list[Point]:
    return [Point(x=x, y=y), Point(x=x + size, y=y), Point(x=x + size, y=y + size)]


@pytest.fixture
def site_config() -> SiteConfig:
    return SiteConfig(
        site_id="ng-lag-agbara-01",
        tenant_id="t-agbara-foods",
        name="Agbara DC",
        country="NG",
        timezone="Africa/Lagos",
        data_region="africa",
        config_version=3,
        llm_mode=LlmMode.HYBRID,
        policy_pack="ng-ndpa@1.0.0",
        rule_pack="warehouse-v1@1.0.0",
        cameras=[
            CameraConfig(camera_id="cam-01", name="Gate Cam 1"),
            CameraConfig(camera_id="cam-02", name="Bay Cam 2"),
            CameraConfig(camera_id="cam-07", name="Yard Cam"),
        ],
        zones=[
            ZoneConfig(
                zone_id="yard",
                name="Yard",
                camera_id="cam-07",
                polygon=_square(0.1, 0.1),
                template="yard",
            ),
            ZoneConfig(
                zone_id="bay_2",
                name="Loading Bay 2",
                camera_id="cam-02",
                polygon=_square(0.3, 0.3),
                template="loading_bay",
                group="loading_bay",
            ),
        ],
        tripwires=[],
        schedule=Schedule(
            opening_hours=[
                OpeningWindow(
                    days=[Weekday.MON, Weekday.TUE, Weekday.WED, Weekday.THU, Weekday.FRI],
                    open=time(7, 0),
                    close=time(19, 0),
                )
            ],
            shifts=[
                Shift(name="day", start=time(7, 0), end=time(19, 0)),
                Shift(name="night", start=time(19, 0), end=time(7, 0)),
            ],
            armed_zone_ids=["bay_2"],
            always_armed_zone_ids=["yard"],
            holidays=[date(2026, 12, 25)],
        ),
        recipients=[Recipient(user=OWNER, role=Role.OWNER)],
    )


@pytest.fixture
def rule_pack() -> RulePack:
    return RulePack(
        id="warehouse-v1",
        version="1.0.0",
        description="Warehouses and distribution yards.",
        zone_templates=[
            ZoneTemplate(template="yard", default_name="Yard"),
            ZoneTemplate(
                template="loading_bay", default_name="Loading Bay", default_group="loading_bay"
            ),
        ],
        alert_types=[
            AlertType(
                name="after_hours_person",
                category=AlertCategory.SECURITY,
                severity=Severity.HIGH,
                deliver=True,
                verify_with_vlm=True,
                vlm_prompt="Is there a person in the marked area? Answer Yes or No, then why.",
                unverified_policy=UnverifiedPolicy.SEND_AS_UNVERIFIED,
            ),
            AlertType(
                name="truck_arrival",
                category=AlertCategory.LOGISTICS,
                severity=Severity.INFO,
                deliver=False,
                verify_with_vlm=False,
            ),
            AlertType(
                name="camera_offline",
                category=AlertCategory.CAMERA_HEALTH,
                severity=Severity.NORMAL,
                deliver=True,
                verify_with_vlm=False,
            ),
        ],
        rules=[
            Rule(
                name="person_in_armed_zone",
                trigger=Trigger.ROI_ENTER,
                object_classes=[ObjectClass.PERSON],
                when=ArmCondition.ARMED,
                emits="after_hours_person",
            ),
            Rule(
                name="truck_at_bay",
                trigger=Trigger.ROI_ENTER,
                object_classes=[ObjectClass.TRUCK],
                zone_templates=["loading_bay"],
                when=ArmCondition.ALWAYS,
                emits="truck_arrival",
            ),
            Rule(
                name="camera_down",
                trigger=Trigger.CAMERA_OFFLINE,
                when=ArmCondition.ALWAYS,
                emits="camera_offline",
            ),
        ],
    )


@pytest.fixture
def policy_pack() -> PolicyPack:
    raw = yaml.safe_load((FIXTURES / "ng-ndpa.yaml").read_text(encoding="utf-8"))
    return PolicyPack.model_validate(raw)
