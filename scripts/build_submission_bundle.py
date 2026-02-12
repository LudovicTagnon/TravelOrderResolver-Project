#!/usr/bin/env python3
import argparse
import hashlib
import json
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


DEFAULT_FILES = [
    "README.md",
    "docs/report_draft.md",
    "docs/coverage_matrix.md",
    "reports/snapshot.md",
    "reports/snapshot.json",
    "reports/manual_gold_dashboard.json",
    "reports/manual_gold_metrics_rule_based.json",
    "reports/manual_gold_metrics_ml.json",
    "reports/e2e_manual_gold_120_summary.json",
    "reports/spacy_camembert_metrics.json",
    "reports/spacy_camembert_summary.md",
    "reports/camembert_finetune_metrics.json",
    "reports/camembert_finetune_summary.md",
    "reports/pathfinding_metrics.txt",
    "reports/ml_error_analysis_dev.json",
    "reports/ml_error_analysis_test.json",
    "datasets/manual/output_gold_120.csv",
    "datasets/manual/e2e_manual_gold_120.csv",
    "students_project/sample_pipeline_nlp_output.txt",
    "students_project/sample_pipeline_path_output.txt",
]


def sha256_file(path: Path) -> str:
    hasher = hashlib.sha256()
    with path.open("rb") as handle:
        while True:
            chunk = handle.read(1024 * 1024)
            if not chunk:
                break
            hasher.update(chunk)
    return hasher.hexdigest()


def copy_file(src: Path, bundle_root: Path) -> dict | None:
    if not src.exists() or not src.is_file():
        return None
    relative = src.relative_to(ROOT)
    target = bundle_root / relative
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, target)
    return {
        "path": str(relative),
        "size_bytes": src.stat().st_size,
        "sha256": sha256_file(src),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Build a ready-to-submit bundle directory.")
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=ROOT / "deliverables" / "submission_bundle",
    )
    parser.add_argument(
        "--manifest",
        type=Path,
        default=ROOT / "deliverables" / "submission_bundle" / "manifest.json",
    )
    parser.add_argument(
        "--include",
        nargs="*",
        default=DEFAULT_FILES,
        help="Repository-relative files to include in the bundle.",
    )
    args = parser.parse_args()

    bundle_root = args.output_dir.resolve()
    manifest_path = args.manifest.resolve()
    if bundle_root.exists():
        shutil.rmtree(bundle_root)
    bundle_root.mkdir(parents=True, exist_ok=True)

    included = []
    missing = []
    for relative in args.include:
        src = ROOT / relative
        entry = copy_file(src, bundle_root)
        if entry is None:
            missing.append(relative)
        else:
            included.append(entry)

    manifest = {
        "bundle_root": str(bundle_root.relative_to(ROOT)),
        "file_count": len(included),
        "files": included,
        "missing": missing,
    }

    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    with manifest_path.open("w", encoding="utf-8") as handle:
        json.dump(manifest, handle, ensure_ascii=True, indent=2)

    print(f"bundle={bundle_root}")
    print(f"manifest={manifest_path}")
    print(f"included={len(included)}")
    print(f"missing={len(missing)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
