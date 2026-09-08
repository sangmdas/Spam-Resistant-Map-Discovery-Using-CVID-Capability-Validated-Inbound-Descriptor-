import unittest
from concurrent.futures import ThreadPoolExecutor
from fixtures import NOW, attempt, world


class QuotaReplayConcurrencyTests(unittest.TestCase):
    def test_single_quota_denies_new_logical_replay(self):
        *_, authority, enforcement, _ = world(quota=1)
        self.assertTrue(enforcement.evaluate(authority, attempt(authority), NOW).allowed)
        self.assertEqual("QUOTA_EXHAUSTED", enforcement.evaluate(authority, attempt(authority, transaction_id="transaction-2"), NOW).code)

    def test_transport_retransmission_is_idempotent(self):
        *_, authority, enforcement, _ = world(quota=1)
        first = enforcement.evaluate(authority, attempt(authority), NOW); second = enforcement.evaluate(authority, attempt(authority), NOW)
        self.assertTrue(first.allowed and second.allowed); self.assertFalse(first.idempotent); self.assertTrue(second.idempotent)

    def test_three_quota_allows_exactly_three_acts(self):
        *_, authority, enforcement, _ = world(quota=3)
        results = [enforcement.evaluate(authority, attempt(authority, transaction_id=f"t-{i}"), NOW) for i in range(4)]
        self.assertEqual([True, True, True, False], [r.allowed for r in results])

    def test_fifty_way_race_cannot_double_consume(self):
        *_, authority, enforcement, _ = world(quota=1)
        with ThreadPoolExecutor(max_workers=20) as pool:
            results = list(pool.map(lambda i: enforcement.evaluate(authority, attempt(authority, transaction_id=f"race-{i}"), NOW), range(50)))
        self.assertEqual(1, sum(x.allowed for x in results)); self.assertEqual(49, sum(x.code == "QUOTA_EXHAUSTED" for x in results))

    def test_fifty_retransmissions_share_one_reservation(self):
        *_, authority, enforcement, _ = world(quota=1)
        with ThreadPoolExecutor(max_workers=20) as pool:
            results = list(pool.map(lambda _: enforcement.evaluate(authority, attempt(authority, transaction_id="same"), NOW), range(50)))
        self.assertTrue(all(x.allowed for x in results)); self.assertEqual(1, len({x.reservation_id for x in results}))

    def test_rollback_returns_quota_before_effect(self):
        state, *_, authority, enforcement, _ = world(quota=1)
        decision = enforcement.evaluate(authority, attempt(authority), NOW)
        self.assertEqual("OK", state.rollback(decision.reservation_id))
        self.assertTrue(enforcement.evaluate(authority, attempt(authority, transaction_id="new"), NOW).allowed)

    def test_committed_reservation_cannot_be_rolled_back(self):
        state, *_, authority, enforcement, allocator = world(quota=1)
        decision = enforcement.evaluate(authority, attempt(authority), NOW)
        allocator.allocate(decision.capability, authority.requesting_actor_id, decision.capability.resource_id, NOW)
        self.assertEqual("RESERVATION_NOT_PENDING", state.rollback(decision.reservation_id))

    def test_poisoned_uncertain_outcome_fails_closed(self):
        state, *_, authority, enforcement, _ = world(quota=1)
        decision = enforcement.evaluate(authority, attempt(authority), NOW); state.poison(decision.reservation_id)
        self.assertEqual("UNCERTAIN_OUTCOME", enforcement.evaluate(authority, attempt(authority), NOW).code)

    def test_released_same_transaction_is_not_silently_reused(self):
        state, *_, authority, enforcement, _ = world(quota=1)
        decision = enforcement.evaluate(authority, attempt(authority), NOW); state.rollback(decision.reservation_id)
        self.assertEqual("RESERVATION_RELEASED", enforcement.evaluate(authority, attempt(authority), NOW).code)

    def test_separate_authorities_have_separate_quota_domains(self):
        state, _, service, context, handle, a1, enforcement, _ = world(quota=1)
        a2 = service.issue_preview(context, handle, "business:D1", "actor:D1", "property:P1", now=NOW, quota=1)
        self.assertTrue(enforcement.evaluate(a1, attempt(a1, transaction_id="a1"), NOW).allowed)
        self.assertTrue(enforcement.evaluate(a2, attempt(a2, transaction_id="a2"), NOW).allowed)

if __name__ == "__main__": unittest.main()
