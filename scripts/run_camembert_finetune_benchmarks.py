#!/usr/bin/env python3
import argparse
import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def run_json(command: list[str]) -> dict:
    output = subprocess.check_output(command, text=True)
    return json.loads(output)


def main() -> int:
    parser = argparse.ArgumentParser(description="Run dev/test benchmarks for fine-tuned CamemBERT models.")
    parser.add_argument("--python-bin", default=str(ROOT / ".venv" / "bin" / "python"))
    parser.add_argument("--datasets", type=Path, default=ROOT / "datasets")
    parser.add_argument(
        "--origin-model-dir",
        type=Path,
        default=ROOT / "models" / "camembert_finetune" / "origin",
    )
    parser.add_argument(
        "--destination-model-dir",
        type=Path,
        default=ROOT / "models" / "camembert_finetune" / "destination",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=ROOT / "reports" / "camembert_finetune_metrics.json",
    )
    args = parser.parse_args()

    results = {}
    for split in ("dev", "test"):
        input_path = args.datasets / f"{split}_input.txt"
        expected_path = args.datasets / f"{split}_output.txt"
        results[split] = run_json(
            [
                args.python_bin,
                str(ROOT / "scripts" / "evaluate_camembert_finetune.py"),
                "--input",
                str(input_path),
                "--expected",
                str(expected_path),
                "--origin-model-dir",
                str(args.origin_model_dir),
                "--destination-model-dir",
                str(args.destination_model_dir),
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
