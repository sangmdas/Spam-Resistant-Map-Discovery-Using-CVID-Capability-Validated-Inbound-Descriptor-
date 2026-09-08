import json
import unittest
from pathlib import Path
from fixtures import world
from map_cvid.crypto import canonical


class VariationsAndPrivacyTests(unittest.TestCase):
    CONFIGS = Path(__file__).parents[1] / "configs"

    def test_all_five_variations_exist(self):
        self.assertEqual(5, len(list(self.CONFIGS.glob("*.json"))))

    def test_all_variations_state_claim_limit(self):
        for path in self.CONFIGS.glob("*.json"):
            with self.subTest(path=path.name): self.assertTrue(json.loads(path.read_text())["claim_limit"])

    def test_all_variations_identify_finality_boundary(self):
        for path in self.CONFIGS.glob("*.json"):
            with self.subTest(path=path.name): self.assertTrue(json.loads(path.read_text())["boundary"])

    def test_canonical_authority_contains_no_phone_number_field(self):
        *_, authority, _, _ = world(); self.assertNotIn(b"phone", canonical(authority.unsigned_dict()).lower())

    def test_canonical_authority_contains_no_exact_location_field(self):
        *_, authority, _, _ = world(); self.assertNotIn(b"latitude", canonical(authority.unsigned_dict()).lower()); self.assertNotIn(b"longitude", canonical(authority.unsigned_dict()).lower())

    def test_handle_is_pseudonymous_reference_not_underlying_number(self):
        _, _, _, _, handle, *_ = world(); self.assertTrue(handle.handle_id.startswith("cvid-")); self.assertNotIn("+", handle.handle_id)

    def test_query_context_region_is_not_disclosed_in_authority(self):
        _, _, _, context, _, authority, *_ = world(); self.assertNotIn(context.region.encode(), canonical(authority.unsigned_dict()))

    def test_commercial_state_is_predicate_not_payment_record(self):
        *_, authority, _, _ = world(preview=False); encoded = canonical(authority.unsigned_dict()).lower()
        self.assertIn(b"commercial_required", encoded); self.assertNotIn(b"payment_record", encoded)

if __name__ == "__main__": unittest.main()
