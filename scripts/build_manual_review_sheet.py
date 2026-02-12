#!/usr/bin/env python3
import argparse
import csv
import json
import sys
from collections import Counter
from pathlib import Path

from joblib import load

ROOT = Path(__file__).resolve().parents[1]
sys.path.append(str(ROOT))

from src.travel_order_resolver import (
    build_place_index,
    build_place_pattern,
    load_places,
    resolve_order,
)


Prediction = tuple[str, str]


def load_inputs(path: Path) -> dict[str, str]:
    rows: dict[str, str] = {}
    with path.open("r", encoding="utf-8") as handle:
        reader = csv.reader(handle)
        for row in reader:
            if len(row) < 2:
                continue
            sentence_id = row[0].strip()
            sentence = row[1].strip()
            if sentence_id and sentence:
                rows[sentence_id] = sentence
    return rows


def load_outputs(path: Path) -> dict[str, Prediction]:
    rows: dict[str, Prediction] = {}
    with path.open("r", encoding="utf-8") as handle:
        reader = csv.reader(handle)
        for row in reader:
            if len(row) < 2:
                continue
            sentence_id = row[0].strip()
            if not sentence_id:
                continue
            origin = row[1].strip() if len(row) >= 2 else ""
            destination = row[2].strip() if len(row) >= 3 else ""
            rows[sentence_id] = (origin, destination)
    return rows


def normalize_prediction(origin: str, destination: str) -> Prediction:
    if origin == "INVALID":
        return ("INVALID", "")
    return (origin, destination)


def compute_flags(
    sentence: str,
    prefill: Prediction,
    rule_based: Prediction,
    ml: Prediction | None,
) -> list[str]:
    flags: list[str] = []
    sentence_lower = sentence.lower()
    prefill_origin, prefill_destination = prefill
    rb_origin, rb_destination = rule_based

    if prefill_origin == "INVALID":
        flags.append("prefill_invalid")
    elif bool(prefill_origin) != bool(prefill_destination):
        flags.append("prefill_malformed")

    if "en passant par" in sentence_lower:
        flags.append("contains_intermediate")

    if any(token in sentence_lower for token in ("ami ", "amis ", "voir mon ami")):
        flags.append("contains_context_noise")

    if (prefill_origin, prefill_destination) != (rb_origin, rb_destination):
        flags.append("prefill_rule_based_diff")

    if ml is not None:
        ml_origin, ml_destination = ml
        if (ml_origin, ml_destination) != (rb_origin, rb_destination):
            flags.append("ml_rule_based_diff")
        if (ml_origin, ml_destination) != (prefill_origin, prefill_destination):
            flags.append("ml_prefill_diff")

    return flags


def compute_priority(flags: list[str]) -> str:
    if any(flag in flags for flag in ("prefill_invalid", "prefill_malformed", "prefill_rule_based_diff")):
        return "high"
    if any(flag in flags for flag in ("contains_intermediate", "contains_context_noise")):
        return "medium"
    if flags:
        return "low"
    return "none"


def load_models(model_dir: Path):
    origin_model_path = model_dir / "origin_model.joblib"
    destination_model_path = model_dir / "dest_model.joblib"
    if not origin_model_path.exists() or not destination_model_path.exists():
        return None, None
    return load(origin_model_path), load(destination_model_path)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Build a review sheet for manual dataset validation."
    )
    parser.add_argument("--input", type=Path, default=Path("datasets/manual/input_starter.csv"))
    parser.add_argument(
        "--prefill", type=Path, default=Path("datasets/manual/output_prefill_120.csv")
    )
    parser.add_argument("--places", type=Path, default=Path("data/places.txt"))
    parser.add_argument("--model-dir", type=Path, default=Path("models"))
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("datasets/manual/review_sheet_120.csv"),
    )
    parser.add_argument(
        "--summary",
        type=Path,
        default=Path("reports/manual_review_summary.json"),
    )
    parser.add_argument(
        "--output-actionable",
        type=Path,
        default=Path("datasets/manual/review_actionable_120.csv"),
    )
    args = parser.parse_args()

    if not args.input.exists() or not args.prefill.exists() or not args.places.exists():
        return 1

    inputs = load_inputs(args.input)
    prefill = load_outputs(args.prefill)

    mapping = load_places(args.places)
    place_pattern = build_place_pattern(list(mapping.keys()))
    place_index, max_place_tokens = build_place_index(mapping)

    ml_origin_model, ml_destination_model = load_models(args.model_dir)

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.summary.parent.mkdir(parents=True, exist_ok=True)
    args.output_actionable.parent.mkdir(parents=True, exist_ok=True)

    flag_counts: Counter[str] = Counter()
    priority_counts: Counter[str] = Counter()
    flagged_ids: list[str] = []
    actionable_ids: list[str] = []
    rows_written = 0

    header = [
        "id",
        "sentence",
        "prefill_origin",
        "prefill_destination",
        "rule_based_origin",
        "rule_based_destination",
        "ml_origin",
        "ml_destination",
        "flags",
        "priority",
    ]
    with (
        args.output.open("w", encoding="utf-8", newline="") as handle,
        args.output_actionable.open("w", encoding="utf-8", newline="") as actionable_handle,
    ):
        writer = csv.writer(handle)
        actionable_writer = csv.writer(actionable_handle)
        writer.writerow(header)
        actionable_writer.writerow(header)

        for sentence_id in sorted(inputs.keys(), key=lambda value: int(value) if value.isdigit() else value):
            sentence = inputs[sentence_id]

            prefill_origin, prefill_destination = normalize_prediction(
                *(prefill.get(sentence_id, ("", "")))
            )

            rb_origin, rb_destination = resolve_order(
                sentence, mapping, place_pattern, place_index, max_place_tokens
            )
            rule_based = ("INVALID", "") if (rb_origin is None or rb_destination is None) else (
                rb_origin,
                rb_destination,
            )

            ml_prediction: Prediction | None = None
            ml_origin = ""
            ml_destination = ""
            if ml_origin_model is not None and ml_destination_model is not None:
                ml_origin = str(ml_origin_model.predict([sentence])[0])
                ml_destination = str(ml_destination_model.predict([sentence])[0])
                if ml_origin == "INVALID":
                    ml_prediction = ("INVALID", "")
                    ml_destination = ""
                else:
                    ml_prediction = (ml_origin, ml_destination)

            flags = compute_flags(sentence, (prefill_origin, prefill_destination), rule_based, ml_prediction)
            priority = compute_priority(flags)

            for flag in flags:
                flag_counts[flag] += 1
            if flags:
                flagged_ids.append(sentence_id)
            if priority in ("high", "medium"):
                actionable_ids.append(sentence_id)
            priority_counts[priority] += 1

            out_row = [
                sentence_id,
                sentence,
                prefill_origin,
                prefill_destination,
                rule_based[0],
                rule_based[1],
                ml_origin,
                ml_destination,
                "|".join(flags),
                priority,
            ]
            writer.writerow(out_row)
            if priority in ("high", "medium"):
                actionable_writer.writerow(out_row)
            rows_written += 1

    summary = {
        "total": rows_written,
        "flagged": len(flagged_ids),
        "flagged_ratio": (len(flagged_ids) / rows_written) if rows_written else 0.0,
        "actionable": len(actionable_ids),
        "actionable_ratio": (len(actionable_ids) / rows_written) if rows_written else 0.0,
        "flag_counts": dict(sorted(flag_counts.items())),
        "priority_counts": dict(sorted(priority_counts.items())),
        "flagged_ids": flagged_ids,
        "actionable_ids": actionable_ids,
    }
    with args.summary.open("w", encoding="utf-8") as handle:
        json.dump(summary, handle, ensure_ascii=True, indent=2)

    print(f"rows={rows_written}")
    print(f"flagged={summary['flagged']}")
    print(f"summary={args.summary}")
    print(f"sheet={args.output}")
    print(f"actionable_sheet={args.output_actionable}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
