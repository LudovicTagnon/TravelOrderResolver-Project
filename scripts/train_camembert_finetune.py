#!/usr/bin/env python3
import argparse
import csv
import json
import random
from pathlib import Path

import numpy as np
import torch
from torch.optim import AdamW
from torch.utils.data import DataLoader, Dataset
from transformers import AutoModelForSequenceClassification, AutoTokenizer


def set_seed(seed: int) -> None:
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)


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


class EncodedDataset(Dataset):
    def __init__(self, encodings: dict, labels: list[int]):
        self.encodings = encodings
        self.labels = labels

    def __len__(self) -> int:
        return len(self.labels)

    def __getitem__(self, idx: int):
        item = {key: torch.tensor(value[idx]) for key, value in self.encodings.items()}
        item["labels"] = torch.tensor(self.labels[idx])
        return item


def build_samples(
    input_rows: dict[str, str],
    output_rows: dict[str, tuple[str, str]],
    target: str,
) -> tuple[list[str], list[str]]:
    sentences: list[str] = []
    labels: list[str] = []
    for sentence_id, sentence in input_rows.items():
        if sentence_id not in output_rows:
            continue
        origin, destination = output_rows[sentence_id]
        label = origin if target == "origin" else destination
        sentences.append(sentence)
        labels.append(label)
    return sentences, labels


def evaluate_accuracy(model, data_loader: DataLoader, device: torch.device) -> float:
    model.eval()
    total = 0
    correct = 0
    with torch.no_grad():
        for batch in data_loader:
            labels = batch["labels"].to(device)
            inputs = {key: value.to(device) for key, value in batch.items() if key != "labels"}
            outputs = model(**inputs)
            preds = outputs.logits.argmax(dim=1)
            total += labels.size(0)
            correct += (preds == labels).sum().item()
    return (correct / total) if total else 0.0


def train(
    model,
    train_loader: DataLoader,
    dev_loader: DataLoader | None,
    device: torch.device,
    lr: float,
    epochs: int,
    output_dir: Path,
) -> dict:
    optimizer = AdamW(model.parameters(), lr=lr)
    best_dev = -1.0
    history = []
    best_state_path = output_dir / "best_state.pt"

    for epoch in range(1, epochs + 1):
        model.train()
        epoch_loss = 0.0
        for batch in train_loader:
            labels = batch["labels"].to(device)
            inputs = {key: value.to(device) for key, value in batch.items() if key != "labels"}
            outputs = model(**inputs, labels=labels)
            loss = outputs.loss
            loss.backward()
            optimizer.step()
            optimizer.zero_grad()
            epoch_loss += float(loss.item())

        train_loss = epoch_loss / max(1, len(train_loader))
        entry = {"epoch": epoch, "train_loss": train_loss}
        if dev_loader is not None:
            dev_acc = evaluate_accuracy(model, dev_loader, device)
            entry["dev_accuracy"] = dev_acc
            if dev_acc > best_dev:
                best_dev = dev_acc
                torch.save(model.state_dict(), best_state_path)
        history.append(entry)
        print(json.dumps(entry, ensure_ascii=True))

    if dev_loader is not None and best_state_path.exists():
        model.load_state_dict(torch.load(best_state_path, map_location=device))
        best_state_path.unlink(missing_ok=True)

    return {"history": history, "best_dev_accuracy": best_dev if best_dev >= 0 else None}


def main() -> int:
    parser = argparse.ArgumentParser(description="Fine-tune CamemBERT for origin or destination classification.")
    parser.add_argument("--train-input", type=Path, default=Path("datasets/train_input.txt"))
    parser.add_argument("--train-output", type=Path, default=Path("datasets/train_output.txt"))
    parser.add_argument("--dev-input", type=Path, default=Path("datasets/dev_input.txt"))
    parser.add_argument("--dev-output", type=Path, default=Path("datasets/dev_output.txt"))
    parser.add_argument("--target", choices=["origin", "destination"], required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--hf-model", default="camembert-base")
    parser.add_argument("--max-length", type=int, default=64)
    parser.add_argument("--batch-size", type=int, default=16)
    parser.add_argument("--epochs", type=int, default=2)
    parser.add_argument("--lr", type=float, default=2e-5)
    parser.add_argument("--max-train-samples", type=int, default=None)
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()

    if not args.train_input.exists() or not args.train_output.exists():
        return 1

    set_seed(args.seed)

    train_inputs = load_inputs(args.train_input)
    train_outputs = load_outputs(args.train_output)
    train_sentences, train_labels_raw = build_samples(train_inputs, train_outputs, args.target)
    if args.max_train_samples is not None:
        train_sentences = train_sentences[: args.max_train_samples]
        train_labels_raw = train_labels_raw[: args.max_train_samples]
    if not train_sentences:
        return 1

    label_values = sorted(set(train_labels_raw))
    label2id = {label: idx for idx, label in enumerate(label_values)}
    id2label = {idx: label for label, idx in label2id.items()}
    train_labels = [label2id[label] for label in train_labels_raw]

    tokenizer = AutoTokenizer.from_pretrained(args.hf_model)
    train_encodings = tokenizer(
        train_sentences,
        truncation=True,
        padding=True,
        max_length=args.max_length,
    )
    train_dataset = EncodedDataset(train_encodings, train_labels)
    train_loader = DataLoader(train_dataset, batch_size=args.batch_size, shuffle=True)

    dev_loader = None
    if args.dev_input.exists() and args.dev_output.exists():
        dev_inputs = load_inputs(args.dev_input)
        dev_outputs = load_outputs(args.dev_output)
        dev_sentences, dev_labels_raw = build_samples(dev_inputs, dev_outputs, args.target)
        dev_sentences_filtered = []
        dev_labels = []
        for sentence, label in zip(dev_sentences, dev_labels_raw):
            if label not in label2id:
                continue
            dev_sentences_filtered.append(sentence)
            dev_labels.append(label2id[label])
        if dev_sentences_filtered:
            dev_encodings = tokenizer(
                dev_sentences_filtered,
                truncation=True,
                padding=True,
                max_length=args.max_length,
            )
            dev_dataset = EncodedDataset(dev_encodings, dev_labels)
            dev_loader = DataLoader(dev_dataset, batch_size=args.batch_size, shuffle=False)

    model = AutoModelForSequenceClassification.from_pretrained(
        args.hf_model,
        num_labels=len(label2id),
        id2label=id2label,
        label2id=label2id,
    )
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model.to(device)

    args.output_dir.mkdir(parents=True, exist_ok=True)
    train_info = train(
        model=model,
        train_loader=train_loader,
        dev_loader=dev_loader,
        device=device,
        lr=args.lr,
        epochs=args.epochs,
        output_dir=args.output_dir,
    )

    model.save_pretrained(args.output_dir)
    tokenizer.save_pretrained(args.output_dir)
    metadata = {
        "target": args.target,
        "hf_model": args.hf_model,
        "max_length": args.max_length,
        "batch_size": args.batch_size,
        "epochs": args.epochs,
        "lr": args.lr,
        "seed": args.seed,
        "train_size": len(train_sentences),
        "label_count": len(label2id),
        "device": str(device),
        **train_info,
    }
    with (args.output_dir / "metadata.json").open("w", encoding="utf-8") as handle:
        json.dump(metadata, handle, ensure_ascii=True, indent=2)

    print(f"output_dir={args.output_dir}")
    print(f"target={args.target}")
    print(f"train_size={len(train_sentences)}")
    print(f"label_count={len(label2id)}")
    print(f"device={device}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
