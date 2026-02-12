#!/usr/bin/env python3
import argparse
import csv
import json
from collections import Counter
from pathlib import Path

from joblib import load


def load_inputs(path: Path) -> dict[str, str]:
    rows: dict[str, str] = {}
    with path.open("r", encoding="utf-8") as handle:
        reader = csv.reader(handle)
        for row in reader:
            if len(row) < 2:
                continue
            rows[row[0]] = row[1]
    return rows


def load_outputs(path: Path) -> dict[str, tuple[str, str]]:
    rows: dict[str, tuple[str, str]] = {}
    with path.open("r", encoding="utf-8") as handle:
        reader = csv.reader(handle)
        for row in reader:
            if len(row) < 2:
                continue
            sentence_id = row[0]
            origin = row[1] if len(row) >= 2 else ""
            destination = row[2] if len(row) >= 3 else ""
            if origin == "INVALID":
                rows[sentence_id] = ("INVALID", "INVALID")
            else:
                rows[sentence_id] = (origin, destination)
    return rows


def top_items(counter: Counter, limit: int = 20) -> list[list]:
    return [[key[0], key[1], value] for key, value in counter.most_common(limit)]


def main() -> int:
    parser = argparse.ArgumentParser(description="Analyze ML baseline errors.")
    parser.add_argument("--input", type=Path, default=Path("datasets/dev_input.txt"))
    parser.add_argument("--expected", type=Path, default=Path("datasets/dev_output.txt"))
    parser.add_argument("--model-dir", type=Path, default=Path("models"))
    parser.add_argument("--output", type=Path, default=Path("reports/ml_error_analysis_dev.json"))
    parser.add_argument("--max-samples", type=int, default=50)
    args = parser.parse_args()

    origin_model_path = args.model_dir / "origin_model.joblib"
    dest_model_path = args.model_dir / "dest_model.joblib"
    if (
        not args.input.exists()
        or not args.expected.exists()
        or not origin_model_path.exists()
        or not dest_model_path.exists()
    ):
        return 1

    inputs = load_inputs(args.input)
    outputs = load_outputs(args.expected)

    origin_model = load(origin_model_path)
    dest_model = load(dest_model_path)

    total = 0
    exact_ok = 0
    invalid_expected = 0
    invalid_predicted = 0
    origin_confusions: Counter = Counter()
    destination_confusions: Counter = Counter()
    exact_confusions: Counter = Counter()
    samples: list[dict] = []

    for sentence_id, sentence in inputs.items():
        expected = outputs.get(sentence_id)
        if expected is None:
            continue
        expected_origin, expected_destination = expected
        pred_origin = str(origin_model.predict([sentence])[0])
        pred_destination = str(dest_model.predict([sentence])[0])

        total += 1
        if expected_origin == "INVALID":
            invalid_expected += 1
        if pred_origin == "INVALID":
            invalid_predicted += 1

        if (pred_origin, pred_destination) == (expected_origin, expected_destination):
            exact_ok += 1
            continue

        if pred_origin != expected_origin:
            origin_confusions[(expected_origin, pred_origin)] += 1
        if pred_destination != expected_destination:
            destination_confusions[(expected_destination, pred_destination)] += 1
        exact_confusions[
            (f"{expected_origin}->{expected_destination}", f"{pred_origin}->{pred_destination}")
        ] += 1

        if len(samples) < args.max_samples:
            samples.append(
                {
                    "id": sentence_id,
                    "sentence": sentence,
                    "expected_origin": expected_origin,
                    "expected_destination": expected_destination,
                    "pred_origin": pred_origin,
                    "pred_destination": pred_destination,
                }
            )

    analysis = {
        "total": total,
        "exact_ok": exact_ok,
        "exact_accuracy": (exact_ok / total) if total else 0.0,
        "invalid_expected": invalid_expected,
        "invalid_predicted": invalid_predicted,
        "origin_top_confusions": top_items(origin_confusions),
        "destination_top_confusions": top_items(destination_confusions),
        "exact_top_confusions": top_items(exact_confusions),
        "samples": samples,
    }

    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", encoding="utf-8") as handle:
        json.dump(analysis, handle, ensure_ascii=True, indent=2)

    print(f"output={args.output}")
    print(f"exact_accuracy={analysis['exact_accuracy']:.3f}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
