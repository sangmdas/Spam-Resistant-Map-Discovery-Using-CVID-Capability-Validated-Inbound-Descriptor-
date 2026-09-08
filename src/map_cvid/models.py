from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any


class AuthorityPhase(str, Enum): PREVIEW = "PREVIEW"; FUTURE = "FUTURE"
class Direction(str, Enum): USER_TO_BUSINESS = "USER_TO_BUSINESS"; BUSINESS_TO_USER = "BUSINESS_TO_USER"
class Channel(str, Enum): VOICE = "voice"; MESSAGE = "message"; WEBRTC = "webrtc"; NOTIFICATION = "notification"
class Effect(str, Enum): PREVIEW_CALL = "PREVIEW_CALL"; PREVIEW_MESSAGE = "PREVIEW_MESSAGE"; FUTURE_CONTACT = "FUTURE_CONTACT"; CALLBACK = "CALLBACK"


def aware(value: datetime, name: str) -> datetime:
    if value.tzinfo is None: raise ValueError(f"{name} must be timezone-aware")
    return value.astimezone(timezone.utc)


def required(**values: str) -> None:
    for name, value in values.items():
        if not isinstance(value, str) or not value.strip(): raise ValueError(f"{name} must be non-empty")


@dataclass(frozen=True)
class QueryContext:
    query_context_id: str
    inquiry_id: str
    user_binding: str
    listing_ids: tuple[str, ...]
    valid_from: datetime
    valid_until: datetime
    region: str = ""

    def __post_init__(self):
        required(query_context_id=self.query_context_id, inquiry_id=self.inquiry_id, user_binding=self.user_binding)
        if not self.listing_ids or any(not x.strip() for x in self.listing_ids): raise ValueError("listing_ids must be non-empty")
        object.__setattr__(self, "valid_from", aware(self.valid_from, "valid_from")); object.__setattr__(self, "valid_until", aware(self.valid_until, "valid_until"))
        if self.valid_until <= self.valid_from: raise ValueError("query validity window is invalid")


@dataclass(frozen=True)
class QueryScopedHandle:
    handle_id: str
    query_context_id: str
    user_binding: str
    platform_id: str
    expires_at: datetime

    def __post_init__(self):
        required(handle_id=self.handle_id, query_context_id=self.query_context_id, user_binding=self.user_binding, platform_id=self.platform_id)
        object.__setattr__(self, "expires_at", aware(self.expires_at, "expires_at"))


@dataclass(frozen=True)
class CommunicationAuthority:
    authority_id: str
    inquiry_id: str
    query_context_id: str
    user_binding: str
    handle_id: str
    requesting_actor_id: str
    business_identity: str
    authorized_actor_ids: tuple[str, ...]
    property_id: str
    phase: AuthorityPhase
    direction: Direction
    channel: Channel
    purpose: str
    permitted_effect: Effect
    validity_start: datetime
    validity_end: datetime
    nonce: str
    quota: int
    revocation_epoch: int
    policy_epoch: int
    enforcement_point_id: str
    commercial_required: bool = False
    selection_required: bool = False
    device_binding: str = ""
    signature: str = field(default="", compare=False)

    def __post_init__(self):
        required(authority_id=self.authority_id, inquiry_id=self.inquiry_id, query_context_id=self.query_context_id,
                 user_binding=self.user_binding, handle_id=self.handle_id, requesting_actor_id=self.requesting_actor_id,
                 business_identity=self.business_identity, property_id=self.property_id, purpose=self.purpose,
                 nonce=self.nonce, enforcement_point_id=self.enforcement_point_id)
        if not self.authorized_actor_ids or any(not x.strip() for x in self.authorized_actor_ids): raise ValueError("authorized_actor_ids must be non-empty")
        object.__setattr__(self, "validity_start", aware(self.validity_start, "validity_start")); object.__setattr__(self, "validity_end", aware(self.validity_end, "validity_end"))
        if self.validity_end <= self.validity_start: raise ValueError("authority validity window is invalid")
        if self.quota < 1: raise ValueError("quota must be positive")
        if self.revocation_epoch < 0 or self.policy_epoch < 0: raise ValueError("epochs must not be negative")
        if self.requesting_actor_id not in self.authorized_actor_ids: raise ValueError("requesting actor must be within authorized actors")
        if self.phase == AuthorityPhase.PREVIEW and self.permitted_effect not in (Effect.PREVIEW_CALL, Effect.PREVIEW_MESSAGE): raise ValueError("preview authority cannot grant future effect")
        if self.phase == AuthorityPhase.FUTURE and self.permitted_effect in (Effect.PREVIEW_CALL, Effect.PREVIEW_MESSAGE): raise ValueError("future authority cannot grant preview effect")

    def unsigned_dict(self) -> dict[str, Any]:
        value = asdict(self); value.pop("signature", None); return value


@dataclass(frozen=True)
class AttemptDescriptor:
    transaction_id: str
    authority_id: str
    observed_query_context: str
    observed_inquiry_id: str
    observed_business_identity: str
    observed_actor_id: str
    observed_user_binding: str
    observed_property_id: str
    observed_handle: str
    observed_phase: AuthorityPhase
    observed_direction: Direction
    observed_channel: Channel
    observed_purpose: str
    observed_effect: Effect
    observed_nonce: str
    observed_enforcement_point: str
    observed_device_binding: str = ""

    def __post_init__(self):
        for name, value in asdict(self).items():
            if name != "observed_device_binding" and isinstance(value, str) and not value.strip(): raise ValueError(f"{name} must be non-empty")


@dataclass(frozen=True)
class Decision:
    allowed: bool
    code: str
    reservation_id: str = ""
    capability: "BoundedReleaseCapability | None" = None
    idempotent: bool = False


@dataclass(frozen=True)
class BoundedReleaseCapability:
    capability_id: str
    authority_id: str
    transaction_id: str
    reservation_id: str
    actor_id: str
    resource_id: str
    effect: Effect
    enforcement_point_id: str
    expires_at: datetime
    signature: str = field(default="", compare=False)

    def __post_init__(self):
        required(capability_id=self.capability_id, authority_id=self.authority_id, transaction_id=self.transaction_id,
                 reservation_id=self.reservation_id, actor_id=self.actor_id, resource_id=self.resource_id,
                 enforcement_point_id=self.enforcement_point_id)
        object.__setattr__(self, "expires_at", aware(self.expires_at, "expires_at"))

    def unsigned_dict(self) -> dict[str, Any]:
        value = asdict(self); value.pop("signature", None); return value
