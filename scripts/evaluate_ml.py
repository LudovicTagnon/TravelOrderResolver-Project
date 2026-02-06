#!/usr/bin/env python3
import argparse
import csv
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


def main() -> int:
    parser = argparse.ArgumentParser(description="Evaluate ML baseline.")
    parser.add_argument("--input", type=Path, default=Path("datasets/dev_input.txt"))
    parser.add_argument("--expected", type=Path, default=Path("datasets/dev_output.txt"))
    parser.add_argument("--model-dir", type=Path, default=Path("models"))
    args = parser.parse_args()

    origin_model_path = args.model_dir / "origin_model.joblib"
    dest_model_path = args.model_dir / "dest_model.joblib"
    if not origin_model_path.exists() or not dest_model_path.exists():
        return 1

    inputs = load_inputs(args.input)
    outputs = load_outputs(args.expected)

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

    print(f"total={total}")
    print(f"correct={correct}")
    print(f"accuracy={accuracy:.3f}")
    print(f"invalid_expected={invalid_expected}")
    print(f"invalid_correct={invalid_correct}")
    print(f"invalid_accuracy={invalid_accuracy:.3f}")
    print(f"valid_expected={valid_expected}")
    print(f"valid_predicted={valid_predicted}")
    print(f"valid_correct={valid_correct}")
    print(f"valid_precision={valid_precision:.3f}")
    print(f"valid_recall={valid_recall:.3f}")
    print(f"valid_f1={valid_f1:.3f}")
    print(f"origin_accuracy={origin_accuracy:.3f}")
    print(f"destination_accuracy={destination_accuracy:.3f}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
