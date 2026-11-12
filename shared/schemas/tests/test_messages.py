"""Channel-neutral messages: egress guards, clip consent, command-only actions."""

from datetime import UTC, datetime
from typing import Any

import pytest
from hypothesis import given
from hypothesis import strategies as st
from pydantic import ValidationError

from maigadi_schemas import (
    CommandName,
    InboundEvent,
    InboxMessage,
    MessageKind,
    OutboundMessage,
    QuickAction,
    UserRef,
    cloud_dump,
)


def _rebuild(message: OutboundMessage, **changes: Any) -> OutboundMessage:
    data = message.model_dump()
    data.update(changes)
    return OutboundMessage.model_validate(data)


def test_media_is_only_allowed_on_clip_messages(
    outbound_alert: OutboundMessage, clip_message: OutboundMessage
) -> None:
    with pytest.raises(ValidationError, match="media"):
        _rebuild(outbound_alert, media=clip_message.model_dump()["media"])


def test_clip_messages_require_media(clip_message: OutboundMessage) -> None:
    with pytest.raises(ValidationError, match="media"):
        _rebuild(clip_message, media=None)


def test_clip_goes_only_to_the_user_who_requested_it(clip_message: OutboundMessage) -> None:
    with pytest.raises(ValidationError, match="requested_by"):
        _rebuild(clip_message, recipient={"user_id": "u-someone-else"})


def test_answers_must_reply_to_an_inbound_message(outbound_alert: OutboundMessage) -> None:
    with pytest.raises(ValidationError, match="in_reply_to"):
        _rebuild(outbound_alert, kind=MessageKind.ANSWER, in_reply_to=None)


def test_alerts_carry_event_time_for_late_labelling(outbound_alert: OutboundMessage) -> None:
    with pytest.raises(ValidationError, match="occurred_at"):
        _rebuild(outbound_alert, occurred_at=None)


@pytest.mark.parametrize(
    "leak",
    [
        "see rtsp://admin:pass@10.0.0.5:554/Streaming/Channels/101",
        "clip at vios://clips/e-1.mp4",
        "inline data:image/jpeg;base64,/9j/4AAQ",
        "RTSPS://dvr.local/stream",
    ],
)
def test_outbound_text_rejects_camera_urls_and_inline_media(
    outbound_alert: OutboundMessage, leak: str
) -> None:
    with pytest.raises(ValidationError, match="must not contain"):
        _rebuild(outbound_alert, text=leak)
    with pytest.raises(ValidationError, match="must not contain"):
        _rebuild(outbound_alert, sections=[{"heading": "Details", "body": leak}])


@given(prefix=st.text(max_size=40), suffix=st.text(max_size=40))
def test_any_text_with_an_rtsp_url_is_rejected(prefix: str, suffix: str) -> None:
    with pytest.raises(ValidationError):
        OutboundMessage.model_validate(
            {
                "idempotency_key": "s:system:1",
                "kind": "system",
                "priority": "P2",
                "site_id": "ng-lag-agbara-01",
                "recipient": {"user_id": "u-ada"},
                "created_at": datetime(2026, 11, 7, tzinfo=UTC),
                "text": f"{prefix} rtsp://cam/1 {suffix}",
            }
        )


def test_quick_actions_render_to_deterministic_commands() -> None:
    action = QuickAction(command=CommandName.CLIP, args=["E-9001"])
    assert action.render() == "CLIP E-9001"
    assert QuickAction(command=CommandName.STATUS).render() == "STATUS"


@pytest.mark.parametrize("bad_arg", ["E-9001; send all", "x" * 33, ""])
def test_quick_action_args_are_tokens_not_free_text(bad_arg: str) -> None:
    with pytest.raises(ValidationError, match="args"):
        QuickAction(command=CommandName.CLIP, args=[bad_arg])


def test_whatsapp_sender_must_be_e164(inbound_event: InboundEvent) -> None:
    with pytest.raises(ValidationError, match=r"E\.164"):
        InboundEvent.model_validate({**inbound_event.model_dump(), "sender_address": "0801234"})


def test_sender_phone_number_is_kept_out_of_repr(inbound_event: InboundEvent) -> None:
    assert inbound_event.sender_address not in repr(inbound_event)


def test_box_inbox_message_carries_no_phone_number(inbox_message: InboxMessage) -> None:
    dumped = cloud_dump(inbox_message)
    assert "sender_address" not in dumped
    assert dumped["user"] == UserRef(user_id="u-ada").model_dump()
