#!/usr/bin/env python3
import argparse
import json
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


def compute_metrics(
    input_path: Path,
    expected_path: Path,
    places_path: Path,
    show_mismatches: bool,
) -> tuple[dict, list]:
    mapping = load_places(places_path)
    place_pattern = build_place_pattern(list(mapping.keys()))
    expected = load_expected(expected_path)

    total = 0
    correct = 0
    invalid_expected = 0
    invalid_correct = 0
    valid_expected = 0
    valid_predicted = 0
    valid_correct = 0
    origin_correct = 0
    destination_correct = 0
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
            else:
                valid_expected += 1
            if origin is None or destination is None:
                predicted = (None, None)
            else:
                predicted = (origin, destination)
                valid_predicted += 1
            if predicted == (expected_origin, expected_destination):
                correct += 1
                if expected_origin is None:
                    invalid_correct += 1
                else:
                    valid_correct += 1
                    origin_correct += 1
                    destination_correct += 1
            else:
                if expected_origin is not None and predicted != (None, None):
                    if predicted[0] == expected_origin:
                        origin_correct += 1
                    if predicted[1] == expected_destination:
                        destination_correct += 1
                mismatches.append((sentence_id, predicted, (expected_origin, expected_destination)))

    accuracy = (correct / total) if total else 0.0
    invalid_accuracy = (invalid_correct / invalid_expected) if invalid_expected else 0.0
    valid_precision = (valid_correct / valid_predicted) if valid_predicted else 0.0
    valid_recall = (valid_correct / valid_expected) if valid_expected else 0.0
    if valid_precision + valid_recall:
        valid_f1 = (2 * valid_precision * valid_recall) / (valid_precision + valid_recall)
    else:
        valid_f1 = 0.0
    origin_accuracy = (origin_correct / valid_expected) if valid_expected else 0.0
    destination_accuracy = (destination_correct / valid_expected) if valid_expected else 0.0

    metrics = {
        "total": total,
        "correct": correct,
        "accuracy": accuracy,
        "invalid_expected": invalid_expected,
        "invalid_correct": invalid_correct,
        "invalid_accuracy": invalid_accuracy,
        "valid_expected": valid_expected,
        "valid_predicted": valid_predicted,
        "valid_correct": valid_correct,
        "valid_precision": valid_precision,
        "valid_recall": valid_recall,
        "valid_f1": valid_f1,
        "origin_accuracy": origin_accuracy,
        "destination_accuracy": destination_accuracy,
    }

    return metrics, mismatches


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
    parser.add_argument("--format", choices=["text", "json"], default="text")
    args = parser.parse_args()

    if not args.input.exists() or not args.expected.exists() or not args.places.exists():
        return 1

    metrics, mismatches = compute_metrics(
        args.input, args.expected, args.places, args.show_mismatches
    )

    if args.format == "json":
        print(json.dumps(metrics, ensure_ascii=True, indent=2))
    else:
        print(f"total={metrics['total']}")
        print(f"correct={metrics['correct']}")
        print(f"accuracy={metrics['accuracy']:.3f}")
        print(f"invalid_expected={metrics['invalid_expected']}")
        print(f"invalid_correct={metrics['invalid_correct']}")
        print(f"invalid_accuracy={metrics['invalid_accuracy']:.3f}")
        print(f"valid_expected={metrics['valid_expected']}")
        print(f"valid_predicted={metrics['valid_predicted']}")
        print(f"valid_correct={metrics['valid_correct']}")
        print(f"valid_precision={metrics['valid_precision']:.3f}")
        print(f"valid_recall={metrics['valid_recall']:.3f}")
        print(f"valid_f1={metrics['valid_f1']:.3f}")
        print(f"origin_accuracy={metrics['origin_accuracy']:.3f}")
        print(f"destination_accuracy={metrics['destination_accuracy']:.3f}")

        if args.show_mismatches and mismatches:
            print("mismatches=")
            for sentence_id, predicted, expected_value in mismatches:
                print(f"{sentence_id},{predicted},{expected_value}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
