#!/usr/bin/env python3
import argparse
import csv
import json
import sys
from collections import deque
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.append(str(ROOT))

from src.travel_order_resolver import levenshtein, max_distance, normalize

GENERIC_TOKENS = {"gare", "station", "halte", "arret", "stop"}


def load_graph(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as handle:
        data = json.load(handle)
    return data.get("edges", {})


def load_stops_index(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def load_stop_names(path: Path) -> dict:
    if not path.exists():
        return {}
    mapping = {}
    with path.open("r", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            stop_id = row.get("stop_id")
            stop_name = row.get("stop_name")
            if stop_id and stop_name and stop_id not in mapping:
                mapping[stop_id] = stop_name
    return mapping


def bfs(graph: dict, sources: list[str], targets: set[str]) -> list[str] | None:
    queue = deque(sources)
    visited = {source: None for source in sources}

    while queue:
        current = queue.popleft()
        if current in targets:
            path = [current]
            while visited[current] is not None:
                current = visited[current]
                path.append(current)
            return list(reversed(path))
        for neighbor in graph.get(current, []):
            if neighbor not in visited:
                visited[neighbor] = current
                queue.append(neighbor)
    return None


def resolve_stop_ids(index: dict, name: str) -> list[str]:
    key = normalize(name)
    if not key:
        return []

    key_variants = {key}
    if "saint " in key:
        key_variants.add(key.replace("saint ", "st "))
    if "st " in key:
        key_variants.add(key.replace("st ", "saint "))

    matched_ids = set()
    for variant in key_variants:
        entry = index.get(variant)
        if entry:
            matched_ids.update(entry.get("stop_ids", []))

    if matched_ids:
        return sorted(matched_ids)

    for variant in key_variants:
        prefix = f"{variant} "
        for candidate_key, candidate_entry in index.items():
            if candidate_key.startswith(prefix):
                matched_ids.update(candidate_entry.get("stop_ids", []))

    if matched_ids:
        return sorted(matched_ids)

    # Fuzzy fallback for noisy stop names (encoding glitches, abbreviations).
    for variant in key_variants:
        variant_tokens = variant.split()
        if not variant_tokens:
            continue
        informative_tokens = [
            token for token in variant_tokens if len(token) >= 3 and token not in GENERIC_TOKENS
        ]
        if not informative_tokens:
            continue
        token_count = len(variant_tokens)
        best_distance = None
        best_ids = set()
        for candidate_key, candidate_entry in index.items():
            candidate_tokens = candidate_key.split()
            if len(candidate_tokens) < token_count:
                continue
            candidate_prefix = " ".join(candidate_tokens[:token_count])
            distance = levenshtein(variant, candidate_prefix)
            if distance > max_distance(variant):
                continue
            if best_distance is None or distance < best_distance:
                best_distance = distance
                best_ids = set(candidate_entry.get("stop_ids", []))
            elif distance == best_distance:
                best_ids.update(candidate_entry.get("stop_ids", []))
        matched_ids.update(best_ids)

    if matched_ids:
        return sorted(matched_ids)

    # Last-resort contains fallback.
    for variant in key_variants:
        for candidate_key, candidate_entry in index.items():
            if variant in candidate_key:
                matched_ids.update(candidate_entry.get("stop_ids", []))

    if matched_ids:
        return sorted(matched_ids)

    return []


def pathfind(origin: str, destination: str, graph: dict, index: dict) -> list[str] | None:
    sources = resolve_stop_ids(index, origin)
    targets = set(resolve_stop_ids(index, destination))
    if not sources or not targets:
        return None
    return bfs(graph, sources, targets)


def pathfind_ids(origin: str, destination: str, graph: dict) -> list[str] | None:
    return bfs(graph, [origin], {destination})


def iter_inputs(path: Path | None):
    if path is None:
        for line in sys.stdin:
            yield line.rstrip("\n")
        return
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            yield line.rstrip("\n")


def main() -> int:
    parser = argparse.ArgumentParser(description="Pathfinding on a stop graph.")
    parser.add_argument("--graph", type=Path, default=Path("data/graph.json"))
    parser.add_argument("--stops-index", type=Path, default=Path("data/stops_index.json"))
    parser.add_argument("--stops-areas", type=Path, default=Path("data/stops_areas.csv"))
    parser.add_argument("--input", type=Path, default=None)
    parser.add_argument("--output-ids", action="store_true")
    parser.add_argument("--ids", action="store_true")
    args = parser.parse_args()

    if not args.graph.exists() or not args.stops_index.exists():
        return 1

    graph = load_graph(args.graph)
    index = load_stops_index(args.stops_index)
    stop_names = load_stop_names(args.stops_areas)

    for line in iter_inputs(args.input):
        if not line or "," not in line:
            continue
        parts = line.split(",", 2)
        if len(parts) != 3:
            continue
        sentence_id, origin, destination = parts
        if args.ids:
            path = pathfind_ids(origin, destination, graph)
        else:
            path = pathfind(origin, destination, graph, index)
        if not path:
            print(f"{sentence_id},INVALID,")
            continue
        if args.output_ids:
            print(f"{sentence_id}," + ",".join(path))
        else:
            readable = [stop_names.get(stop_id, stop_id) for stop_id in path]
            print(f"{sentence_id}," + ",".join(readable))

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
