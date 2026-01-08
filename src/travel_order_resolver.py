#!/usr/bin/env python3
import argparse
import re
import sys
import urllib.request
from typing import Iterable
import unicodedata
from pathlib import Path


def normalize(text: str) -> str:
    text = text.lower()
    text = unicodedata.normalize("NFD", text)
    text = "".join(ch for ch in text if unicodedata.category(ch) != "Mn")
    text = re.sub(r"[^a-z0-9\s-]", " ", text)
    text = text.replace("-", " ")
    text = re.sub(r"\s+", " ", text).strip()
    return text


def load_places(path: Path) -> dict:
    variants = {}
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            name = line.strip()
            if not name or name.startswith("#"):
                continue
            variant = normalize(name)
            variants[variant] = name
    return variants


def build_place_pattern(variants: list[str]) -> str:
    escaped = sorted(variants, key=len, reverse=True)
    patterns = []
    for value in escaped:
        pattern = re.escape(value).replace("\\ ", r"\s+")
        patterns.append(pattern)
    combined = "|".join(patterns)
    return rf"(?<!\w)(?:{combined})(?!\w)"


def extract_candidates(
    sentence_norm: str,
    cue_pattern: str,
    place_pattern: str,
    mapping: dict,
    max_gap_tokens: int = 3,
) -> list:
    gap = rf"(?:\s+\w+){{0,{max_gap_tokens}}}"
    regex = re.compile(rf"(?:{cue_pattern}){gap}\s+(?P<place>{place_pattern})")
    matches = []
    for match in regex.finditer(sentence_norm):
        raw = re.sub(r"\s+", " ", match.group("place")).strip()
        canonical = mapping.get(raw)
        if canonical:
            matches.append((match.start("place"), canonical))
    return matches


def collect_candidates(
    sentence_norm: str,
    cue_specs: list[tuple[str, int]],
    place_pattern: str,
    mapping: dict,
) -> list:
    candidates = []
    seen = set()
    for cue_pattern, max_gap_tokens in cue_specs:
        for pos, place in extract_candidates(
            sentence_norm, cue_pattern, place_pattern, mapping, max_gap_tokens
        ):
            key = (pos, place)
            if key not in seen:
                candidates.append((pos, place))
                seen.add(key)
    return sorted(candidates, key=lambda item: item[0])


def extract_places(sentence_norm: str, place_pattern: str, mapping: dict) -> list:
    regex = re.compile(rf"(?P<place>{place_pattern})")
    matches = []
    for match in regex.finditer(sentence_norm):
        raw = re.sub(r"\s+", " ", match.group("place")).strip()
        canonical = mapping.get(raw)
        if canonical:
            matches.append((match.start(), canonical))
    return matches


def resolve_order(sentence: str, mapping: dict, place_pattern: str) -> tuple:
    sentence_norm = normalize(sentence)
    origin_specs = [
        (r"\bdepuis\b", 3),
        (r"\ben\s+partant\s+de\b", 1),
        (r"\bpartant\s+de\b", 1),
        (r"\bde\b", 1),
    ]
    dest_specs = [
        (r"\ba\b", 1),
        (r"\bvers\b", 1),
        (r"\bpour\b", 1),
        (r"\bjusqu\s*a\b", 1),
    ]
    fallback_markers = {
        "je",
        "veux",
        "voudrais",
        "souhaite",
        "aller",
        "rendre",
        "gare",
        "billet",
        "partir",
        "partant",
        "depuis",
        "faire",
    }

    origin_candidates = collect_candidates(sentence_norm, origin_specs, place_pattern, mapping)
    dest_candidates = collect_candidates(sentence_norm, dest_specs, place_pattern, mapping)
    all_places = extract_places(sentence_norm, place_pattern, mapping)

    ordered = []
    for _, place in sorted(all_places, key=lambda item: item[0]):
        if place not in ordered:
            ordered.append(place)

    origin = origin_candidates[-1][1] if origin_candidates else None
    destination = dest_candidates[-1][1] if dest_candidates else None
    fallback_allowed = bool(origin_candidates or dest_candidates) or bool(
        set(sentence_norm.split()) & fallback_markers
    )

    if origin is None and ordered and fallback_allowed:
        origin = ordered[0]

    if destination is None and fallback_allowed:
        if origin is None:
            if len(ordered) >= 2:
                destination = ordered[1]
        else:
            for place in ordered:
                if place != origin:
                    destination = place
                    break

    if not origin or not destination or origin == destination:
        return None, None

    return origin, destination


def read_url_lines(url: str) -> Iterable[str]:
    with urllib.request.urlopen(url) as response:
        content = response.read().decode("utf-8", errors="replace")
    for line in content.splitlines():
        yield line


def iter_input_lines(inputs: list[str]) -> Iterable[str]:
    if not inputs:
        for line in sys.stdin:
            yield line.rstrip("\n")
        return
    for item in inputs:
        if item == "-":
            for line in sys.stdin:
                yield line.rstrip("\n")
            continue
        if item.startswith("http://") or item.startswith("https://"):
            for line in read_url_lines(item):
                yield line.rstrip("\n")
            continue
        path = Path(item)
        with path.open("r", encoding="utf-8") as handle:
            for line in handle:
                yield line.rstrip("\n")


def main() -> int:
    default_places = Path(__file__).resolve().parents[1] / "data" / "places.txt"
    parser = argparse.ArgumentParser(description="Extract origin and destination from travel orders.")
    parser.add_argument("inputs", nargs="*", help="Input files, URLs, or '-' for stdin")
    parser.add_argument("--places", type=Path, default=default_places, help="Path to places list")
    args = parser.parse_args()

    if not args.places.exists():
        print(f"Places file not found: {args.places}", file=sys.stderr)
        return 1

    mapping = load_places(args.places)
    if not mapping:
        print("Places list is empty.", file=sys.stderr)
        return 1

    place_pattern = build_place_pattern(list(mapping.keys()))

    for line in iter_input_lines(args.inputs):
        if not line.strip():
            continue
        if "," not in line:
            continue
        sentence_id, sentence = line.split(",", 1)
        origin, destination = resolve_order(sentence, mapping, place_pattern)
        if origin and destination:
            print(f"{sentence_id},{origin},{destination}")
        else:
            print(f"{sentence_id},INVALID,")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
