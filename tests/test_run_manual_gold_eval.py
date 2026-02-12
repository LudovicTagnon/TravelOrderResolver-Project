import sys
import unittest

from scripts.run_manual_gold_eval import run_json


class RunManualGoldEvalTest(unittest.TestCase):
    def test_run_json(self) -> None:
        data = run_json([sys.executable, "-c", "import json;print(json.dumps({'ok': 1}))"])
        self.assertEqual({"ok": 1}, data)


if __name__ == "__main__":
    unittest.main()
