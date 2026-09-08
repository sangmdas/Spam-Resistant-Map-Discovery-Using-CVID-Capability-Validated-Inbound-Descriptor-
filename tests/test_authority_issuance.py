import unittest
from dataclasses import replace
from datetime import timedelta
from fixtures import NOW, world
from map_cvid import AuthorityPhase, Channel, Effect


class AuthorityIssuanceTests(unittest.TestCase):
    def test_preview_and_future_are_distinct_authorities(self):
        state, _, service, context, handle, preview, *_ = world()
        future = service.issue_future(context, handle, "business:D1", "actor:D1", "property:P1", now=NOW, require_commercial=True)
        self.assertNotEqual(preview.authority_id, future.authority_id); self.assertNotEqual(preview.nonce, future.nonce)
        self.assertEqual(AuthorityPhase.PREVIEW, preview.phase); self.assertEqual(AuthorityPhase.FUTURE, future.phase)

    def test_preview_success_does_not_create_future_authority(self):
        *_, authority, _, _ = world()
        self.assertEqual(AuthorityPhase.PREVIEW, authority.phase); self.assertEqual(Effect.PREVIEW_CALL, authority.permitted_effect)

    def test_future_issuance_requires_selection(self):
        _, _, service, context, handle, *_ = world(selection=False)
        with self.assertRaisesRegex(PermissionError, "selection"): service.issue_future(context, handle, "business:D1", "actor:D1", "property:P1", now=NOW)

    def test_future_issuance_can_require_commercial_state(self):
        _, _, service, context, handle, *_ = world(commercial=False)
        with self.assertRaisesRegex(PermissionError, "commercial"): service.issue_future(context, handle, "business:D1", "actor:D1", "property:P1", now=NOW, require_commercial=True)

    def test_payment_state_alone_cannot_replace_selection(self):
        _, _, service, context, handle, *_ = world(selection=False, commercial=True)
        with self.assertRaises(PermissionError): service.issue_future(context, handle, "business:D1", "actor:D1", "property:P1", now=NOW, require_selection=True, require_commercial=True)

    def test_future_can_be_issued_without_commercial_requirement(self):
        _, _, service, context, handle, *_ = world(commercial=False)
        authority = service.issue_future(context, handle, "business:D1", "actor:D1", "property:P1", now=NOW, require_commercial=False)
        self.assertFalse(authority.commercial_required)

    def test_property_outside_query_results_is_rejected(self):
        _, _, service, context, handle, *_ = world()
        with self.assertRaisesRegex(ValueError, "outside query"): service.issue_preview(context, handle, "business:D1", "actor:D1", "property:P99", now=NOW)

    def test_handle_from_another_query_is_rejected(self):
        _, _, service, context, _, *_ = world()
        other = service.create_context("inquiry-2", "user:A", ("property:P1",), NOW, NOW + timedelta(hours=1))
        other_handle = service.create_handle(other, NOW + timedelta(minutes=30))
        with self.assertRaisesRegex(ValueError, "not bound"): service.issue_preview(context, other_handle, "business:D1", "actor:D1", "property:P1", now=NOW)

    def test_unregistered_context_is_rejected(self):
        _, _, service, context, handle, *_ = world(); unregistered = replace(context, query_context_id="query:unknown")
        with self.assertRaisesRegex(ValueError, "not registered"): service.issue_preview(unregistered, handle, "business:D1", "actor:D1", "property:P1", now=NOW)

    def test_inactive_context_is_rejected_at_issuance(self):
        _, _, service, context, handle, *_ = world()
        with self.assertRaisesRegex(ValueError, "inactive"): service.issue_preview(context, handle, "business:D1", "actor:D1", "property:P1", now=context.valid_until)

    def test_handle_cannot_outlive_query(self):
        _, _, service, context, *_ = world()
        with self.assertRaisesRegex(ValueError, "outlive"): service.create_handle(context, context.valid_until + timedelta(seconds=1))

    def test_authority_is_clamped_to_query_end(self):
        _, _, service, context, handle, *_ = world()
        authority = service.issue_future(context, handle, "business:D1", "actor:D1", "property:P1", now=NOW, duration=timedelta(days=30))
        self.assertEqual(handle.expires_at, authority.validity_end)

    def test_preview_quota_is_explicit(self):
        *_, authority, _, _ = world(quota=2); self.assertEqual(2, authority.quota)

    def test_delegated_actor_is_explicitly_in_scope(self):
        _, _, service, context, handle, *_ = world()
        authority = service.issue_preview(context, handle, "business:D1", "actor:D1", "property:P1", now=NOW, authorized_actors=("callcenter:C1",))
        self.assertIn("callcenter:C1", authority.authorized_actor_ids)

    def test_duplicate_delegated_actor_is_deduplicated(self):
        _, _, service, context, handle, *_ = world()
        authority = service.issue_preview(context, handle, "business:D1", "actor:D1", "property:P1", now=NOW, authorized_actors=("actor:D1", "actor:D1"))
        self.assertEqual(("actor:D1",), authority.authorized_actor_ids)

    def test_preview_cannot_encode_future_effect(self):
        _, _, service, context, handle, *_ = world()
        with self.assertRaisesRegex(ValueError, "preview authority"): service.issue_preview(context, handle, "business:D1", "actor:D1", "property:P1", now=NOW, effect=Effect.FUTURE_CONTACT)

    def test_future_cannot_encode_preview_effect(self):
        _, _, service, context, handle, *_ = world()
        with self.assertRaisesRegex(ValueError, "future authority"): service.issue_future(context, handle, "business:D1", "actor:D1", "property:P1", now=NOW, effect=Effect.PREVIEW_CALL)

    def test_message_preview_is_supported_as_variation(self):
        _, _, service, context, handle, *_ = world()
        authority = service.issue_preview(context, handle, "business:D1", "actor:D1", "property:P1", now=NOW, channel=Channel.MESSAGE, effect=Effect.PREVIEW_MESSAGE)
        self.assertEqual(Channel.MESSAGE, authority.channel)

    def test_each_handle_is_query_scoped_and_rotated(self):
        _, _, service, context, *_ = world()
        h1 = service.create_handle(context, NOW + timedelta(hours=1)); h2 = service.create_handle(context, NOW + timedelta(hours=1))
        self.assertNotEqual(h1.handle_id, h2.handle_id); self.assertEqual(context.query_context_id, h1.query_context_id)

if __name__ == "__main__": unittest.main()
