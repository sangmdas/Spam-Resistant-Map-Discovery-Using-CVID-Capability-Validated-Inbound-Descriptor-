import unittest
from datetime import timedelta
from fixtures import NOW, attempt, world
from map_cvid import Channel, Effect


class EndToEndFlowTests(unittest.TestCase):
    def test_preview_call_end_to_end(self):
        *_, authority, enforcement, allocator = world()
        decision = enforcement.evaluate(authority, attempt(authority), NOW)
        self.assertTrue(allocator.allocate(decision.capability, "actor:D1", decision.capability.resource_id, NOW).allowed)

    def test_preview_does_not_authorize_next_day_future_call(self):
        *_, authority, enforcement, _ = world()
        later = attempt(authority, transaction_id="future", observed_phase="FUTURE", observed_effect="FUTURE_CONTACT")
        self.assertFalse(enforcement.evaluate(authority, later, NOW + timedelta(minutes=1)).allowed)

    def test_new_future_authority_enables_bounded_later_contact(self):
        *_, authority, enforcement, allocator = world(preview=False, quota=3)
        decision = enforcement.evaluate(authority, attempt(authority), NOW + timedelta(hours=1))
        self.assertTrue(allocator.allocate(decision.capability, "actor:D1", decision.capability.resource_id, NOW + timedelta(hours=1)).allowed)

    def test_property_pivot_is_denied(self):
        *_, authority, enforcement, _ = world(preview=False)
        self.assertEqual("PROPERTY_MISMATCH", enforcement.evaluate(authority, attempt(authority, observed_property_id="property:P99"), NOW).code)

    def test_business_pivot_is_denied(self):
        *_, authority, enforcement, _ = world(preview=False)
        self.assertEqual("BUSINESS_MISMATCH", enforcement.evaluate(authority, attempt(authority, observed_business_identity="business:D6"), NOW).code)

    def test_affiliate_pivot_is_denied_without_delegation(self):
        *_, authority, enforcement, _ = world(preview=False)
        self.assertEqual("ACTOR_UNAUTHORIZED", enforcement.evaluate(authority, attempt(authority, observed_actor_id="affiliate:X"), NOW).code)

    def test_purpose_laundering_is_denied(self):
        *_, authority, enforcement, _ = world(preview=False)
        self.assertEqual("PURPOSE_MISMATCH", enforcement.evaluate(authority, attempt(authority, observed_purpose="unrelated-marketing"), NOW).code)

    def test_voice_authority_cannot_send_message(self):
        *_, authority, enforcement, _ = world(preview=False)
        self.assertEqual("CHANNEL_MISMATCH", enforcement.evaluate(authority, attempt(authority, observed_channel=Channel.MESSAGE), NOW).code)

    def test_stolen_handle_without_authority_is_not_reachability(self):
        *_, authority, enforcement, _ = world()
        stolen = attempt(authority, authority_id="made-up", observed_actor_id="attacker:X")
        self.assertEqual("AUTHORITY_ID_MISMATCH", enforcement.evaluate(authority, stolen, NOW).code)

    def test_ai_agent_requires_explicit_delegation(self):
        _, _, service, context, handle, _, enforcement, _ = world()
        authority = service.issue_preview(context, handle, "business:D1", "actor:D1", "property:P1", now=NOW, authorized_actors=("agent:AI1",))
        self.assertTrue(enforcement.evaluate(authority, attempt(authority, observed_actor_id="agent:AI1"), NOW).allowed)

    def test_undelegated_ai_agent_is_denied(self):
        *_, authority, enforcement, _ = world()
        self.assertFalse(enforcement.evaluate(authority, attempt(authority, observed_actor_id="agent:AI1"), NOW).allowed)

    def test_device_bound_flow_requires_same_device(self):
        *_, authority, enforcement, _ = world(device_binding="device:A")
        self.assertTrue(enforcement.evaluate(authority, attempt(authority), NOW).allowed)

    def test_device_bound_flow_denies_other_device(self):
        *_, authority, enforcement, _ = world(device_binding="device:A")
        self.assertEqual("DEVICE_BINDING_MISMATCH", enforcement.evaluate(authority, attempt(authority, observed_device_binding="device:B"), NOW).code)

if __name__ == "__main__": unittest.main()
