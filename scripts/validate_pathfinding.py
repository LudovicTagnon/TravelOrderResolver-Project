#!/usr/bin/env python3
import argparse
import csv
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.append(str(ROOT))

GENERIC_TOKENS = {"gare", "station", "halte", "arret", "stop"}


def load_graph(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle).get("edges", {})


def load_index(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def normalize(name: str) -> str:
    from src.travel_order_resolver import normalize as normalize_fn

    return normalize_fn(name)


def resolve_stop_ids(index: dict, name: str) -> list[str]:
    from src.travel_order_resolver import levenshtein, max_distance

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

    for variant in key_variants:
        for candidate_key, candidate_entry in index.items():
            if variant in candidate_key:
                matched_ids.update(candidate_entry.get("stop_ids", []))
    return sorted(matched_ids)


def bfs(graph: dict, sources: list[str], targets: set[str]) -> list[str] | None:
    from collections import deque

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


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate pathfinding against expected paths.")
    parser.add_argument("--graph", type=Path, default=Path("data/graph.json"))
    parser.add_argument("--stops-index", type=Path, default=Path("data/stops_index.json"))
    parser.add_argument("--triplets", type=Path, default=Path("datasets/path_triplets.csv"))
    parser.add_argument("--expected", type=Path, default=Path("datasets/path_expected.csv"))
    args = parser.parse_args()

    if not args.graph.exists() or not args.stops_index.exists():
        return 1

    graph = load_graph(args.graph)
    index = load_index(args.stops_index)

    expected_map = {}
    with args.expected.open("r", encoding="utf-8") as handle:
        reader = csv.reader(handle)
        for row in reader:
            if len(row) < 2:
                continue
            expected_map[row[0]] = row[1:]

    total = 0
    correct = 0
    with args.triplets.open("r", encoding="utf-8") as handle:
        reader = csv.reader(handle)
        for row in reader:
            if len(row) != 3:
                continue
            sentence_id, origin, destination = row
            sources = resolve_stop_ids(index, origin)
            targets = set(resolve_stop_ids(index, destination))
            if not sources or not targets:
                total += 1
                continue
            path = bfs(graph, sources, targets)
            total += 1
            if path and expected_map.get(sentence_id) == path:
                correct += 1

    accuracy = (correct / total) if total else 0.0
    print(f"total={total}")
    print(f"correct={correct}")
    print(f"accuracy={accuracy:.3f}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
