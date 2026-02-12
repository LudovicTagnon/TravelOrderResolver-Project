import unittest

from src.travel_order_resolver import (
    build_place_index,
    build_place_pattern,
    resolve_order,
)


class ResolveTyposTest(unittest.TestCase):
    def test_first_letter_typo_is_recovered(self) -> None:
        mapping = {
            "strasbourg": "Strasbourg",
            "tours": "Tours",
            "lyon": "Lyon",
        }
        pattern = build_place_pattern(list(mapping.keys()))
        index, max_tokens = build_place_index(mapping)
        origin, destination = resolve_order(
            "comment aller a Tours depuis trasbourg",
            mapping,
            pattern,
            index,
            max_tokens,
        )
        self.assertEqual("Strasbourg", origin)
        self.assertEqual("Tours", destination)


if __name__ == "__main__":
    unittest.main()
