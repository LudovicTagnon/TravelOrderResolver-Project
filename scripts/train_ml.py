#!/usr/bin/env python3
import argparse
import csv
from pathlib import Path

from joblib import dump
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.pipeline import Pipeline
from sklearn.svm import LinearSVC


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


def build_pipeline() -> Pipeline:
    return Pipeline(
        [
            (
                "tfidf",
                TfidfVectorizer(
                    analyzer="char_wb",
                    ngram_range=(3, 5),
                    min_df=2,
                ),
            ),
            ("clf", LinearSVC(dual="auto")),
        ]
    )


def main() -> int:
    parser = argparse.ArgumentParser(description="Train ML baseline (origin/destination classifiers).")
    parser.add_argument("--train-input", type=Path, default=Path("datasets/train_input.txt"))
    parser.add_argument("--train-output", type=Path, default=Path("datasets/train_output.txt"))
    parser.add_argument("--model-dir", type=Path, default=Path("models"))
    args = parser.parse_args()

    if not args.train_input.exists() or not args.train_output.exists():
        return 1

    inputs = load_inputs(args.train_input)
    outputs = load_outputs(args.train_output)

    sentences = []
    origin_labels = []
    dest_labels = []

    for sentence_id, sentence in inputs.items():
        if sentence_id not in outputs:
            continue
        origin, destination = outputs[sentence_id]
        sentences.append(sentence)
        origin_labels.append(origin)
        dest_labels.append(destination)

    if not sentences:
        return 1

    origin_model = build_pipeline()
    dest_model = build_pipeline()

    origin_model.fit(sentences, origin_labels)
    dest_model.fit(sentences, dest_labels)

    args.model_dir.mkdir(parents=True, exist_ok=True)
    dump(origin_model, args.model_dir / "origin_model.joblib")
    dump(dest_model, args.model_dir / "dest_model.joblib")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
