from dataclasses import dataclass
from datetime import datetime
from threading import RLock

from .models import CommunicationAuthority, QueryContext, QueryScopedHandle


@dataclass
class Reservation:
    reservation_id: str
    authority_id: str
    transaction_id: str
    status: str = "PENDING"


class ProtectedStateStore:
    """Thread-safe reference state. Production systems need durable consensus/transaction semantics."""
    def __init__(self):
        self._lock = RLock()
        self.contexts: dict[str, QueryContext] = {}
        self.handles: dict[str, QueryScopedHandle] = {}
        self.revocation_epochs: dict[str, int] = {}
        self.policy_epochs: dict[str, int] = {}
        self.selected: set[tuple[str, str, str]] = set()
        self.commercial: set[tuple[str, str, str]] = set()
        self.authority_quota: dict[str, int] = {}
        self.authority_nonces: dict[str, str] = {}
        self.transactions: dict[tuple[str, str], str] = {}
        self.reservations: dict[str, Reservation] = {}
        self._reservation_counter = 0

    def register_context(self, context: QueryContext, revocation_epoch=0, policy_epoch=0):
        with self._lock:
            self.contexts[context.query_context_id] = context
            self.revocation_epochs[context.query_context_id] = revocation_epoch
            self.policy_epochs[context.query_context_id] = policy_epoch

    def register_handle(self, handle: QueryScopedHandle):
        with self._lock: self.handles[handle.handle_id] = handle

    def register_authority(self, authority: CommunicationAuthority):
        with self._lock:
            if authority.authority_id in self.authority_quota: raise ValueError("authority already registered")
            self.authority_quota[authority.authority_id] = authority.quota
            self.authority_nonces[authority.authority_id] = authority.nonce

    def set_selection(self, query: str, prop: str, business: str, enabled=True):
        with self._lock:
            key = (query, prop, business)
            self.selected.add(key) if enabled else self.selected.discard(key)

    def set_commercial(self, query: str, prop: str, business: str, enabled=True):
        with self._lock:
            key = (query, prop, business)
            self.commercial.add(key) if enabled else self.commercial.discard(key)

    def set_epochs(self, query: str, revocation: int | None = None, policy: int | None = None):
        if revocation is not None and revocation < 0 or policy is not None and policy < 0: raise ValueError("epochs must not be negative")
        with self._lock:
            if revocation is not None: self.revocation_epochs[query] = revocation
            if policy is not None: self.policy_epochs[query] = policy

    def inspect(self, authority: CommunicationAuthority, now: datetime) -> str:
        with self._lock:
            context = self.contexts.get(authority.query_context_id)
            if context is None: return "QUERY_UNKNOWN"
            if not (context.valid_from <= now < context.valid_until): return "QUERY_INACTIVE"
            handle = self.handles.get(authority.handle_id)
            if handle is None: return "HANDLE_UNKNOWN"
            if handle.expires_at <= now: return "HANDLE_EXPIRED"
            if handle.query_context_id != authority.query_context_id or handle.user_binding != authority.user_binding: return "HANDLE_CONTEXT_MISMATCH"
            if self.revocation_epochs.get(authority.query_context_id) is None: return "REVOCATION_STATE_UNAVAILABLE"
            if self.policy_epochs.get(authority.query_context_id) is None: return "POLICY_STATE_UNAVAILABLE"
            if self.revocation_epochs[authority.query_context_id] != authority.revocation_epoch: return "REVOKED_OR_STALE"
            if self.policy_epochs[authority.query_context_id] != authority.policy_epoch: return "POLICY_STALE"
            key = (authority.query_context_id, authority.property_id, authority.business_identity)
            if authority.selection_required and key not in self.selected: return "SELECTION_REQUIRED"
            if authority.commercial_required and key not in self.commercial: return "COMMERCIAL_STATE_REQUIRED"
            if self.authority_nonces.get(authority.authority_id) != authority.nonce: return "NONCE_INVALID"
            return "OK"

    def reserve(self, authority_id: str, transaction_id: str) -> tuple[str, str, bool]:
        with self._lock:
            key = (authority_id, transaction_id)
            if key in self.transactions:
                rid = self.transactions[key]; record = self.reservations[rid]
                if record.status == "POISONED": return "UNCERTAIN_OUTCOME", rid, True
                if record.status == "RELEASED": return "RESERVATION_RELEASED", rid, True
                return "OK", rid, True
            if self.authority_quota.get(authority_id, 0) <= 0: return "QUOTA_EXHAUSTED", "", False
            self.authority_quota[authority_id] -= 1; self._reservation_counter += 1
            rid = f"reservation-{self._reservation_counter}"
            self.transactions[key] = rid; self.reservations[rid] = Reservation(rid, authority_id, transaction_id)
            return "OK", rid, False

    def commit(self, reservation_id: str) -> tuple[str, bool]:
        with self._lock:
            record = self.reservations.get(reservation_id)
            if record is None: return "RESERVATION_UNKNOWN", False
            if record.status == "POISONED": return "UNCERTAIN_OUTCOME", False
            if record.status == "RELEASED": return "RESERVATION_RELEASED", False
            if record.status == "COMMITTED": return "OK", True
            record.status = "COMMITTED"; return "OK", False

    def rollback(self, reservation_id: str) -> str:
        with self._lock:
            record = self.reservations.get(reservation_id)
            if record is None: return "RESERVATION_UNKNOWN"
            if record.status != "PENDING": return "RESERVATION_NOT_PENDING"
            record.status = "RELEASED"; self.authority_quota[record.authority_id] += 1
            return "OK"

    def poison(self, reservation_id: str) -> str:
        with self._lock:
            record = self.reservations.get(reservation_id)
            if record is None: return "RESERVATION_UNKNOWN"
            if record.status == "RELEASED": return "RESERVATION_RELEASED"
            record.status = "POISONED"; return "OK"
