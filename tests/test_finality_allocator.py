import unittest
from dataclasses import replace
from datetime import timedelta
from fixtures import NOW, attempt, world
from map_cvid import HMACSigner, ResourceAllocator


class FinalityAllocatorTests(unittest.TestCase):
    def decision(self):
        state, signer, _, _, _, authority, enforcement, allocator = world()
        return state, signer, authority, allocator, enforcement.evaluate(authority, attempt(authority), NOW)

    def test_no_capability_means_no_effect(self):
        *_, allocator, _ = self.decision()
        self.assertEqual("CAPABILITY_REQUIRED", allocator.allocate(None, "actor:D1", "resource:x", NOW).code); self.assertEqual({}, allocator.effects)

    def test_valid_capability_allocates_bounded_resource(self):
        _, _, authority, allocator, decision = self.decision()
        result = allocator.allocate(decision.capability, authority.requesting_actor_id, decision.capability.resource_id, NOW)
        self.assertTrue(result.allowed); self.assertIn(decision.capability.transaction_id, allocator.effects)

    def test_unsigned_capability_is_denied(self):
        _, _, authority, allocator, decision = self.decision(); cap = replace(decision.capability, signature="")
        self.assertEqual("CAPABILITY_INTEGRITY_INVALID", allocator.allocate(cap, authority.requesting_actor_id, cap.resource_id, NOW).code)

    def test_tampered_capability_is_denied(self):
        _, _, authority, allocator, decision = self.decision(); cap = replace(decision.capability, resource_id="resource:other")
        self.assertEqual("CAPABILITY_INTEGRITY_INVALID", allocator.allocate(cap, authority.requesting_actor_id, cap.resource_id, NOW).code)

    def test_capability_signed_by_wrong_key_is_denied(self):
        _, _, authority, allocator, decision = self.decision()
        wrong = HMACSigner(b"different-reference-test-key-32-bytes-long").sign(replace(decision.capability, signature=""))
        self.assertFalse(allocator.allocate(wrong, authority.requesting_actor_id, wrong.resource_id, NOW).allowed)

    def test_capability_actor_substitution_is_denied(self):
        _, _, _, allocator, decision = self.decision()
        self.assertEqual("CAPABILITY_ACTOR_MISMATCH", allocator.allocate(decision.capability, "actor:attacker", decision.capability.resource_id, NOW).code)

    def test_capability_resource_widening_is_denied(self):
        _, _, authority, allocator, decision = self.decision()
        self.assertEqual("CAPABILITY_RESOURCE_MISMATCH", allocator.allocate(decision.capability, authority.requesting_actor_id, "resource:unlimited", NOW).code)

    def test_capability_wrong_enforcement_point_is_denied(self):
        state, signer, authority, _, decision = self.decision(); other = ResourceAllocator("edge:east", signer, state)
        self.assertEqual("CAPABILITY_AUDIENCE_MISMATCH", other.allocate(decision.capability, authority.requesting_actor_id, decision.capability.resource_id, NOW).code)

    def test_capability_at_expiry_is_denied(self):
        _, _, authority, allocator, decision = self.decision()
        self.assertEqual("CAPABILITY_EXPIRED", allocator.allocate(decision.capability, authority.requesting_actor_id, decision.capability.resource_id, decision.capability.expires_at).code)

    def test_capability_just_before_expiry_is_allowed(self):
        _, _, authority, allocator, decision = self.decision()
        self.assertTrue(allocator.allocate(decision.capability, authority.requesting_actor_id, decision.capability.resource_id, decision.capability.expires_at - timedelta(microseconds=1)).allowed)

    def test_allocator_is_idempotent_for_same_transaction_and_resource(self):
        _, _, authority, allocator, decision = self.decision()
        first = allocator.allocate(decision.capability, authority.requesting_actor_id, decision.capability.resource_id, NOW)
        second = allocator.allocate(decision.capability, authority.requesting_actor_id, decision.capability.resource_id, NOW)
        self.assertTrue(first.allowed and second.allowed); self.assertTrue(second.idempotent)

    def test_poisoned_reservation_cannot_allocate(self):
        state, _, authority, allocator, decision = self.decision(); state.poison(decision.reservation_id)
        self.assertEqual("UNCERTAIN_OUTCOME", allocator.allocate(decision.capability, authority.requesting_actor_id, decision.capability.resource_id, NOW).code)

    def test_released_reservation_cannot_allocate(self):
        state, _, authority, allocator, decision = self.decision(); state.rollback(decision.reservation_id)
        self.assertEqual("RESERVATION_RELEASED", allocator.allocate(decision.capability, authority.requesting_actor_id, decision.capability.resource_id, NOW).code)

    def test_naive_allocation_time_is_rejected(self):
        _, _, authority, allocator, decision = self.decision()
        with self.assertRaises(ValueError): allocator.allocate(decision.capability, authority.requesting_actor_id, decision.capability.resource_id, NOW.replace(tzinfo=None))

if __name__ == "__main__": unittest.main()
