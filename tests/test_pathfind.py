import os
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
sys.path.append(str(SCRIPTS))

import pathfind


class PathfindTest(unittest.TestCase):
    def setUp(self) -> None:
        fixtures = ROOT / "tests" / "fixtures"
        self.graph = pathfind.load_graph(fixtures / "graph.json")
        self.index = pathfind.load_stops_index(fixtures / "stops_index.json")
        self.stop_names = pathfind.load_stop_names(fixtures / "stops_areas.csv")

    def test_pathfind_simple(self) -> None:
        path = pathfind.pathfind("Gare A", "Gare C", self.graph, self.index)
        self.assertEqual(["StopArea:A", "StopArea:B", "StopArea:C"], path)

    def test_pathfind_invalid(self) -> None:
        path = pathfind.pathfind("Gare A", "Gare X", self.graph, self.index)
        self.assertIsNone(path)

    def test_readable_output(self) -> None:
        path = pathfind.pathfind("Gare A", "Gare C", self.graph, self.index)
        readable = [self.stop_names.get(stop_id, stop_id) for stop_id in path]
        self.assertEqual(["Gare A", "Gare B", "Gare C"], readable)

    def test_resolve_stop_ids_prefix_fallback(self) -> None:
        index = {
            "paris gare de lyon": {"stop_ids": ["StopArea:PARIS_LYON"]},
            "paris montparnasse": {"stop_ids": ["StopArea:PARIS_MONTP"]},
        }
        ids = pathfind.resolve_stop_ids(index, "Paris")
        self.assertEqual(
            {"StopArea:PARIS_LYON", "StopArea:PARIS_MONTP"},
            set(ids),
        )

    def test_resolve_stop_ids_saint_abbreviation_fallback(self) -> None:
        index = {
            "st etienne ch tcrx": {"stop_ids": ["StopArea:ST_ETIENNE"]},
        }
        ids = pathfind.resolve_stop_ids(index, "Saint-Etienne")
        self.assertEqual(["StopArea:ST_ETIENNE"], ids)


if __name__ == "__main__":
    unittest.main()
