#!/usr/bin/env python3
import argparse
import csv
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Prepare a corrections template from actionable review rows."
    )
    parser.add_argument(
        "--review-actionable",
        type=Path,
        default=Path("datasets/manual/review_actionable_120.csv"),
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("datasets/manual/corrections_120.csv"),
    )
    args = parser.parse_args()

    if not args.review_actionable.exists():
        return 1

    rows = []
    with args.review_actionable.open("r", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            rows.append(row)

    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(
            [
                "id",
                "sentence",
                "current_origin",
                "current_destination",
                "suggested_origin",
                "suggested_destination",
                "final_origin",
                "final_destination",
                "notes",
            ]
        )
        for row in rows:
            writer.writerow(
                [
                    row.get("id", ""),
                    row.get("sentence", ""),
                    row.get("prefill_origin", ""),
                    row.get("prefill_destination", ""),
                    row.get("rule_based_origin", ""),
                    row.get("rule_based_destination", ""),
                    row.get("prefill_origin", ""),
                    row.get("prefill_destination", ""),
                    "",
                ]
            )

    print(f"rows={len(rows)}")
    print(f"template={args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
