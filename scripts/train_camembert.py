#!/usr/bin/env python3
import argparse
import csv
import json
from pathlib import Path

import numpy as np
import torch
from joblib import dump
from sklearn.svm import LinearSVC
from transformers import AutoModel, AutoTokenizer


def load_inputs(path: Path) -> dict[str, str]:
    data = {}
    with path.open("r", encoding="utf-8") as handle:
        reader = csv.reader(handle)
        for row in reader:
            if len(row) < 2:
                continue
            data[row[0]] = row[1]
    return data


def load_outputs(path: Path) -> dict[str, tuple[str, str]]:
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


def embed_sentences(
    sentences: list[str],
    tokenizer,
    model,
    device: torch.device,
    batch_size: int,
    max_length: int,
) -> np.ndarray:
    vectors = []
    model.eval()
    for start in range(0, len(sentences), batch_size):
        batch = sentences[start : start + batch_size]
        encoded = tokenizer(
            batch,
            padding=True,
            truncation=True,
            max_length=max_length,
            return_tensors="pt",
        )
        encoded = {key: value.to(device) for key, value in encoded.items()}
        with torch.no_grad():
            output = model(**encoded)
            hidden = output.last_hidden_state
            mask = encoded["attention_mask"].unsqueeze(-1)
            pooled = (hidden * mask).sum(dim=1) / mask.sum(dim=1).clamp(min=1)
            vectors.append(pooled.cpu().numpy())
    return np.vstack(vectors) if vectors else np.empty((0, model.config.hidden_size))


def main() -> int:
    parser = argparse.ArgumentParser(description="Train CamemBERT + LinearSVC baseline.")
    parser.add_argument("--train-input", type=Path, default=Path("datasets/train_input.txt"))
    parser.add_argument("--train-output", type=Path, default=Path("datasets/train_output.txt"))
    parser.add_argument("--model-dir", type=Path, default=Path("models/camembert"))
    parser.add_argument("--hf-model", default="camembert-base")
    parser.add_argument("--batch-size", type=int, default=32)
    parser.add_argument("--max-length", type=int, default=64)
    parser.add_argument("--max-samples", type=int, default=None)
    args = parser.parse_args()

    if not args.train_input.exists() or not args.train_output.exists():
        return 1

    inputs = load_inputs(args.train_input)
    outputs = load_outputs(args.train_output)

    sentence_ids = [sid for sid in inputs.keys() if sid in outputs]
    if args.max_samples is not None:
        sentence_ids = sentence_ids[: args.max_samples]
    if not sentence_ids:
        return 1

    sentences = [inputs[sid] for sid in sentence_ids]
    origins = [outputs[sid][0] for sid in sentence_ids]
    destinations = [outputs[sid][1] for sid in sentence_ids]

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    tokenizer = AutoTokenizer.from_pretrained(args.hf_model)
    model = AutoModel.from_pretrained(args.hf_model).to(device)

    embeddings = embed_sentences(
        sentences,
        tokenizer=tokenizer,
        model=model,
        device=device,
        batch_size=args.batch_size,
        max_length=args.max_length,
    )

    origin_clf = LinearSVC(dual="auto")
    destination_clf = LinearSVC(dual="auto")
    origin_clf.fit(embeddings, origins)
    destination_clf.fit(embeddings, destinations)

    args.model_dir.mkdir(parents=True, exist_ok=True)
    dump(origin_clf, args.model_dir / "origin_clf.joblib")
    dump(destination_clf, args.model_dir / "destination_clf.joblib")
    metadata = {
        "hf_model": args.hf_model,
        "batch_size": args.batch_size,
        "max_length": args.max_length,
        "max_samples": args.max_samples,
        "device": str(device),
        "train_size": len(sentence_ids),
    }
    with (args.model_dir / "metadata.json").open("w", encoding="utf-8") as handle:
        json.dump(metadata, handle, ensure_ascii=True, indent=2)

    print(f"model_dir={args.model_dir}")
    print(f"train_size={len(sentence_ids)}")
    print(f"device={device}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
