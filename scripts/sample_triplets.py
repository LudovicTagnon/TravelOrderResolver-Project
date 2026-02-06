#!/usr/bin/env python3
import argparse
import csv
import json
import random
from collections import deque
from pathlib import Path


def sanitize(value: str) -> str:
    return value.replace(",", " ").strip()


def load_graph(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as handle:
        data = json.load(handle)
    return data.get("edges", {})


def load_stop_names(path: Path) -> dict:
    mapping = {}
    with path.open("r", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            stop_id = row.get("stop_id")
            stop_name = row.get("stop_name")
            if stop_id and stop_name and stop_id not in mapping:
                mapping[stop_id] = sanitize(stop_name)
    return mapping


def bfs(graph: dict, source: str, target: str, max_depth: int | None = None) -> list[str] | None:
    queue = deque([(source, 0)])
    visited = {source: None}

    while queue:
        current, depth = queue.popleft()
        if current == target:
            path = [current]
            while visited[current] is not None:
                current = visited[current]
                path.append(current)
            return list(reversed(path))
        if max_depth is not None and depth >= max_depth:
            continue
        for neighbor in graph.get(current, []):
            if neighbor not in visited:
                visited[neighbor] = current
                queue.append((neighbor, depth + 1))
    return None


def main() -> int:
    parser = argparse.ArgumentParser(description="Sample connected triplets from a graph.")
    parser.add_argument("--graph", type=Path, default=Path("data/graph.json"))
    parser.add_argument("--stops-areas", type=Path, default=Path("data/stops_areas.csv"))
    parser.add_argument("--output-triplets", type=Path, default=Path("datasets/path_triplets.csv"))
    parser.add_argument("--output-expected", type=Path, default=Path("datasets/path_expected.csv"))
    parser.add_argument("--count", type=int, default=50)
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--max-depth", type=int, default=8)
    args = parser.parse_args()

    if not args.graph.exists() or not args.stops_areas.exists():
        print("Missing graph or stops_areas file")
        return 1

    graph = load_graph(args.graph)
    stop_names = load_stop_names(args.stops_areas)
    nodes = [node for node in graph.keys() if node in stop_names]
    if len(nodes) < 2:
        print("Not enough nodes for sampling")
        return 1

    rng = random.Random(args.seed)
    triplets = []
    expected = []
    attempts = 0

    while len(triplets) < args.count and attempts < args.count * 20:
        attempts += 1
        origin = rng.choice(nodes)
        destination = rng.choice(nodes)
        if origin == destination:
            continue
        path = bfs(graph, origin, destination, max_depth=args.max_depth)
        if not path:
            continue
        sentence_id = str(len(triplets) + 1)
        triplets.append((sentence_id, stop_names[origin], stop_names[destination]))
        expected.append((sentence_id, path))

    if not triplets:
        print("No triplets generated")
        return 1

    args.output_triplets.parent.mkdir(parents=True, exist_ok=True)
    with args.output_triplets.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle)
        for row in triplets:
            writer.writerow(row)

    with args.output_expected.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle)
        for sentence_id, path in expected:
            writer.writerow([sentence_id] + path)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
