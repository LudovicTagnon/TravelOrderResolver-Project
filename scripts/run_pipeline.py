#!/usr/bin/env python3
import argparse
import csv
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
sys.path.append(str(ROOT))
sys.path.append(str(SCRIPTS))

import pathfind
from src.travel_order_resolver import (
    build_place_index,
    build_place_pattern,
    iter_input_lines,
    load_places,
    resolve_order,
)


def process_order(
    sentence_id: str,
    sentence: str,
    mapping: dict,
    place_pattern: str,
    place_index: dict[int, dict[str, list[tuple[str, str]]]],
    max_place_tokens: int,
    graph: dict,
    stops_index: dict,
    stop_names: dict,
    output_ids: bool = False,
) -> tuple[list[str], list[str], str]:
    origin, destination = resolve_order(
        sentence, mapping, place_pattern, place_index, max_place_tokens
    )

    if origin is None or destination is None:
        return [sentence_id, "INVALID", ""], [sentence_id, "INVALID", ""], "nlp_invalid"

    nlp_row = [sentence_id, origin, destination]
    route = pathfind.pathfind(origin, destination, graph, stops_index)
    if not route:
        return nlp_row, [sentence_id, "INVALID", ""], "path_invalid"

    if output_ids:
        path_row = [sentence_id] + route
    else:
        path_row = [sentence_id] + [stop_names.get(stop_id, stop_id) for stop_id in route]
    return nlp_row, path_row, "ok"


def parse_sentence_line(line: str) -> tuple[str, str] | None:
    if "," not in line:
        return None
    sentence_id, sentence = line.split(",", 1)
    sentence_id = sentence_id.strip()
    sentence = sentence.strip()
    if not sentence_id or not sentence:
        return None
    return sentence_id, sentence


def main() -> int:
    parser = argparse.ArgumentParser(description="Run NLP + pathfinding pipeline.")
    parser.add_argument("inputs", nargs="*", help="Input files, URLs, or '-' for stdin")
    parser.add_argument("--places", type=Path, default=ROOT / "data" / "places.txt")
    parser.add_argument("--graph", type=Path, default=ROOT / "data" / "graph.json")
    parser.add_argument("--stops-index", type=Path, default=ROOT / "data" / "stops_index.json")
    parser.add_argument("--stops-areas", type=Path, default=ROOT / "data" / "stops_areas.csv")
    parser.add_argument(
        "--output-nlp", type=Path, default=ROOT / "reports" / "pipeline_nlp_output.csv"
    )
    parser.add_argument(
        "--output-path", type=Path, default=ROOT / "reports" / "pipeline_path_output.csv"
    )
    parser.add_argument("--output-ids", action="store_true")
    args = parser.parse_args()

    required = (args.places, args.graph, args.stops_index)
    if any(not path.exists() for path in required):
        return 1

    mapping = load_places(args.places)
    place_pattern = build_place_pattern(list(mapping.keys()))
    place_index, max_place_tokens = build_place_index(mapping)

    graph = pathfind.load_graph(args.graph)
    stops_index = pathfind.load_stops_index(args.stops_index)
    stop_names = pathfind.load_stop_names(args.stops_areas)

    args.output_nlp.parent.mkdir(parents=True, exist_ok=True)
    args.output_path.parent.mkdir(parents=True, exist_ok=True)

    total = 0
    ok = 0
    nlp_invalid = 0
    path_invalid = 0

    with args.output_nlp.open("w", encoding="utf-8", newline="") as nlp_handle, args.output_path.open(
        "w", encoding="utf-8", newline=""
    ) as path_handle:
        nlp_writer = csv.writer(nlp_handle)
        path_writer = csv.writer(path_handle)

        for raw_line in iter_input_lines(args.inputs):
            parsed = parse_sentence_line(raw_line)
            if parsed is None:
                continue
            sentence_id, sentence = parsed
            total += 1
            nlp_row, path_row, status = process_order(
                sentence_id,
                sentence,
                mapping,
                place_pattern,
                place_index,
                max_place_tokens,
                graph,
                stops_index,
                stop_names,
                args.output_ids,
            )
            nlp_writer.writerow(nlp_row)
            path_writer.writerow(path_row)
            if status == "ok":
                ok += 1
            elif status == "nlp_invalid":
                nlp_invalid += 1
            else:
                path_invalid += 1

    print(f"total={total}")
    print(f"ok={ok}")
    print(f"nlp_invalid={nlp_invalid}")
    print(f"path_invalid={path_invalid}")
    print(f"output_nlp={args.output_nlp}")
    print(f"output_path={args.output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
