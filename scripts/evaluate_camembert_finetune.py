#!/usr/bin/env python3
import argparse
import csv
import json
from pathlib import Path

import torch
from transformers import AutoModelForSequenceClassification, AutoTokenizer


def load_inputs(path: Path) -> dict[str, str]:
    rows = {}
    with path.open("r", encoding="utf-8") as handle:
        reader = csv.reader(handle)
        for row in reader:
            if len(row) < 2:
                continue
            rows[row[0]] = row[1]
    return rows


def load_outputs(path: Path) -> dict[str, tuple[str, str]]:
    rows = {}
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


def predict_labels(
    model,
    tokenizer,
    sentences: list[str],
    sentence_ids: list[str],
    device: torch.device,
    batch_size: int,
    max_length: int,
) -> dict[str, str]:
    model.eval()
    pred_map = {}
    for start in range(0, len(sentences), batch_size):
        batch_sentences = sentences[start : start + batch_size]
        batch_ids = sentence_ids[start : start + batch_size]
        encoded = tokenizer(
            batch_sentences,
            truncation=True,
            padding=True,
            max_length=max_length,
            return_tensors="pt",
        )
        encoded = {key: value.to(device) for key, value in encoded.items()}
        with torch.no_grad():
            outputs = model(**encoded)
            preds = outputs.logits.argmax(dim=1).cpu().tolist()
        for sid, pred in zip(batch_ids, preds):
            pred_map[sid] = model.config.id2label[int(pred)]
    return pred_map


def compute_metrics(
    inputs: dict[str, str],
    expected: dict[str, tuple[str, str]],
    origin_pred: dict[str, str],
    destination_pred: dict[str, str],
) -> dict:
    total = 0
    correct = 0
    invalid_expected = 0
    invalid_correct = 0
    valid_expected = 0
    valid_predicted = 0
    valid_correct = 0
    origin_correct = 0
    destination_correct = 0

    for sentence_id in inputs:
        if sentence_id not in expected:
            continue
        expected_origin, expected_destination = expected[sentence_id]
        pred_origin = origin_pred.get(sentence_id, "INVALID")
        pred_destination = destination_pred.get(sentence_id, "INVALID")

        total += 1
        if expected_origin == "INVALID":
            invalid_expected += 1
        else:
            valid_expected += 1

        if pred_origin != "INVALID" and pred_destination != "INVALID":
            valid_predicted += 1

        if expected_origin == "INVALID" and pred_origin == "INVALID" and pred_destination == "INVALID":
            invalid_correct += 1

        if (pred_origin, pred_destination) == (expected_origin, expected_destination):
            correct += 1
            if expected_origin != "INVALID":
                valid_correct += 1
                origin_correct += 1
                destination_correct += 1
        else:
            if expected_origin != "INVALID":
                if pred_origin == expected_origin:
                    origin_correct += 1
                if pred_destination == expected_destination:
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
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Evaluate fine-tuned CamemBERT origin/destination models.")
    parser.add_argument("--input", type=Path, default=Path("datasets/dev_input.txt"))
    parser.add_argument("--expected", type=Path, default=Path("datasets/dev_output.txt"))
    parser.add_argument("--origin-model-dir", type=Path, required=True)
    parser.add_argument("--destination-model-dir", type=Path, required=True)
    parser.add_argument("--batch-size", type=int, default=32)
    parser.add_argument("--max-length", type=int, default=64)
    parser.add_argument("--format", choices=["text", "json"], default="text")
    args = parser.parse_args()

    if not args.input.exists() or not args.expected.exists():
        return 1
    if not args.origin_model_dir.exists() or not args.destination_model_dir.exists():
        return 1

    inputs = load_inputs(args.input)
    expected = load_outputs(args.expected)
    sentence_ids = [sid for sid in inputs.keys() if sid in expected]
    sentences = [inputs[sid] for sid in sentence_ids]

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    origin_tokenizer = AutoTokenizer.from_pretrained(args.origin_model_dir)
    destination_tokenizer = AutoTokenizer.from_pretrained(args.destination_model_dir)
    origin_model = AutoModelForSequenceClassification.from_pretrained(args.origin_model_dir).to(device)
    destination_model = AutoModelForSequenceClassification.from_pretrained(
        args.destination_model_dir
    ).to(device)

    origin_pred = predict_labels(
        model=origin_model,
        tokenizer=origin_tokenizer,
        sentences=sentences,
        sentence_ids=sentence_ids,
        device=device,
        batch_size=args.batch_size,
        max_length=args.max_length,
    )
    destination_pred = predict_labels(
        model=destination_model,
        tokenizer=destination_tokenizer,
        sentences=sentences,
        sentence_ids=sentence_ids,
        device=device,
        batch_size=args.batch_size,
        max_length=args.max_length,
    )

    metrics = compute_metrics(inputs, expected, origin_pred, destination_pred)
    metrics["device"] = str(device)

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
    print(f"device={metrics['device']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
