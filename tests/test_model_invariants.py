import unittest
from dataclasses import FrozenInstanceError, replace
from datetime import datetime, timedelta
from fixtures import NOW, attempt, world
from map_cvid import (AttemptDescriptor, AuthorityPhase, Channel, CommunicationAuthority,
                      Direction, Effect, QueryContext, QueryScopedHandle)


class ModelInvariantTests(unittest.TestCase):
    def test_query_requires_listing(self):
        with self.assertRaises(ValueError): QueryContext("q", "i", "u", (), NOW, NOW + timedelta(seconds=1))

    def test_query_rejects_empty_listing(self):
        with self.assertRaises(ValueError): QueryContext("q", "i", "u", ("",), NOW, NOW + timedelta(seconds=1))

    def test_query_rejects_equal_time_bounds(self):
        with self.assertRaises(ValueError): QueryContext("q", "i", "u", ("p",), NOW, NOW)

    def test_query_rejects_reversed_time_bounds(self):
        with self.assertRaises(ValueError): QueryContext("q", "i", "u", ("p",), NOW, NOW - timedelta(seconds=1))

    def test_query_rejects_naive_time(self):
        with self.assertRaises(ValueError): QueryContext("q", "i", "u", ("p",), datetime(2026, 1, 1), NOW)

    def test_handle_rejects_naive_expiry(self):
        with self.assertRaises(ValueError): QueryScopedHandle("h", "q", "u", "map", datetime(2026, 1, 1))

    def test_handle_rejects_empty_platform(self):
        with self.assertRaises(ValueError): QueryScopedHandle("h", "q", "u", "", NOW)

    def test_authority_rejects_zero_quota(self):
        *_, authority, _, _ = world()
        with self.assertRaises(ValueError): replace(authority, quota=0)

    def test_authority_rejects_negative_quota(self):
        *_, authority, _, _ = world()
        with self.assertRaises(ValueError): replace(authority, quota=-1)

    def test_authority_rejects_negative_revocation_epoch(self):
        *_, authority, _, _ = world()
        with self.assertRaises(ValueError): replace(authority, revocation_epoch=-1)

    def test_authority_rejects_negative_policy_epoch(self):
        *_, authority, _, _ = world()
        with self.assertRaises(ValueError): replace(authority, policy_epoch=-1)

    def test_authority_rejects_requester_outside_actor_set(self):
        *_, authority, _, _ = world()
        with self.assertRaises(ValueError): replace(authority, authorized_actor_ids=("actor:other",))

    def test_authority_rejects_empty_actor_set(self):
        *_, authority, _, _ = world()
        with self.assertRaises(ValueError): replace(authority, authorized_actor_ids=())

    def test_authority_rejects_equal_validity_bounds(self):
        *_, authority, _, _ = world()
        with self.assertRaises(ValueError): replace(authority, validity_end=authority.validity_start)

    def test_authority_is_immutable(self):
        *_, authority, _, _ = world()
        with self.assertRaises(FrozenInstanceError): authority.purpose = "marketing"

    def test_attempt_is_immutable(self):
        *_, authority, _, _ = world(); value = attempt(authority)
        with self.assertRaises(FrozenInstanceError): value.observed_handle = "other"

    def test_attempt_rejects_empty_transaction(self):
        *_, authority, _, _ = world()
        with self.assertRaises(ValueError): attempt(authority, transaction_id="")

    def test_attempt_rejects_empty_purpose(self):
        *_, authority, _, _ = world()
        with self.assertRaises(ValueError): attempt(authority, observed_purpose="")

    def test_unsigned_dict_excludes_signature(self):
        *_, authority, _, _ = world()
        self.assertNotIn("signature", authority.unsigned_dict())

    def test_region_is_not_required_for_authority_binding(self):
        _, _, service, context, *_ = world()
        self.assertEqual("region:opaque", context.region); self.assertNotIn("region", service.state.authority_nonces)

if __name__ == "__main__": unittest.main()
