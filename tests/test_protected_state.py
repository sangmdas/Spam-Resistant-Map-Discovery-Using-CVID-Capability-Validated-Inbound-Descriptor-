import unittest
from dataclasses import replace
from datetime import timedelta
from fixtures import NOW, attempt, resign, world


class ProtectedStateTests(unittest.TestCase):
    def evaluate(self, mutate):
        state, signer, _, _, _, authority, enforcement, _ = world(); mutate(state, signer, authority)
        return enforcement.evaluate(authority, attempt(authority), NOW)

    def test_unknown_query_is_denied(self):
        self.assertEqual("QUERY_UNKNOWN", self.evaluate(lambda s, _k, a: s.contexts.pop(a.query_context_id)).code)

    def test_query_before_start_is_denied(self):
        state, signer, _, context, _, authority, enforcement, _ = world()
        state.contexts[context.query_context_id] = replace(context, valid_from=NOW + timedelta(seconds=1), valid_until=NOW + timedelta(hours=1))
        self.assertEqual("QUERY_INACTIVE", enforcement.evaluate(authority, attempt(authority), NOW).code)

    def test_query_at_end_is_denied(self):
        state, _, _, context, _, authority, enforcement, _ = world()
        state.contexts[context.query_context_id] = replace(context, valid_until=NOW)
        self.assertEqual("QUERY_INACTIVE", enforcement.evaluate(authority, attempt(authority), NOW).code)

    def test_unknown_handle_is_denied(self):
        self.assertEqual("HANDLE_UNKNOWN", self.evaluate(lambda s, _k, a: s.handles.pop(a.handle_id)).code)

    def test_expired_handle_is_denied(self):
        def mutate(s, _k, a): s.handles[a.handle_id] = replace(s.handles[a.handle_id], expires_at=NOW)
        self.assertEqual("HANDLE_EXPIRED", self.evaluate(mutate).code)

    def test_handle_query_substitution_is_denied(self):
        def mutate(s, _k, a): s.handles[a.handle_id] = replace(s.handles[a.handle_id], query_context_id="query:other")
        self.assertEqual("HANDLE_CONTEXT_MISMATCH", self.evaluate(mutate).code)

    def test_handle_user_substitution_is_denied(self):
        def mutate(s, _k, a): s.handles[a.handle_id] = replace(s.handles[a.handle_id], user_binding="user:other")
        self.assertEqual("HANDLE_CONTEXT_MISMATCH", self.evaluate(mutate).code)

    def test_missing_revocation_state_fails_closed(self):
        self.assertEqual("REVOCATION_STATE_UNAVAILABLE", self.evaluate(lambda s, _k, a: s.revocation_epochs.pop(a.query_context_id)).code)

    def test_missing_policy_state_fails_closed(self):
        self.assertEqual("POLICY_STATE_UNAVAILABLE", self.evaluate(lambda s, _k, a: s.policy_epochs.pop(a.query_context_id)).code)

    def test_revocation_epoch_increment_denies(self):
        self.assertEqual("REVOKED_OR_STALE", self.evaluate(lambda s, _k, a: s.set_epochs(a.query_context_id, revocation=a.revocation_epoch + 1)).code)

    def test_revocation_epoch_rollback_denies(self):
        state, signer, _, _, _, authority, enforcement, _ = world(); authority = resign(authority, signer, revocation_epoch=2)
        self.assertEqual("REVOKED_OR_STALE", enforcement.evaluate(authority, attempt(authority), NOW).code)

    def test_policy_epoch_increment_denies(self):
        self.assertEqual("POLICY_STALE", self.evaluate(lambda s, _k, a: s.set_epochs(a.query_context_id, policy=a.policy_epoch + 1)).code)

    def test_selection_withdrawal_denies_future_authority(self):
        state, _, _, _, _, authority, enforcement, _ = world(preview=False)
        state.set_selection(authority.query_context_id, authority.property_id, authority.business_identity, False)
        self.assertEqual("SELECTION_REQUIRED", enforcement.evaluate(authority, attempt(authority), NOW).code)

    def test_commercial_state_withdrawal_denies_future_authority(self):
        state, _, _, _, _, authority, enforcement, _ = world(preview=False)
        state.set_commercial(authority.query_context_id, authority.property_id, authority.business_identity, False)
        self.assertEqual("COMMERCIAL_STATE_REQUIRED", enforcement.evaluate(authority, attempt(authority), NOW).code)

    def test_nonce_state_change_denies(self):
        self.assertEqual("NONCE_INVALID", self.evaluate(lambda s, _k, a: s.authority_nonces.__setitem__(a.authority_id, "nonce:new")).code)

if __name__ == "__main__": unittest.main()
