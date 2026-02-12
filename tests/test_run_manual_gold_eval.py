import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
sys.path.append(str(SCRIPTS))

import run_manual_gold_eval


class RunManualGoldEvalTest(unittest.TestCase):
    def test_build_nlp_leaderboard_sorts_and_skips_none(self) -> None:
        leaderboard = run_manual_gold_eval.build_nlp_leaderboard(
            {
                "ml": {"accuracy": 0.55, "valid_f1": 0.54, "invalid_accuracy": 1.0},
                "camembert_v2": {
                    "accuracy": 0.99,
                    "valid_f1": 0.99,
                    "invalid_accuracy": 1.0,
                },
                "rule_based": {"accuracy": 1.0, "valid_f1": 1.0, "invalid_accuracy": 1.0},
                "missing": None,
            }
        )
        self.assertEqual(["rule_based", "camembert_v2", "ml"], [row["model"] for row in leaderboard])
        self.assertEqual(3, len(leaderboard))


if __name__ == "__main__":
    unittest.main()
