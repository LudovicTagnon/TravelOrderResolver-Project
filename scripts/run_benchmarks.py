#!/usr/bin/env python3
import argparse
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def run_eval(input_path: Path, expected_path: Path, places_path: Path) -> dict:
    command = [
        sys.executable,
        str(ROOT / "scripts" / "evaluate.py"),
        "--input",
        str(input_path),
        "--expected",
        str(expected_path),
        "--places",
        str(places_path),
        "--format",
        "json",
    ]
    output = subprocess.check_output(command, text=True)
    return json.loads(output)


def main() -> int:
    parser = argparse.ArgumentParser(description="Run benchmarks on train/dev/test splits.")
    parser.add_argument("--datasets", type=Path, default=ROOT / "datasets")
    parser.add_argument("--places", type=Path, default=ROOT / "data" / "places.txt")
    parser.add_argument("--output", type=Path, default=ROOT / "reports" / "metrics.json")
    args = parser.parse_args()

    splits = {
        "train": (args.datasets / "train_input.txt", args.datasets / "train_output.txt"),
        "dev": (args.datasets / "dev_input.txt", args.datasets / "dev_output.txt"),
        "test": (args.datasets / "test_input.txt", args.datasets / "test_output.txt"),
    }

    results = {}
    for name, (input_path, expected_path) in splits.items():
        if not input_path.exists() or not expected_path.exists():
            continue
        results[name] = run_eval(input_path, expected_path, args.places)

    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", encoding="utf-8") as handle:
        json.dump(results, handle, indent=2, ensure_ascii=True)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
