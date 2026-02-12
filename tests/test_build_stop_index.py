import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
import sys

sys.path.append(str(SCRIPTS))

import build_stop_index


class BuildStopIndexTest(unittest.TestCase):
    def test_read_rows_supports_csv(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            csv_path = Path(tmpdir) / "stops.csv"
            csv_path.write_text(
                "stop_id;stop_name;location_type\n"
                "StopArea:1;Paris Gare de Lyon;1\n"
                "StopPoint:2;Paris Gare de Lyon quai A;0\n",
                encoding="utf-8",
            )
            header, rows = build_stop_index.read_rows(csv_path)
            self.assertIn("stop_id", header)
            self.assertIn("stop_name", header)
            self.assertEqual(2, len(rows))

    def test_build_variant_keys_cleans_encoding_glitch(self) -> None:
        keys = build_stop_index.build_variant_keys("Saint √©tienne")
        self.assertIn("saint etienne", keys)


if __name__ == "__main__":
    unittest.main()
