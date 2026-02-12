#!/usr/bin/env python3
import argparse
import csv
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.append(str(ROOT))


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
    key = normalize(name)
    if not key:
        return []
    entry = index.get(key)
    if not entry:
        matched_ids = set()
        prefix = f"{key} "
        for candidate_key, candidate_entry in index.items():
            if candidate_key.startswith(prefix):
                matched_ids.update(candidate_entry.get("stop_ids", []))
        return sorted(matched_ids)
    return entry.get("stop_ids", [])


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
