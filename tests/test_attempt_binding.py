import unittest
from fixtures import NOW, attempt, world


class AttemptBindingTests(unittest.TestCase):
    def test_exact_attempt_is_authorized(self):
        *_, authority, enforcement, _ = world()
        self.assertTrue(enforcement.evaluate(authority, attempt(authority), NOW).allowed)


CASES = {
    "authority_id": ("authority_id", "other-authority", "AUTHORITY_ID_MISMATCH"),
    "query_context": ("observed_query_context", "query-other", "QUERY_MISMATCH"),
    "inquiry": ("observed_inquiry_id", "inquiry-other", "INQUIRY_MISMATCH"),
    "business": ("observed_business_identity", "business:D2", "BUSINESS_MISMATCH"),
    "actor": ("observed_actor_id", "actor:attacker", "ACTOR_UNAUTHORIZED"),
    "user": ("observed_user_binding", "user:other", "USER_BINDING_MISMATCH"),
    "property": ("observed_property_id", "property:P2", "PROPERTY_MISMATCH"),
    "handle": ("observed_handle", "cvid:copied", "HANDLE_MISMATCH"),
    "phase": ("observed_phase", "FUTURE", "PHASE_MISMATCH"),
    "direction": ("observed_direction", "USER_TO_BUSINESS", "DIRECTION_MISMATCH"),
    "channel": ("observed_channel", "message", "CHANNEL_MISMATCH"),
    "purpose": ("observed_purpose", "marketing", "PURPOSE_MISMATCH"),
    "effect": ("observed_effect", "FUTURE_CONTACT", "EFFECT_MISMATCH"),
    "nonce": ("observed_nonce", "nonce:replayed", "NONCE_MISMATCH"),
    "enforcement_point": ("observed_enforcement_point", "edge:east", "ENFORCEMENT_POINT_MISMATCH"),
    "device": ("observed_device_binding", "device:other", "DEVICE_BINDING_MISMATCH"),
}


def make_case(field, value, expected):
    def test(self):
        *_, authority, enforcement, _ = world(device_binding="device:A" if field == "observed_device_binding" else "")
        decision = enforcement.evaluate(authority, attempt(authority, **{field: value}), NOW)
        self.assertFalse(decision.allowed); self.assertEqual(expected, decision.code)
    return test


for name, args in CASES.items(): setattr(AttemptBindingTests, f"test_mismatch_{name}_is_denied", make_case(*args))

if __name__ == "__main__": unittest.main()
