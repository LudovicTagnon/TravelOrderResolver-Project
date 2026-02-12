import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
sys.path.append(str(SCRIPTS))

import build_manual_review_sheet


class BuildManualReviewSheetTest(unittest.TestCase):
    def test_flags_for_invalid_and_intermediate(self) -> None:
        flags = build_manual_review_sheet.compute_flags(
            sentence="y a t il un train de paris a lyon en passant par tours",
            prefill=("INVALID", ""),
            rule_based=("Paris", "Lyon"),
            ml=("Paris", "Lyon"),
        )
        self.assertIn("prefill_invalid", flags)
        self.assertIn("contains_intermediate", flags)
        self.assertIn("prefill_rule_based_diff", flags)
        self.assertIn("ml_prefill_diff", flags)
        self.assertEqual("high", build_manual_review_sheet.compute_priority(flags))

    def test_priority_low_when_only_ml_disagrees(self) -> None:
        flags = build_manual_review_sheet.compute_flags(
            sentence="depart paris destination lyon",
            prefill=("Paris", "Lyon"),
            rule_based=("Paris", "Lyon"),
            ml=("Lyon", "Paris"),
        )
        self.assertEqual(["ml_rule_based_diff", "ml_prefill_diff"], flags)
        self.assertEqual("low", build_manual_review_sheet.compute_priority(flags))


if __name__ == "__main__":
    unittest.main()
