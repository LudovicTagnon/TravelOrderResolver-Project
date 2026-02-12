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


def build_nlp_leaderboard(models: dict[str, dict | None]) -> list[dict]:
    leaderboard = []
    for model_name, metrics in models.items():
        if not metrics:
            continue
        leaderboard.append(
            {
                "model": model_name,
                "accuracy": metrics.get("accuracy"),
                "valid_f1": metrics.get("valid_f1"),
                "invalid_accuracy": metrics.get("invalid_accuracy"),
            }
        )
    leaderboard.sort(key=lambda row: float(row.get("accuracy", 0.0)), reverse=True)
    return leaderboard


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
    parser.add_argument(
        "--python-bin",
        default=sys.executable,
        help="Python binary used for optional Camembert evaluation scripts.",
    )
    parser.add_argument(
        "--with-camembert-ft",
        action="store_true",
        help="Include Camembert fine-tuned v2 metrics in the dashboard.",
    )
    parser.add_argument(
        "--camembert-origin-model-dir",
        type=Path,
        default=ROOT / "models" / "camembert_finetune_v2" / "origin",
    )
    parser.add_argument(
        "--camembert-destination-model-dir",
        type=Path,
        default=ROOT / "models" / "camembert_finetune_v2" / "destination",
    )
    parser.add_argument("--camembert-batch-size", type=int, default=32)
    parser.add_argument("--camembert-max-length", type=int, default=64)
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
    camembert_metrics = None
    camembert_e2e_metrics = None

    if args.with_camembert_ft:
        if not args.camembert_origin_model_dir.exists() or not args.camembert_destination_model_dir.exists():
            print("Camembert model directories are missing.", file=sys.stderr)
            return 1
        camembert_metrics = run_json(
            [
                args.python_bin,
                str(ROOT / "scripts" / "evaluate_camembert_finetune.py"),
                "--input",
                str(args.input),
                "--expected",
                str(args.gold_output),
                "--origin-model-dir",
                str(args.camembert_origin_model_dir),
                "--destination-model-dir",
                str(args.camembert_destination_model_dir),
                "--batch-size",
                str(args.camembert_batch_size),
                "--max-length",
                str(args.camembert_max_length),
                "--format",
                "json",
            ]
        )
        camembert_e2e_metrics = run_json(
            [
                args.python_bin,
                str(ROOT / "scripts" / "evaluate_end_to_end.py"),
                "--input",
                str(args.input),
                "--nlp-backend",
                "camembert-ft",
                "--origin-model-dir",
                str(args.camembert_origin_model_dir),
                "--destination-model-dir",
                str(args.camembert_destination_model_dir),
                "--graph",
                str(args.graph),
                "--stops-index",
                str(args.stops_index),
                "--stops-areas",
                str(args.stops_areas),
                "--output-csv",
                str(args.datasets / "manual" / "e2e_manual_gold_120_camembert_v2.csv"),
                "--summary",
                str(args.reports / "e2e_manual_gold_120_camembert_v2_summary.json"),
            ]
        )

    rule_path = args.reports / "manual_gold_metrics_rule_based.json"
    ml_path = args.reports / "manual_gold_metrics_ml.json"
    camembert_path = args.reports / "manual_gold_metrics_camembert_v2.json"
    dashboard_path = args.reports / "manual_gold_dashboard.json"

    with rule_path.open("w", encoding="utf-8") as handle:
        json.dump(rule_metrics, handle, ensure_ascii=True, indent=2)
    with ml_path.open("w", encoding="utf-8") as handle:
        json.dump(ml_metrics, handle, ensure_ascii=True, indent=2)
    if camembert_metrics is not None:
        with camembert_path.open("w", encoding="utf-8") as handle:
            json.dump(camembert_metrics, handle, ensure_ascii=True, indent=2)

    dashboard = {
        "input": str(args.input),
        "gold_output": str(args.gold_output),
        "rule_based": rule_metrics,
        "ml": ml_metrics,
        "end_to_end": e2e_metrics,
        "camembert_v2": camembert_metrics,
        "end_to_end_camembert_v2": camembert_e2e_metrics,
        "nlp_leaderboard": build_nlp_leaderboard(
            {
                "rule_based": rule_metrics,
                "camembert_v2": camembert_metrics,
                "ml": ml_metrics,
            }
        ),
    }
    with dashboard_path.open("w", encoding="utf-8") as handle:
        json.dump(dashboard, handle, ensure_ascii=True, indent=2)

    print(f"rule_based={rule_path}")
    print(f"ml={ml_path}")
    if camembert_metrics is not None:
        print(f"camembert_v2={camembert_path}")
        print(f"e2e_camembert_v2={args.reports / 'e2e_manual_gold_120_camembert_v2_summary.json'}")
    print(f"e2e={args.reports / 'e2e_manual_gold_120_summary.json'}")
    print(f"dashboard={dashboard_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
