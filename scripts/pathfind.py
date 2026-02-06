#!/usr/bin/env python3
import argparse
import csv
import json
import sys
from collections import deque
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.append(str(ROOT))

from src.travel_order_resolver import normalize


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
    entry = index.get(key)
    if not entry:
        return []
    return entry.get("stop_ids", [])


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
