#!/usr/bin/env python3
import argparse
import csv
from pathlib import Path


def load_output_rows(path: Path) -> list[list[str]]:
    rows: list[list[str]] = []
    with path.open("r", encoding="utf-8") as handle:
        reader = csv.reader(handle)
        for row in reader:
            if not row:
                continue
            sentence_id = row[0].strip()
            origin = row[1].strip() if len(row) >= 2 else ""
            destination = row[2].strip() if len(row) >= 3 else ""
            rows.append([sentence_id, origin, destination])
    return rows


def load_corrections(path: Path) -> dict[str, tuple[str, str]]:
    corrections: dict[str, tuple[str, str]] = {}
    with path.open("r", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            sentence_id = (row.get("id") or "").strip()
            if not sentence_id:
                continue
            origin = (row.get("final_origin") or "").strip()
            destination = (row.get("final_destination") or "").strip()
            if not origin and not destination:
                continue
            corrections[sentence_id] = (origin, destination)
    return corrections


def main() -> int:
    parser = argparse.ArgumentParser(description="Apply manual corrections on a base output file.")
    parser.add_argument(
        "--base-output",
        type=Path,
        default=Path("datasets/manual/output_prefill_120.csv"),
    )
    parser.add_argument(
        "--corrections",
        type=Path,
        default=Path("datasets/manual/corrections_120.csv"),
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("datasets/manual/output_gold_120.csv"),
    )
    args = parser.parse_args()

    if not args.base_output.exists() or not args.corrections.exists():
        return 1

    rows = load_output_rows(args.base_output)
    corrections = load_corrections(args.corrections)

    applied = 0
    malformed = 0
    for row in rows:
        sentence_id = row[0]
        update = corrections.get(sentence_id)
        if update is None:
            continue
        origin, destination = update
        if origin == "INVALID":
            row[1] = "INVALID"
            row[2] = ""
            applied += 1
            continue
        if not origin or not destination:
            malformed += 1
            continue
        row[1] = origin
        row[2] = destination
        applied += 1

    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerows(rows)

    print(f"base_rows={len(rows)}")
    print(f"corrections={len(corrections)}")
    print(f"applied={applied}")
    print(f"malformed={malformed}")
    print(f"output={args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
