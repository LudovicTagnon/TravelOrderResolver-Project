#!/usr/bin/env python3
import argparse
import csv
import json
import re
import sys
from pathlib import Path

import spacy
from spacy.matcher import Matcher

ROOT = Path(__file__).resolve().parents[1]
sys.path.append(str(ROOT))

from src.travel_order_resolver import load_places, normalize


def build_matcher(nlp, mapping: dict[str, str]) -> Matcher:
    matcher = Matcher(nlp.vocab)
    seen = set()
    for alias_norm in mapping.keys():
        tokens = alias_norm.split()
        if not tokens:
            continue
        key = tuple(tokens)
        if key in seen:
            continue
        seen.add(key)
        pattern = [{"LOWER": token} for token in tokens]
        matcher.add("PLACE", [pattern])
    return matcher


def select_by_cues(
    mentions: list[tuple[int, str]],
    sentence_norm: str,
    cue_patterns: list[str],
) -> str | None:
    candidates = []
    for cue in cue_patterns:
        for match in re.finditer(cue, sentence_norm):
            cue_end = match.end()
            after = [item for item in mentions if item[0] >= cue_end]
            if after:
                candidates.append(after[0])
    if not candidates:
        return None
    return candidates[-1][1]


def predict_sentence(
    nlp,
    matcher: Matcher,
    mapping: dict[str, str],
    sentence: str,
) -> tuple[str | None, str | None]:
    sentence_norm = normalize(sentence)
    doc = nlp(sentence)
    matches = matcher(doc)

    mentions: list[tuple[int, str]] = []
    seen = set()
    for _, start, end in matches:
        span = doc[start:end]
        canonical = mapping.get(normalize(span.text))
        if not canonical:
            continue
        key = (span.start_char, canonical)
        if key in seen:
            continue
        seen.add(key)
        mentions.append((span.start_char, canonical))

    mentions.sort(key=lambda item: item[0])
    ordered = []
    for _, place in mentions:
        if place not in ordered:
            ordered.append(place)

    origin_cues = [
        r"\bdepuis\b",
        r"\ben\s+partant\s+de\b",
        r"\bpartant\s+de\b",
        r"\bdepart\b",
        r"\bde\b",
    ]
    destination_cues = [
        r"\ba\b",
        r"\bvers\b",
        r"\bpour\b",
        r"\bdestination\b",
    ]

    origin = select_by_cues(mentions, sentence_norm, origin_cues)
    destination = select_by_cues(mentions, sentence_norm, destination_cues)

    if origin is None and ordered:
        origin = ordered[0]
    if destination is None and len(ordered) >= 2:
        for place in ordered:
            if place != origin:
                destination = place
                break

    if not origin or not destination or origin == destination:
        return None, None
    return origin, destination


def load_expected(path: Path) -> dict[str, tuple[str | None, str | None]]:
    expected = {}
    with path.open("r", encoding="utf-8") as handle:
        reader = csv.reader(handle)
        for row in reader:
            if len(row) < 2:
                continue
            sentence_id = row[0]
            origin = row[1] if len(row) >= 2 else ""
            destination = row[2] if len(row) >= 3 else ""
            if origin == "INVALID":
                expected[sentence_id] = (None, None)
            else:
                expected[sentence_id] = (origin, destination)
    return expected


def compute_metrics(
    input_path: Path,
    expected_path: Path,
    places_path: Path,
    spacy_model: str,
) -> dict:
    mapping = load_places(places_path)
    nlp = spacy.load(spacy_model)
    matcher = build_matcher(nlp, mapping)
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

    with input_path.open("r", encoding="utf-8") as handle:
        reader = csv.reader(handle)
        for row in reader:
            if len(row) < 2:
                continue
            sentence_id = row[0]
            sentence = row[1]
            total += 1

            expected_origin, expected_destination = expected.get(sentence_id, (None, None))
            if expected_origin is None:
                invalid_expected += 1
            else:
                valid_expected += 1

            origin, destination = predict_sentence(nlp, matcher, mapping, sentence)
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

    accuracy = (correct / total) if total else 0.0
    invalid_accuracy = (invalid_correct / invalid_expected) if invalid_expected else 0.0
    valid_precision = (valid_correct / valid_predicted) if valid_predicted else 0.0
    valid_recall = (valid_correct / valid_expected) if valid_expected else 0.0
    valid_f1 = (
        (2 * valid_precision * valid_recall) / (valid_precision + valid_recall)
        if (valid_precision + valid_recall)
        else 0.0
    )
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
        "spacy_model": spacy_model,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Evaluate spaCy baseline on NLP task.")
    parser.add_argument("--input", type=Path, default=Path("datasets/dev_input.txt"))
    parser.add_argument("--expected", type=Path, default=Path("datasets/dev_output.txt"))
    parser.add_argument("--places", type=Path, default=Path("data/places.txt"))
    parser.add_argument("--spacy-model", default="fr_core_news_sm")
    parser.add_argument("--format", choices=["text", "json"], default="text")
    args = parser.parse_args()

    if not args.input.exists() or not args.expected.exists() or not args.places.exists():
        return 1

    metrics = compute_metrics(args.input, args.expected, args.places, args.spacy_model)
    if args.format == "json":
        print(json.dumps(metrics, ensure_ascii=True, indent=2))
        return 0

    for key in [
        "total",
        "correct",
        "accuracy",
        "invalid_expected",
        "invalid_correct",
        "invalid_accuracy",
        "valid_expected",
        "valid_predicted",
        "valid_correct",
        "valid_precision",
        "valid_recall",
        "valid_f1",
        "origin_accuracy",
        "destination_accuracy",
    ]:
        value = metrics[key]
        if isinstance(value, float):
            print(f"{key}={value:.3f}")
        else:
            print(f"{key}={value}")
    print(f"spacy_model={metrics['spacy_model']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
