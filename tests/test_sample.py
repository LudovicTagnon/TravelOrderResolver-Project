import unittest
from pathlib import Path

from src.travel_order_resolver import (
    build_place_index,
    build_place_pattern,
    load_places,
    resolve_order,
)


class SampleInputOutputTest(unittest.TestCase):
    def setUp(self) -> None:
        root = Path(__file__).resolve().parents[1]
        self.input_path = root / "students_project" / "sample_nlp_input.txt"
        self.output_path = root / "students_project" / "sample_nlp_output.txt"
        places_path = root / "data" / "places.txt"
        self.mapping = load_places(places_path)
        self.place_pattern = build_place_pattern(list(self.mapping.keys()))
        self.place_index, self.max_place_tokens = build_place_index(self.mapping)

    def test_sample_file_matches_expected(self) -> None:
        expected = {}
        with self.output_path.open("r", encoding="utf-8") as handle:
            for line in handle:
                line = line.strip("\n")
                if not line:
                    continue
                parts = line.split(",", 2)
                self.assertEqual(3, len(parts), msg=f"Bad output line: {line}")
                expected[parts[0]] = line

        with self.input_path.open("r", encoding="utf-8") as handle:
            for line in handle:
                line = line.strip("\n")
                if not line:
                    continue
                sentence_id, sentence = line.split(",", 1)
                origin, destination = resolve_order(
                    sentence,
                    self.mapping,
                    self.place_pattern,
                    self.place_index,
                    self.max_place_tokens,
                )
                if origin and destination:
                    actual = f"{sentence_id},{origin},{destination}"
                else:
                    actual = f"{sentence_id},INVALID,"
                self.assertEqual(expected[sentence_id], actual)


if __name__ == "__main__":
    unittest.main()
