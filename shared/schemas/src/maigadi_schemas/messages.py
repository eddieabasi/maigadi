"""Channel-neutral messages (spec/ARCHITECTURE.md §7.1, §8).

- ``OutboundMessage``: box → cloud → user, for any channel.
- ``InboundEvent``: what a channel adapter parses from a webhook. Cloud-only;
  it holds the sender's phone number.
- ``InboxMessage``: what the box receives on ``down/inbox``. It holds the
  resolved user and role, never the phone number.
"""

import re
from datetime import timedelta
from enum import StrEnum
from typing import Annotated, Self

from pydantic import Field, PositiveInt, StringConstraints, model_validator

from maigadi_schemas._base import CloudText, Identifier, Model, UtcDateTime
from maigadi_schemas.common import CaptionId, EventId, Priority, Role, SiteId, UserId

CLIP_MAX_CLOUD_LIFETIME = timedelta(hours=24)
"""Transient cloud copies of clips are deleted within 24 h (spec/SECURITY_AND_PRIVACY.md §B3)."""

IdempotencyKey = Annotated[str, StringConstraints(pattern=r"^[!-~]{1,200}$")]
ChannelMessageId = Annotated[str, StringConstraints(min_length=1, max_length=256)]
CommandArg = Annotated[str, StringConstraints(pattern=r"^[A-Za-z0-9:._-]{1,32}$")]

_E164 = re.compile(r"^\+[1-9][0-9]{6,14}$")


class MessageKind(StrEnum):
    ALERT = "alert"
    SUMMARY = "summary"
    ANSWER = "answer"
    SYSTEM = "system"
    CLIP = "clip"  # the only kind that may carry media


class Channel(StrEnum):
    WHATSAPP = "whatsapp"
    SMS = "sms"
    TELEGRAM = "telegram"
    SLACK = "slack"
    TEAMS = "teams"
    FAKE = "fake"  # tests and demos


PHONE_CHANNELS = frozenset({Channel.WHATSAPP, Channel.SMS})


class CommandName(StrEnum):
    """Deterministic, user-typed commands parsed by the relay, never by the LLM
    (spec/ARCHITECTURE.md §7.1)."""

    CLIP = "CLIP"
    MORE = "MORE"
    MUTE = "MUTE"
    FALSE = "FALSE"
    LATE = "LATE"
    STATUS = "STATUS"
    HELP = "HELP"
    STOP = "STOP"
    YES = "YES"
    ALLOW = "ALLOW"


class UserRef(Model):
    user_id: UserId


class QuickAction(Model):
    """A suggested reply. Actions are structured commands, never free text, so
    model output can't smuggle instructions into a button."""

    command: CommandName
    args: list[CommandArg] = Field(default_factory=list, max_length=4)
    label: CloudText | None = Field(default=None, min_length=1, max_length=20)

    def render(self) -> str:
        """The exact text the user sends back, e.g. ``CLIP E-9001``."""
        return " ".join([self.command.value, *self.args])


class MessageSection(Model):
    heading: CloudText | None = Field(default=None, max_length=100)
    body: CloudText = Field(min_length=1, max_length=4096)


class ClipRef(Model):
    """A clip uploaded to the transient cloud bucket after an explicit ``CLIP``
    request. ``request_id`` and ``requested_by`` tie it to that request."""

    object_key: str = Field(pattern=r"^clips/[A-Za-z0-9/_.=-]{1,240}$")
    sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    mime: str = Field(default="video/mp4", pattern=r"^video/mp4$")
    duration_s: float = Field(gt=0, le=60)
    size_bytes: PositiveInt = Field(le=16_000_000)
    request_id: ChannelMessageId
    requested_by: UserRef
    source_event_id: EventId | None = None
    expires_at: UtcDateTime


class OutboundMessage(Model):
    idempotency_key: IdempotencyKey
    kind: MessageKind
    priority: Priority
    site_id: SiteId
    recipient: UserRef
    created_at: UtcDateTime
    text: CloudText = Field(min_length=1, max_length=4096)
    sections: list[MessageSection] = Field(default_factory=list, max_length=20)
    media: ClipRef | None = None
    actions: list[QuickAction] = Field(default_factory=list, max_length=10)
    citations: list[EventId | CaptionId] = Field(default_factory=list, max_length=50)
    occurred_at: UtcDateTime | None = None
    in_reply_to: ChannelMessageId | None = None
    template_hint: Identifier | None = None

    @model_validator(mode="after")
    def _consistent(self) -> Self:
        if self.kind is MessageKind.CLIP:
            self._check_clip()
        elif self.media is not None:
            raise ValueError("media is only allowed on clip messages")
        if self.kind is MessageKind.ANSWER and self.in_reply_to is None:
            raise ValueError("answers need in_reply_to (the question's message id)")
        if self.kind is MessageKind.ALERT and self.occurred_at is None:
            raise ValueError("alerts need occurred_at so late delivery can be labelled")
        return self

    def _check_clip(self) -> None:
        clip = self.media
        if clip is None:
            raise ValueError("clip messages need media")
        if clip.requested_by != self.recipient:
            raise ValueError("clips go only to the user who requested them (requested_by)")
        if self.in_reply_to != clip.request_id:
            raise ValueError("clip messages must reply to the CLIP request (in_reply_to)")
        if clip.expires_at > self.created_at + CLIP_MAX_CLOUD_LIFETIME:
            raise ValueError("media expires_at must be within 24 h of created_at")


class InboundEvent(Model):
    """A message as parsed by a channel adapter. Cloud-only (holds PII)."""

    channel: Channel
    message_id: ChannelMessageId
    sender_address: str = Field(min_length=1, max_length=256, repr=False)
    text: str = Field(default="", max_length=4096)
    received_at: UtcDateTime
    reply_to_message_id: ChannelMessageId | None = None

    @model_validator(mode="after")
    def _sender(self) -> Self:
        if self.channel in PHONE_CHANNELS and not _E164.fullmatch(self.sender_address):
            raise ValueError("sender_address must be an E.164 phone number on this channel")
        return self


class InboxMessage(Model):
    """A user's message delivered to the box (MQTT ``down/inbox``). The relay
    has already resolved and authorised the sender."""

    message_id: ChannelMessageId
    site_id: SiteId
    user: UserRef
    role: Role
    channel: Channel
    text: str = Field(min_length=1, max_length=4096)
    received_at: UtcDateTime
    reply_to_message_id: ChannelMessageId | None = None
