#!/usr/bin/env python3
import argparse
import csv
import json
import sys
from pathlib import Path
from typing import Callable

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
sys.path.append(str(ROOT))
sys.path.append(str(SCRIPTS))

import pathfind
from src.travel_order_resolver import (
    build_place_index,
    build_place_pattern,
    load_places,
    resolve_order,
)


def parse_input_line(line: str) -> tuple[str, str] | None:
    if "," not in line:
        return None
    sentence_id, sentence = line.split(",", 1)
    sentence_id = sentence_id.strip()
    sentence = sentence.strip()
    if not sentence_id or not sentence:
        return None
    return sentence_id, sentence


def build_summary(total: int, nlp_valid: int, path_valid: int) -> dict:
    nlp_invalid = total - nlp_valid
    path_invalid = nlp_valid - path_valid
    return {
        "total": total,
        "nlp_valid": nlp_valid,
        "nlp_invalid": nlp_invalid,
        "nlp_valid_rate": (nlp_valid / total) if total else 0.0,
        "path_valid_on_nlp_valid": path_valid,
        "path_invalid_on_nlp_valid": path_invalid,
        "path_success_rate_on_nlp_valid": (path_valid / nlp_valid) if nlp_valid else 0.0,
        "end_to_end_success": path_valid,
        "end_to_end_success_rate": (path_valid / total) if total else 0.0,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Evaluate end-to-end pipeline (NLP + pathfinding).")
    parser.add_argument("--input", type=Path, default=Path("datasets/manual/input_starter.csv"))
    parser.add_argument(
        "--nlp-backend",
        choices=["rule-based", "camembert-ft"],
        default="rule-based",
        help="NLP backend used to extract origin/destination.",
    )
    parser.add_argument("--places", type=Path, default=Path("data/places.txt"))
    parser.add_argument("--graph", type=Path, default=Path("data/graph.json"))
    parser.add_argument("--stops-index", type=Path, default=Path("data/stops_index.json"))
    parser.add_argument("--stops-areas", type=Path, default=Path("data/stops_areas.csv"))
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
    parser.add_argument("--camembert-batch-size", type=int, default=32)
    parser.add_argument("--camembert-max-length", type=int, default=64)
    parser.add_argument(
        "--output-csv",
        type=Path,
        default=Path("datasets/manual/e2e_manual_120.csv"),
    )
    parser.add_argument(
        "--summary",
        type=Path,
        default=Path("reports/e2e_manual_120_summary.json"),
    )
    args = parser.parse_args()

    required = (args.input, args.places, args.graph, args.stops_index)
    if any(not path.exists() for path in required):
        return 1

    mapping = load_places(args.places)
    place_pattern = build_place_pattern(list(mapping.keys()))
    place_index, max_place_tokens = build_place_index(mapping)
    nlp_predictor: Callable[[str], tuple[str | None, str | None]] | None = None

    if args.nlp_backend == "camembert-ft":
        if not args.origin_model_dir.exists() or not args.destination_model_dir.exists():
            print("Camembert model directories are missing.", file=sys.stderr)
            return 1
        try:
            from scripts.camembert_finetune_infer import CamembertFineTunePredictor
        except ModuleNotFoundError as exc:
            print(f"Camembert dependencies missing: {exc}", file=sys.stderr)
            return 1
        predictor = CamembertFineTunePredictor(
            origin_model_dir=args.origin_model_dir,
            destination_model_dir=args.destination_model_dir,
            batch_size=args.camembert_batch_size,
            max_length=args.camembert_max_length,
        )
        nlp_predictor = predictor.predict_sentence

    graph = pathfind.load_graph(args.graph)
    index = pathfind.load_stops_index(args.stops_index)
    stop_names = pathfind.load_stop_names(args.stops_areas)

    args.output_csv.parent.mkdir(parents=True, exist_ok=True)
    args.summary.parent.mkdir(parents=True, exist_ok=True)

    total = 0
    nlp_valid = 0
    path_valid = 0

    with args.input.open("r", encoding="utf-8") as handle, args.output_csv.open(
        "w", encoding="utf-8", newline=""
    ) as output_handle:
        writer = csv.writer(output_handle)
        writer.writerow(
            [
                "id",
                "sentence",
                "origin",
                "destination",
                "nlp_status",
                "path_status",
                "path_length",
                "path",
            ]
        )

        for raw_line in handle:
            parsed = parse_input_line(raw_line.rstrip("\n"))
            if parsed is None:
                continue
            sentence_id, sentence = parsed
            total += 1

            if nlp_predictor is not None:
                origin, destination = nlp_predictor(sentence)
            else:
                origin, destination = resolve_order(
                    sentence, mapping, place_pattern, place_index, max_place_tokens
                )
            if origin is None or destination is None:
                writer.writerow(
                    [sentence_id, sentence, "", "", "invalid", "skipped", 0, ""]
                )
                continue

            nlp_valid += 1
            found_path = pathfind.pathfind(origin, destination, graph, index)
            if not found_path:
                writer.writerow(
                    [
                        sentence_id,
                        sentence,
                        origin,
                        destination,
                        "valid",
                        "invalid",
                        0,
                        "",
                    ]
                )
                continue

            path_valid += 1
            readable_path = [stop_names.get(stop_id, stop_id) for stop_id in found_path]
            writer.writerow(
                [
                    sentence_id,
                    sentence,
                    origin,
                    destination,
                    "valid",
                    "valid",
                    len(found_path),
                    " > ".join(readable_path),
                ]
            )

    summary = build_summary(total, nlp_valid, path_valid)
    with args.summary.open("w", encoding="utf-8") as handle:
        json.dump(summary, handle, ensure_ascii=True, indent=2)

    print(json.dumps(summary, ensure_ascii=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
