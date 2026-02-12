import unittest
from collections import Counter

from scripts.analyze_ml_errors import top_items


class AnalyzeMlErrorsTest(unittest.TestCase):
    def test_top_items(self) -> None:
        counter = Counter()
        counter[("Paris", "Lyon")] = 3
        counter[("Nice", "Marseille")] = 1
        rows = top_items(counter, limit=1)
        self.assertEqual([["Paris", "Lyon", 3]], rows)


if __name__ == "__main__":
    unittest.main()
