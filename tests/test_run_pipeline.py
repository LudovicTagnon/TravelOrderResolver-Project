import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
sys.path.append(str(SCRIPTS))

import pathfind
import run_pipeline


class RunPipelineTest(unittest.TestCase):
    def setUp(self) -> None:
        fixtures = ROOT / "tests" / "fixtures"
        self.graph = pathfind.load_graph(fixtures / "graph.json")
        self.stops_index = pathfind.load_stops_index(fixtures / "stops_index.json")
        self.stop_names = pathfind.load_stop_names(fixtures / "stops_areas.csv")
        self.mapping = {
            "gare a": "Gare A",
            "gare b": "Gare B",
            "gare c": "Gare C",
        }
        self.place_pattern = run_pipeline.build_place_pattern(list(self.mapping.keys()))
        self.place_index, self.max_place_tokens = run_pipeline.build_place_index(self.mapping)

    def test_process_order_valid(self) -> None:
        nlp_row, path_row, status = run_pipeline.process_order(
            sentence_id="1",
            sentence="aller de gare a vers gare c",
            mapping=self.mapping,
            place_pattern=self.place_pattern,
            place_index=self.place_index,
            max_place_tokens=self.max_place_tokens,
            graph=self.graph,
            stops_index=self.stops_index,
            stop_names=self.stop_names,
            output_ids=False,
        )
        self.assertEqual("ok", status)
        self.assertEqual(["1", "Gare A", "Gare C"], nlp_row)
        self.assertEqual(["1", "Gare A", "Gare B", "Gare C"], path_row)

    def test_process_order_invalid(self) -> None:
        nlp_row, path_row, status = run_pipeline.process_order(
            sentence_id="2",
            sentence="une phrase sans trajet",
            mapping=self.mapping,
            place_pattern=self.place_pattern,
            place_index=self.place_index,
            max_place_tokens=self.max_place_tokens,
            graph=self.graph,
            stops_index=self.stops_index,
            stop_names=self.stop_names,
            output_ids=False,
        )
        self.assertEqual("nlp_invalid", status)
        self.assertEqual(["2", "INVALID", ""], nlp_row)
        self.assertEqual(["2", "INVALID", ""], path_row)

    def test_process_order_with_custom_predictor_valid(self) -> None:
        nlp_row, path_row, status = run_pipeline.process_order(
            sentence_id="3",
            sentence="texte quelconque",
            mapping=self.mapping,
            place_pattern=self.place_pattern,
            place_index=self.place_index,
            max_place_tokens=self.max_place_tokens,
            graph=self.graph,
            stops_index=self.stops_index,
            stop_names=self.stop_names,
            output_ids=False,
            nlp_predictor=lambda _: ("Gare A", "Gare C"),
        )
        self.assertEqual("ok", status)
        self.assertEqual(["3", "Gare A", "Gare C"], nlp_row)
        self.assertEqual(["3", "Gare A", "Gare B", "Gare C"], path_row)

    def test_process_order_with_custom_predictor_invalid(self) -> None:
        nlp_row, path_row, status = run_pipeline.process_order(
            sentence_id="4",
            sentence="texte quelconque",
            mapping=self.mapping,
            place_pattern=self.place_pattern,
            place_index=self.place_index,
            max_place_tokens=self.max_place_tokens,
            graph=self.graph,
            stops_index=self.stops_index,
            stop_names=self.stop_names,
            output_ids=False,
            nlp_predictor=lambda _: (None, None),
        )
        self.assertEqual("nlp_invalid", status)
        self.assertEqual(["4", "INVALID", ""], nlp_row)
        self.assertEqual(["4", "INVALID", ""], path_row)


if __name__ == "__main__":
    unittest.main()
