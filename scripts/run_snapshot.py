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


def run_text(command: list[str]) -> str:
    return subprocess.check_output(command, text=True)


def run_and_load_json(command: list[str], output_path: Path) -> dict:
    subprocess.check_call(command)
    with output_path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def parse_key_values(text: str) -> dict[str, str]:
    result: dict[str, str] = {}
    for line in text.splitlines():
        if "=" not in line:
            continue
        key, value = line.split("=", 1)
        result[key.strip()] = value.strip()
    return result


def maybe_train_ml(model_dir: Path, datasets_dir: Path) -> None:
    if (model_dir / "origin_model.joblib").exists() and (model_dir / "dest_model.joblib").exists():
        return
    subprocess.check_call(
        [
            sys.executable,
            str(ROOT / "scripts" / "train_ml.py"),
            "--train-input",
            str(datasets_dir / "train_input.txt"),
            "--train-output",
            str(datasets_dir / "train_output.txt"),
            "--model-dir",
            str(model_dir),
        ]
    )


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate a project snapshot with key metrics.")
    parser.add_argument("--datasets", type=Path, default=ROOT / "datasets")
    parser.add_argument("--reports", type=Path, default=ROOT / "reports")
    parser.add_argument("--model-dir", type=Path, default=ROOT / "models")
    parser.add_argument("--places", type=Path, default=ROOT / "data" / "places.txt")
    parser.add_argument("--graph", type=Path, default=ROOT / "data" / "graph.json")
    parser.add_argument("--stops-index", type=Path, default=ROOT / "data" / "stops_index.json")
    parser.add_argument("--stops-areas", type=Path, default=ROOT / "data" / "stops_areas.csv")
    parser.add_argument(
        "--manual-input",
        type=Path,
        default=ROOT / "datasets" / "manual" / "input_starter.csv",
    )
    parser.add_argument(
        "--manual-output",
        type=Path,
        default=ROOT / "datasets" / "manual" / "output_gold_120.csv",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=ROOT / "reports" / "snapshot.json",
    )
    parser.add_argument(
        "--markdown-output",
        type=Path,
        default=ROOT / "reports" / "snapshot.md",
    )
    args = parser.parse_args()

    args.reports.mkdir(parents=True, exist_ok=True)
    maybe_train_ml(args.model_dir, args.datasets)

    rule_metrics = run_and_load_json(
        [
            sys.executable,
            str(ROOT / "scripts" / "run_benchmarks.py"),
            "--datasets",
            str(args.datasets),
            "--places",
            str(args.places),
            "--output",
            str(args.reports / "metrics.json"),
        ],
        args.reports / "metrics.json",
    )

    ml_metrics = run_and_load_json(
        [
            sys.executable,
            str(ROOT / "scripts" / "run_ml_benchmarks.py"),
            "--datasets",
            str(args.datasets),
            "--model-dir",
            str(args.model_dir),
            "--output",
            str(args.reports / "ml_metrics.json"),
        ],
        args.reports / "ml_metrics.json",
    )

    ml_error_dev = run_and_load_json(
        [
            sys.executable,
            str(ROOT / "scripts" / "analyze_ml_errors.py"),
            "--input",
            str(args.datasets / "dev_input.txt"),
            "--expected",
            str(args.datasets / "dev_output.txt"),
            "--model-dir",
            str(args.model_dir),
            "--output",
            str(args.reports / "ml_error_analysis_dev.json"),
            "--max-samples",
            "30",
        ],
        args.reports / "ml_error_analysis_dev.json",
    )
    ml_error_test = run_and_load_json(
        [
            sys.executable,
            str(ROOT / "scripts" / "analyze_ml_errors.py"),
            "--input",
            str(args.datasets / "test_input.txt"),
            "--expected",
            str(args.datasets / "test_output.txt"),
            "--model-dir",
            str(args.model_dir),
            "--output",
            str(args.reports / "ml_error_analysis_test.json"),
            "--max-samples",
            "30",
        ],
        args.reports / "ml_error_analysis_test.json",
    )

    manual_rule = run_json(
        [
            sys.executable,
            str(ROOT / "scripts" / "evaluate.py"),
            "--input",
            str(args.manual_input),
            "--expected",
            str(args.manual_output),
            "--places",
            str(args.places),
            "--format",
            "json",
        ]
    )
    manual_ml = run_json(
        [
            sys.executable,
            str(ROOT / "scripts" / "evaluate_ml.py"),
            "--input",
            str(args.manual_input),
            "--expected",
            str(args.manual_output),
            "--model-dir",
            str(args.model_dir),
            "--format",
            "json",
        ]
    )

    path_text = run_text(
        [
            sys.executable,
            str(ROOT / "scripts" / "validate_pathfinding.py"),
            "--graph",
            str(args.graph),
            "--stops-index",
            str(args.stops_index),
            "--triplets",
            str(args.datasets / "path_triplets.csv"),
            "--expected",
            str(args.datasets / "path_expected.csv"),
        ]
    )
    path_metrics = parse_key_values(path_text)

    e2e = run_json(
        [
            sys.executable,
            str(ROOT / "scripts" / "evaluate_end_to_end.py"),
            "--input",
            str(args.manual_input),
            "--places",
            str(args.places),
            "--graph",
            str(args.graph),
            "--stops-index",
            str(args.stops_index),
            "--stops-areas",
            str(args.stops_areas),
            "--output-csv",
            str(args.datasets / "manual" / "e2e_manual_120.csv"),
            "--summary",
            str(args.reports / "e2e_manual_120_summary.json"),
        ]
    )

    snapshot = {
        "rule_based_benchmarks": rule_metrics,
        "ml_benchmarks": ml_metrics,
        "ml_error_analysis": {
            "dev": {
                "exact_accuracy": ml_error_dev.get("exact_accuracy", 0.0),
                "origin_top_confusions": ml_error_dev.get("origin_top_confusions", [])[:5],
                "destination_top_confusions": ml_error_dev.get("destination_top_confusions", [])[:5],
            },
            "test": {
                "exact_accuracy": ml_error_test.get("exact_accuracy", 0.0),
                "origin_top_confusions": ml_error_test.get("origin_top_confusions", [])[:5],
                "destination_top_confusions": ml_error_test.get("destination_top_confusions", [])[:5],
            },
        },
        "manual_reference_rule_based": manual_rule,
        "manual_reference_ml": manual_ml,
        "pathfinding_validation": path_metrics,
        "end_to_end_manual_120": e2e,
    }

    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", encoding="utf-8") as handle:
        json.dump(snapshot, handle, ensure_ascii=True, indent=2)

    subprocess.check_call(
        [
            sys.executable,
            str(ROOT / "scripts" / "render_snapshot_md.py"),
            "--input",
            str(args.output),
            "--output",
            str(args.markdown_output),
        ]
    )

    print(f"snapshot={args.output}")
    print(f"snapshot_markdown={args.markdown_output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
