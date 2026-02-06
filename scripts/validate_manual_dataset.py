#!/usr/bin/env python3
import argparse
import csv
from pathlib import Path


def load_input(path: Path) -> dict:
    data = {}
    with path.open("r", encoding="utf-8") as handle:
        reader = csv.reader(handle)
        for row in reader:
            if len(row) < 2:
                continue
            sentence_id, sentence = row[0].strip(), row[1].strip()
            if sentence_id:
                data[sentence_id] = sentence
    return data


def load_output(path: Path) -> dict:
    data = {}
    with path.open("r", encoding="utf-8") as handle:
        reader = csv.reader(handle)
        for row in reader:
            if len(row) < 2:
                continue
            sentence_id = row[0].strip()
            origin = row[1].strip() if len(row) >= 2 else ""
            destination = row[2].strip() if len(row) >= 3 else ""
            data[sentence_id] = (origin, destination)
    return data


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate a manually annotated dataset.")
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    if not args.input.exists() or not args.output.exists():
        return 1

    inputs = load_input(args.input)
    outputs = load_output(args.output)

    input_ids = set(inputs.keys())
    output_ids = set(outputs.keys())

    missing_output = sorted(input_ids - output_ids)
    missing_input = sorted(output_ids - input_ids)

    invalid = 0
    valid = 0
    pending = 0
    malformed = 0
    for origin, destination in outputs.values():
        if origin == "INVALID":
            invalid += 1
            continue
        if not origin and not destination:
            pending += 1
            continue
        if bool(origin) != bool(destination):
            malformed += 1
            continue
        valid += 1

    print(f"input_lines={len(inputs)}")
    print(f"output_lines={len(outputs)}")
    print(f"valid={valid}")
    print(f"invalid={invalid}")
    print(f"pending={pending}")
    print(f"malformed={malformed}")
    print(f"missing_output={len(missing_output)}")
    print(f"missing_input={len(missing_input)}")

    if missing_output:
        print("missing_output_ids=")
        for sentence_id in missing_output[:20]:
            print(sentence_id)

    if missing_input:
        print("missing_input_ids=")
        for sentence_id in missing_input[:20]:
            print(sentence_id)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
