#!/usr/bin/env python3
import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.append(str(ROOT))

from src.travel_order_resolver import build_place_pattern, load_places, resolve_order


def load_expected(path: Path) -> dict:
    expected = {}
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip("\n")
            if not line:
                continue
            parts = line.split(",", 2)
            if len(parts) != 3:
                continue
            sentence_id, origin, destination = parts
            if origin == "INVALID":
                expected[sentence_id] = (None, None)
            else:
                expected[sentence_id] = (origin, destination)
    return expected


def evaluate(input_path: Path, expected_path: Path, places_path: Path, show_mismatches: bool) -> int:
    mapping = load_places(places_path)
    place_pattern = build_place_pattern(list(mapping.keys()))
    expected = load_expected(expected_path)

    total = 0
    correct = 0
    invalid_expected = 0
    invalid_correct = 0
    mismatches = []

    with input_path.open("r", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip("\n")
            if not line:
                continue
            if "," not in line:
                continue
            sentence_id, sentence = line.split(",", 1)
            origin, destination = resolve_order(sentence, mapping, place_pattern)
            expected_origin, expected_destination = expected.get(sentence_id, (None, None))
            total += 1
            if expected_origin is None:
                invalid_expected += 1
            if origin is None or destination is None:
                predicted = (None, None)
            else:
                predicted = (origin, destination)
            if predicted == (expected_origin, expected_destination):
                correct += 1
                if expected_origin is None:
                    invalid_correct += 1
            else:
                mismatches.append((sentence_id, predicted, (expected_origin, expected_destination)))

    accuracy = (correct / total) if total else 0.0
    invalid_accuracy = (invalid_correct / invalid_expected) if invalid_expected else 0.0

    print(f"total={total}")
    print(f"correct={correct}")
    print(f"accuracy={accuracy:.3f}")
    print(f"invalid_expected={invalid_expected}")
    print(f"invalid_correct={invalid_correct}")
    print(f"invalid_accuracy={invalid_accuracy:.3f}")

    if show_mismatches and mismatches:
        print("mismatches=")
        for sentence_id, predicted, expected_value in mismatches:
            print(f"{sentence_id},{predicted},{expected_value}")

    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Evaluate predictions against expected output.")
    parser.add_argument(
        "--input",
        type=Path,
        default=ROOT / "students_project" / "sample_nlp_input.txt",
    )
    parser.add_argument(
        "--expected",
        type=Path,
        default=ROOT / "students_project" / "sample_nlp_output.txt",
    )
    parser.add_argument(
        "--places",
        type=Path,
        default=ROOT / "data" / "places.txt",
    )
    parser.add_argument("--show-mismatches", action="store_true")
    args = parser.parse_args()

    if not args.input.exists() or not args.expected.exists() or not args.places.exists():
        return 1

    return evaluate(args.input, args.expected, args.places, args.show_mismatches)


if __name__ == "__main__":
    raise SystemExit(main())
