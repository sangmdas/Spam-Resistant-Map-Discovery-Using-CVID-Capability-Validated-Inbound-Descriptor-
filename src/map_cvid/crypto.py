import hashlib
import hmac
import json
from dataclasses import replace
from datetime import datetime
from enum import Enum
from typing import Any, TypeVar

T = TypeVar("T")


def canonical(value: Any) -> bytes:
    def default(obj):
        if isinstance(obj, datetime): return obj.isoformat().replace("+00:00", "Z")
        if isinstance(obj, Enum): return obj.value
        raise TypeError(type(obj).__name__)
    return json.dumps(value, sort_keys=True, separators=(",", ":"), default=default).encode()


class HMACSigner:
    """Deterministic integrity adapter for the prototype; use managed keys/HSMs in production."""
    def __init__(self, key: bytes):
        if len(key) < 32: raise ValueError("prototype signing key must be at least 32 bytes")
        self._key = key

    def sign(self, obj: T) -> T:
        signature = hmac.new(self._key, canonical(obj.unsigned_dict()), hashlib.sha256).hexdigest()
        return replace(obj, signature=signature)

    def verify(self, obj) -> bool:
        expected = hmac.new(self._key, canonical(obj.unsigned_dict()), hashlib.sha256).hexdigest()
        return bool(obj.signature) and hmac.compare_digest(expected, obj.signature)
