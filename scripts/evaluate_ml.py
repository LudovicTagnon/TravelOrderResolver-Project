#!/usr/bin/env python3
import argparse
import csv
import json
from pathlib import Path

from joblib import load


def load_inputs(path: Path) -> dict:
    data = {}
    with path.open("r", encoding="utf-8") as handle:
        reader = csv.reader(handle)
        for row in reader:
            if len(row) < 2:
                continue
            sentence_id, sentence = row[0], row[1]
            data[sentence_id] = sentence
    return data


def load_outputs(path: Path) -> dict:
    data = {}
    with path.open("r", encoding="utf-8") as handle:
        reader = csv.reader(handle)
        for row in reader:
            if len(row) < 2:
                continue
            sentence_id = row[0]
            origin = row[1] if len(row) >= 2 else ""
            destination = row[2] if len(row) >= 3 else ""
            if origin == "INVALID":
                data[sentence_id] = ("INVALID", "INVALID")
            else:
                data[sentence_id] = (origin, destination)
    return data


def compute_metrics(input_path: Path, expected_path: Path, model_dir: Path) -> dict | None:
    origin_model_path = model_dir / "origin_model.joblib"
    dest_model_path = model_dir / "dest_model.joblib"
    if not origin_model_path.exists() or not dest_model_path.exists():
        return None

    inputs = load_inputs(input_path)
    outputs = load_outputs(expected_path)

    origin_model = load(origin_model_path)
    dest_model = load(dest_model_path)

    total = 0
    correct = 0
    invalid_expected = 0
    invalid_correct = 0
    valid_expected = 0
    valid_predicted = 0
    valid_correct = 0
    origin_correct = 0
    destination_correct = 0

    for sentence_id, sentence in inputs.items():
        if sentence_id not in outputs:
            continue
        expected_origin, expected_dest = outputs[sentence_id]
        origin_pred = origin_model.predict([sentence])[0]
        dest_pred = dest_model.predict([sentence])[0]

        total += 1
        if expected_origin == "INVALID":
            invalid_expected += 1
        else:
            valid_expected += 1

        predicted = (origin_pred, dest_pred)
        expected = (expected_origin, expected_dest)
        if expected_origin == "INVALID" and origin_pred == "INVALID" and dest_pred == "INVALID":
            invalid_correct += 1

        if predicted == expected:
            correct += 1
            if expected_origin != "INVALID":
                valid_correct += 1
                origin_correct += 1
                destination_correct += 1
        else:
            if expected_origin != "INVALID":
                if origin_pred == expected_origin:
                    origin_correct += 1
                if dest_pred == expected_dest:
                    destination_correct += 1

        if origin_pred != "INVALID" and dest_pred != "INVALID":
            valid_predicted += 1

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

    return {
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


def main() -> int:
    parser = argparse.ArgumentParser(description="Evaluate ML baseline.")
    parser.add_argument("--input", type=Path, default=Path("datasets/dev_input.txt"))
    parser.add_argument("--expected", type=Path, default=Path("datasets/dev_output.txt"))
    parser.add_argument("--model-dir", type=Path, default=Path("models"))
    parser.add_argument("--format", choices=["text", "json"], default="text")
    args = parser.parse_args()

    metrics = compute_metrics(args.input, args.expected, args.model_dir)
    if metrics is None:
        return 1

    if args.format == "json":
        print(json.dumps(metrics, ensure_ascii=True, indent=2))
        return 0

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

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
