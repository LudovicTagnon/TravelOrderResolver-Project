#!/usr/bin/env python3
import argparse
import csv
import random
from pathlib import Path


def parse_line(line: str) -> tuple[str, str] | None:
    if not line or "," not in line:
        return None
    sentence_id, sentence = line.split(",", 1)
    sentence_id = sentence_id.strip()
    sentence = sentence.strip()
    if not sentence_id or not sentence:
        return None
    return sentence_id, sentence


def read_inputs(path: Path) -> list[tuple[str, str]]:
    rows = []
    with path.open("r", encoding="utf-8") as handle:
        for raw in handle:
            parsed = parse_line(raw.rstrip("\n"))
            if parsed:
                rows.append(parsed)
    return rows


def bucket(sentence: str) -> str:
    s = sentence.lower()
    if "en passant par" in s:
        return "intermediate"
    if "depart" in s or "destination" in s:
        return "explicit_keywords"
    if "?" in sentence or "comment" in s:
        return "question"
    if "train" in s or "trains" in s:
        return "train_terms"
    if any(token in s for token in ["saint", "gare", "port", "la rochelle"]):
        return "ambiguous_names"
    if len(sentence.split()) >= 10:
        return "long"
    return "standard"


def sample_by_bucket(rows: list[tuple[str, str]], count: int, seed: int) -> list[tuple[str, str]]:
    rng = random.Random(seed)
    groups: dict[str, list[tuple[str, str]]] = {}
    for row in rows:
        key = bucket(row[1])
        groups.setdefault(key, []).append(row)

    order = [
        "ambiguous_names",
        "intermediate",
        "explicit_keywords",
        "question",
        "train_terms",
        "long",
        "standard",
    ]

    # Target a balanced starter set across difficult patterns.
    per_bucket = max(1, count // max(1, len(order)))
    selected: list[tuple[str, str]] = []
    seen = set()

    for key in order:
        candidates = groups.get(key, [])
        rng.shuffle(candidates)
        for sentence_id, sentence in candidates:
            if (sentence_id, sentence) in seen:
                continue
            selected.append((sentence_id, sentence))
            seen.add((sentence_id, sentence))
            if len([1 for item in selected if bucket(item[1]) == key]) >= per_bucket:
                break

    if len(selected) < count:
        all_rows = rows[:]
        rng.shuffle(all_rows)
        for row in all_rows:
            if row in seen:
                continue
            selected.append(row)
            seen.add(row)
            if len(selected) >= count:
                break

    return selected[:count]


def write_input(path: Path, rows: list[tuple[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle)
        for idx, (_, sentence) in enumerate(rows, start=1):
            writer.writerow([idx, sentence])


def write_template(path: Path, rows: list[tuple[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle)
        for idx, _ in enumerate(rows, start=1):
            writer.writerow([idx, "", ""])


def main() -> int:
    parser = argparse.ArgumentParser(description="Bootstrap a manual annotation starter dataset.")
    parser.add_argument("--source", type=Path, default=Path("datasets/all_input.txt"))
    parser.add_argument("--count", type=int, default=120)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--output-input", type=Path, default=Path("datasets/manual/input_starter.csv"))
    parser.add_argument(
        "--output-template",
        type=Path,
        default=Path("datasets/manual/output_template.csv"),
    )
    args = parser.parse_args()

    if not args.source.exists():
        return 1

    rows = read_inputs(args.source)
    if not rows:
        return 1

    sampled = sample_by_bucket(rows, args.count, args.seed)
    write_input(args.output_input, sampled)
    write_template(args.output_template, sampled)

    print(f"generated={len(sampled)}")
    print(f"input={args.output_input}")
    print(f"template={args.output_template}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
