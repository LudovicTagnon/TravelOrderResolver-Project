import csv
import tempfile
import unittest
from pathlib import Path

from scripts.apply_manual_corrections import load_corrections, load_output_rows


class ApplyManualCorrectionsTest(unittest.TestCase):
    def test_apply_corrections(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)
            base_path = tmp / "base.csv"
            corrections_path = tmp / "corrections.csv"

            with base_path.open("w", encoding="utf-8", newline="") as handle:
                writer = csv.writer(handle)
                writer.writerow(["1", "Paris", "Lyon"])
                writer.writerow(["2", "INVALID", ""])

            with corrections_path.open("w", encoding="utf-8", newline="") as handle:
                writer = csv.writer(handle)
                writer.writerow(
                    [
                        "id",
                        "sentence",
                        "current_origin",
                        "current_destination",
                        "suggested_origin",
                        "suggested_destination",
                        "final_origin",
                        "final_destination",
                        "notes",
                    ]
                )
                writer.writerow(["1", "x", "Paris", "Lyon", "", "", "Paris", "Marseille", ""])
                writer.writerow(["2", "x", "INVALID", "", "", "", "INVALID", "", ""])

            rows = load_output_rows(base_path)
            corrections = load_corrections(corrections_path)

            for row in rows:
                update = corrections.get(row[0])
                if not update:
                    continue
                origin, destination = update
                if origin == "INVALID":
                    row[1] = "INVALID"
                    row[2] = ""
                else:
                    row[1] = origin
                    row[2] = destination

            self.assertEqual(["1", "Paris", "Marseille"], rows[0])
            self.assertEqual(["2", "INVALID", ""], rows[1])


if __name__ == "__main__":
    unittest.main()
