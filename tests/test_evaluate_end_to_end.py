import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
sys.path.append(str(SCRIPTS))

import evaluate_end_to_end


class EvaluateEndToEndTest(unittest.TestCase):
    def test_build_summary(self) -> None:
        summary = evaluate_end_to_end.build_summary(total=100, nlp_valid=80, path_valid=60)
        self.assertEqual(20, summary["nlp_invalid"])
        self.assertEqual(20, summary["path_invalid_on_nlp_valid"])
        self.assertAlmostEqual(0.8, summary["nlp_valid_rate"])
        self.assertAlmostEqual(0.75, summary["path_success_rate_on_nlp_valid"])
        self.assertAlmostEqual(0.6, summary["end_to_end_success_rate"])


if __name__ == "__main__":
    unittest.main()
