#!/usr/bin/env python3
import argparse
from collections import Counter
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
            if origin == "INVALID":
                data[sentence_id] = (None, None)
            else:
                data[sentence_id] = (origin, destination)
    return data


def main() -> int:
    parser = argparse.ArgumentParser(description="Dataset report.")
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
    parser.add_argument("--top", type=int, default=10)
    args = parser.parse_args()

    input_data = load_input(args.input)
    expected_data = load_expected(args.expected)

    input_ids = set(input_data.keys())
    expected_ids = set(expected_data.keys())

    missing_expected = sorted(input_ids - expected_ids)
    missing_input = sorted(expected_ids - input_ids)

    total = len(input_ids)
    valid = 0
    invalid = 0
    origins = Counter()
    destinations = Counter()
    lengths = []

    for sentence_id, sentence in input_data.items():
        lengths.append(len(sentence.split()))
        origin, destination = expected_data.get(sentence_id, (None, None))
        if origin is None:
            invalid += 1
        else:
            valid += 1
            origins[origin] += 1
            destinations[destination] += 1

    avg_len = (sum(lengths) / len(lengths)) if lengths else 0.0

    print(f"total={total}")
    print(f"valid_expected={valid}")
    print(f"invalid_expected={invalid}")
    print(f"avg_tokens={avg_len:.2f}")
    print(f"missing_expected={len(missing_expected)}")
    print(f"missing_input={len(missing_input)}")

    if origins:
        print("top_origins=")
        for name, count in origins.most_common(args.top):
            print(f"{name},{count}")

    if destinations:
        print("top_destinations=")
        for name, count in destinations.most_common(args.top):
            print(f"{name},{count}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
