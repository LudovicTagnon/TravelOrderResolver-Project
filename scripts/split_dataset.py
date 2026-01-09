#!/usr/bin/env python3
import argparse
import random
from pathlib import Path


def load_input(path: Path) -> dict:
    data = {}
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip("\n")
            if not line or "," not in line:
                continue
            sentence_id, sentence = line.split(",", 1)
            data[sentence_id] = sentence
    return data


def load_expected(path: Path) -> dict:
    data = {}
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip("\n")
            if not line:
                continue
            parts = line.split(",", 2)
            if len(parts) != 3:
                continue
            sentence_id, origin, destination = parts
            data[sentence_id] = (origin, destination)
    return data


def write_split(path: Path, pairs: list[tuple[str, str]]) -> None:
    with path.open("w", encoding="utf-8") as handle:
        for sentence_id, sentence in pairs:
            handle.write(f"{sentence_id},{sentence}\n")


def write_expected(path: Path, pairs: list[tuple[str, tuple[str, str]]]) -> None:
    with path.open("w", encoding="utf-8") as handle:
        for sentence_id, (origin, destination) in pairs:
            handle.write(f"{sentence_id},{origin},{destination}\n")


def main() -> int:
    parser = argparse.ArgumentParser(description="Split dataset into train/dev/test.")
    parser.add_argument(
        "--input",
        type=Path,
        default=Path("students_project/sample_nlp_input.txt"),
    )
    parser.add_argument(
        "--expected",
        type=Path,
        default=Path("students_project/sample_nlp_output.txt"),
    )
    parser.add_argument("--train", type=float, default=0.8)
    parser.add_argument("--dev", type=float, default=0.1)
    parser.add_argument("--test", type=float, default=0.1)
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--out-dir", type=Path, default=Path("datasets"))
    args = parser.parse_args()

    total_ratio = args.train + args.dev + args.test
    if total_ratio <= 0:
        return 1

    input_data = load_input(args.input)
    expected_data = load_expected(args.expected)

    ids = [sid for sid in input_data if sid in expected_data]
    rng = random.Random(args.seed)
    rng.shuffle(ids)

    total = len(ids)
    train_size = int(total * (args.train / total_ratio))
    dev_size = int(total * (args.dev / total_ratio))

    train_ids = ids[:train_size]
    dev_ids = ids[train_size : train_size + dev_size]
    test_ids = ids[train_size + dev_size :]

    out_dir = args.out_dir
    out_dir.mkdir(parents=True, exist_ok=True)

    write_split(
        out_dir / "train_input.txt",
        [(sid, input_data[sid]) for sid in train_ids],
    )
    write_expected(
        out_dir / "train_output.txt",
        [(sid, expected_data[sid]) for sid in train_ids],
    )

    write_split(
        out_dir / "dev_input.txt",
        [(sid, input_data[sid]) for sid in dev_ids],
    )
    write_expected(
        out_dir / "dev_output.txt",
        [(sid, expected_data[sid]) for sid in dev_ids],
    )

    write_split(
        out_dir / "test_input.txt",
        [(sid, input_data[sid]) for sid in test_ids],
    )
    write_expected(
        out_dir / "test_output.txt",
        [(sid, expected_data[sid]) for sid in test_ids],
    )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
