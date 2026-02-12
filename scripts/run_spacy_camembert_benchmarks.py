#!/usr/bin/env python3
import argparse
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def run_json(command: list[str]) -> dict:
    output = subprocess.check_output(command, text=True)
    return json.loads(output)


def main() -> int:
    parser = argparse.ArgumentParser(description="Run spaCy and CamemBERT benchmarks on dev/test.")
    parser.add_argument("--python-bin", default=str(ROOT / ".venv" / "bin" / "python"))
    parser.add_argument("--datasets", type=Path, default=ROOT / "datasets")
    parser.add_argument("--places", type=Path, default=ROOT / "data" / "places.txt")
    parser.add_argument("--spacy-model", default="fr_core_news_sm")
    parser.add_argument("--camembert-model-dir", type=Path, default=ROOT / "models" / "camembert")
    parser.add_argument(
        "--output",
        type=Path,
        default=ROOT / "reports" / "spacy_camembert_metrics.json",
    )
    args = parser.parse_args()

    python_bin = args.python_bin
    splits = {
        "dev": (args.datasets / "dev_input.txt", args.datasets / "dev_output.txt"),
        "test": (args.datasets / "test_input.txt", args.datasets / "test_output.txt"),
    }
    results: dict[str, dict] = {"spacy": {}, "camembert": {}}

    for split, (input_path, expected_path) in splits.items():
        results["spacy"][split] = run_json(
            [
                python_bin,
                str(ROOT / "scripts" / "evaluate_spacy.py"),
                "--input",
                str(input_path),
                "--expected",
                str(expected_path),
                "--places",
                str(args.places),
                "--spacy-model",
                args.spacy_model,
                "--format",
                "json",
            ]
        )
        results["camembert"][split] = run_json(
            [
                python_bin,
                str(ROOT / "scripts" / "evaluate_camembert.py"),
                "--input",
                str(input_path),
                "--expected",
                str(expected_path),
                "--model-dir",
                str(args.camembert_model_dir),
                "--format",
                "json",
            ]
        )

    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", encoding="utf-8") as handle:
        json.dump(results, handle, ensure_ascii=True, indent=2)

    print(f"output={args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
