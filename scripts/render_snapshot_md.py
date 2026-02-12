#!/usr/bin/env python3
import argparse
import json
from pathlib import Path


def pct(value: float) -> str:
    return f"{value * 100:.1f}%"


def main() -> int:
    parser = argparse.ArgumentParser(description="Render snapshot JSON into a Markdown summary.")
    parser.add_argument("--input", type=Path, default=Path("reports/snapshot.json"))
    parser.add_argument("--output", type=Path, default=Path("reports/snapshot.md"))
    args = parser.parse_args()

    if not args.input.exists():
        return 1

    with args.input.open("r", encoding="utf-8") as handle:
        data = json.load(handle)

    rule = data.get("rule_based_benchmarks", {})
    ml = data.get("ml_benchmarks", {})
    manual_rule = data.get("manual_prefill_rule_based", {})
    manual_ml = data.get("manual_prefill_ml", {})
    path = data.get("pathfinding_validation", {})
    e2e = data.get("end_to_end_manual_120", {})

    lines = [
        "# Snapshot Projet",
        "",
        "## NLP rule-based (train/dev/test)",
        f"- Train accuracy: `{pct(rule.get('train', {}).get('accuracy', 0.0))}`",
        f"- Dev accuracy: `{pct(rule.get('dev', {}).get('accuracy', 0.0))}`",
        f"- Test accuracy: `{pct(rule.get('test', {}).get('accuracy', 0.0))}`",
        "",
        "## NLP baseline ML (train/dev/test)",
        f"- Train accuracy: `{pct(ml.get('train', {}).get('accuracy', 0.0))}`",
        f"- Dev accuracy: `{pct(ml.get('dev', {}).get('accuracy', 0.0))}`",
        f"- Test accuracy: `{pct(ml.get('test', {}).get('accuracy', 0.0))}`",
        "",
        "## Manuel 120 (prefill technique)",
        f"- Rule-based accuracy: `{pct(manual_rule.get('accuracy', 0.0))}`",
        f"- ML accuracy: `{pct(manual_ml.get('accuracy', 0.0))}`",
        "",
        "## Pathfinding",
        f"- Validation echantillon: `{path.get('correct', '?')}/{path.get('total', '?')}` (`{path.get('accuracy', '?')}`)",
        "",
        "## End-to-end (manuel 120)",
        f"- NLP valides: `{e2e.get('nlp_valid', 0)}/{e2e.get('total', 0)}` ({pct(e2e.get('nlp_valid_rate', 0.0))})",
        f"- Pathfinding sur NLP valides: `{e2e.get('path_valid_on_nlp_valid', 0)}/{e2e.get('nlp_valid', 0)}` ({pct(e2e.get('path_success_rate_on_nlp_valid', 0.0))})",
        f"- Succes global: `{e2e.get('end_to_end_success', 0)}/{e2e.get('total', 0)}` ({pct(e2e.get('end_to_end_success_rate', 0.0))})",
        "",
    ]

    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", encoding="utf-8") as handle:
        handle.write("\n".join(lines))

    print(f"markdown={args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
