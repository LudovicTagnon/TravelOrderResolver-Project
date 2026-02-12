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
    parser = argparse.ArgumentParser(
        description="Run complete evaluation on the manual gold dataset."
    )
    parser.add_argument("--input", type=Path, default=ROOT / "datasets" / "manual" / "input_starter.csv")
    parser.add_argument(
        "--gold-output",
        type=Path,
        default=ROOT / "datasets" / "manual" / "output_gold_120.csv",
    )
    parser.add_argument("--places", type=Path, default=ROOT / "data" / "places.txt")
    parser.add_argument("--model-dir", type=Path, default=ROOT / "models")
    parser.add_argument("--graph", type=Path, default=ROOT / "data" / "graph.json")
    parser.add_argument("--stops-index", type=Path, default=ROOT / "data" / "stops_index.json")
    parser.add_argument("--stops-areas", type=Path, default=ROOT / "data" / "stops_areas.csv")
    parser.add_argument("--reports", type=Path, default=ROOT / "reports")
    parser.add_argument("--datasets", type=Path, default=ROOT / "datasets")
    args = parser.parse_args()

    required = (
        args.input,
        args.gold_output,
        args.places,
        args.graph,
        args.stops_index,
    )
    if any(not path.exists() for path in required):
        return 1

    args.reports.mkdir(parents=True, exist_ok=True)
    (args.datasets / "manual").mkdir(parents=True, exist_ok=True)

    rule_metrics = run_json(
        [
            sys.executable,
            str(ROOT / "scripts" / "evaluate.py"),
            "--input",
            str(args.input),
            "--expected",
            str(args.gold_output),
            "--places",
            str(args.places),
            "--format",
            "json",
        ]
    )
    ml_metrics = run_json(
        [
            sys.executable,
            str(ROOT / "scripts" / "evaluate_ml.py"),
            "--input",
            str(args.input),
            "--expected",
            str(args.gold_output),
            "--model-dir",
            str(args.model_dir),
            "--format",
            "json",
        ]
    )
    e2e_metrics = run_json(
        [
            sys.executable,
            str(ROOT / "scripts" / "evaluate_end_to_end.py"),
            "--input",
            str(args.input),
            "--places",
            str(args.places),
            "--graph",
            str(args.graph),
            "--stops-index",
            str(args.stops_index),
            "--stops-areas",
            str(args.stops_areas),
            "--output-csv",
            str(args.datasets / "manual" / "e2e_manual_gold_120.csv"),
            "--summary",
            str(args.reports / "e2e_manual_gold_120_summary.json"),
        ]
    )

    rule_path = args.reports / "manual_gold_metrics_rule_based.json"
    ml_path = args.reports / "manual_gold_metrics_ml.json"
    dashboard_path = args.reports / "manual_gold_dashboard.json"

    with rule_path.open("w", encoding="utf-8") as handle:
        json.dump(rule_metrics, handle, ensure_ascii=True, indent=2)
    with ml_path.open("w", encoding="utf-8") as handle:
        json.dump(ml_metrics, handle, ensure_ascii=True, indent=2)

    dashboard = {
        "input": str(args.input),
        "gold_output": str(args.gold_output),
        "rule_based": rule_metrics,
        "ml": ml_metrics,
        "end_to_end": e2e_metrics,
    }
    with dashboard_path.open("w", encoding="utf-8") as handle:
        json.dump(dashboard, handle, ensure_ascii=True, indent=2)

    print(f"rule_based={rule_path}")
    print(f"ml={ml_path}")
    print(f"e2e={args.reports / 'e2e_manual_gold_120_summary.json'}")
    print(f"dashboard={dashboard_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
