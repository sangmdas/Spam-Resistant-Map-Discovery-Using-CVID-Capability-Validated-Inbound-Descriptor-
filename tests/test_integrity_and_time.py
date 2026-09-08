import unittest
from dataclasses import replace
from datetime import timedelta
from fixtures import NOW, attempt, resign, world
from map_cvid import HMACSigner


class IntegrityAndTimeTests(unittest.TestCase):
    def test_unsigned_authority_is_denied(self):
        _, _, _, _, _, authority, enforcement, _ = world()
        self.assertEqual("AUTHORITY_INTEGRITY_INVALID", enforcement.evaluate(replace(authority, signature=""), attempt(authority), NOW).code)

    def test_tampered_signed_field_is_denied(self):
        _, _, _, _, _, authority, enforcement, _ = world()
        self.assertFalse(enforcement.evaluate(replace(authority, purpose="marketing"), attempt(authority), NOW).allowed)

    def test_wrong_signing_key_is_denied(self):
        _, _, _, _, _, authority, enforcement, _ = world()
        forged = HMACSigner(b"attacker-test-key-that-is-at-least-32-bytes").sign(replace(authority, signature=""))
        self.assertEqual("AUTHORITY_INTEGRITY_INVALID", enforcement.evaluate(forged, attempt(forged), NOW).code)

    def test_before_validity_start_is_denied(self):
        _, _, _, _, _, authority, enforcement, _ = world()
        self.assertEqual("AUTHORITY_NOT_YET_VALID", enforcement.evaluate(authority, attempt(authority), authority.validity_start - timedelta(microseconds=1)).code)

    def test_exact_validity_start_is_allowed(self):
        _, _, _, _, _, authority, enforcement, _ = world()
        self.assertTrue(enforcement.evaluate(authority, attempt(authority), authority.validity_start).allowed)

    def test_just_before_validity_end_is_allowed(self):
        _, _, _, _, _, authority, enforcement, _ = world()
        self.assertTrue(enforcement.evaluate(authority, attempt(authority), authority.validity_end - timedelta(microseconds=1)).allowed)

    def test_exact_validity_end_is_denied(self):
        _, _, _, _, _, authority, enforcement, _ = world()
        self.assertEqual("AUTHORITY_EXPIRED", enforcement.evaluate(authority, attempt(authority), authority.validity_end).code)

    def test_naive_evaluation_time_is_rejected(self):
        _, _, _, _, _, authority, enforcement, _ = world()
        with self.assertRaisesRegex(ValueError, "timezone-aware"): enforcement.evaluate(authority, attempt(authority), NOW.replace(tzinfo=None))

    def test_minimum_signing_key_length_is_enforced(self):
        with self.assertRaises(ValueError): HMACSigner(b"short")

if __name__ == "__main__": unittest.main()
