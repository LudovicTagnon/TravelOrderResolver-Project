#!/usr/bin/env python3
import argparse
import re
import sys
import urllib.request
from typing import Iterable
import unicodedata
from pathlib import Path
from typing import Iterable


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
            if "|" in name:
                alias, canonical = [part.strip() for part in name.split("|", 1)]
            else:
                alias = name
                canonical = name
            if not alias or not canonical:
                continue
            variant = normalize(alias)
            variants[variant] = canonical
    return variants


def build_place_pattern(variants: list[str]) -> str:
    escaped = sorted(variants, key=len, reverse=True)
    patterns = []
    for value in escaped:
        pattern = re.escape(value).replace("\\ ", r"\s+")
        patterns.append(pattern)
    combined = "|".join(patterns)
    return rf"(?<!\w)(?:{combined})(?!\w)"


def build_place_index(mapping: dict) -> tuple[dict[int, dict[str, list[tuple[str, str]]]], int]:
    index = {}
    max_tokens = 1
    for variant, canonical in mapping.items():
        tokens = variant.split()
        length = len(tokens)
        max_tokens = max(max_tokens, length)
        if length not in index:
            index[length] = {"_all": []}
        index[length]["_all"].append((variant, canonical))
        first_char = tokens[0][0] if tokens and tokens[0] else ""
        index[length].setdefault(first_char, []).append((variant, canonical))
    return index, max_tokens


def tokenize_with_positions(sentence_norm: str) -> list[tuple[str, int, int]]:
    return [
        (match.group(0), match.start(), match.end())
        for match in re.finditer(r"\w+", sentence_norm)
    ]


def max_distance(value: str) -> int:
    length = len(value)
    if length <= 4:
        return 0
    if length <= 6:
        return 1
    if length <= 9:
        return 2
    return 3


def levenshtein(a: str, b: str) -> int:
    if a == b:
        return 0
    rows = len(a) + 1
    cols = len(b) + 1
    distance = [[0] * cols for _ in range(rows)]
    for i in range(rows):
        distance[i][0] = i
    for j in range(cols):
        distance[0][j] = j
    for i in range(1, rows):
        for j in range(1, cols):
            cost = 0 if a[i - 1] == b[j - 1] else 1
            distance[i][j] = min(
                distance[i - 1][j] + 1,
                distance[i][j - 1] + 1,
                distance[i - 1][j - 1] + cost,
            )
            if (
                i > 1
                and j > 1
                and a[i - 1] == b[j - 2]
                and a[i - 2] == b[j - 1]
            ):
                distance[i][j] = min(distance[i][j], distance[i - 2][j - 2] + 1)
    return distance[-1][-1]


def extract_candidates(
    sentence_norm: str,
    cue_pattern: str,
    place_pattern: str,
    mapping: dict,
    max_gap_tokens: int = 3,
    blocked_spans: list[tuple[int, int]] | None = None,
) -> list:
    gap = rf"(?:\s+\w+){{0,{max_gap_tokens}}}"
    regex = re.compile(rf"(?:{cue_pattern}){gap}\s+(?P<place>{place_pattern})")
    matches = []
    for match in regex.finditer(sentence_norm):
        if blocked_spans and is_in_spans(match.start(), blocked_spans):
            continue
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
    blocked_spans: list[tuple[int, int]] | None = None,
) -> list:
    candidates = []
    seen = set()
    for cue_pattern, max_gap_tokens in cue_specs:
        for pos, place in extract_candidates(
            sentence_norm,
            cue_pattern,
            place_pattern,
            mapping,
            max_gap_tokens,
            blocked_spans,
        ):
            key = (pos, place)
            if key not in seen:
                candidates.append((pos, place))
                seen.add(key)
    return sorted(candidates, key=lambda item: item[0])


def collect_fuzzy_candidates(
    sentence_norm: str,
    cue_specs: list[tuple[str, int]],
    place_index: dict[int, dict[str, list[tuple[str, str]]]],
    max_place_tokens: int,
    blocked_spans: list[tuple[int, int]] | None = None,
) -> list:
    candidates = []
    seen = set()
    tokens = tokenize_with_positions(sentence_norm)
    if not tokens:
        return candidates

    for cue_pattern, _ in cue_specs:
        regex = re.compile(cue_pattern)
        for match in regex.finditer(sentence_norm):
            if blocked_spans and is_in_spans(match.start(), blocked_spans):
                continue
            token_index = None
            for idx, (_, start, _) in enumerate(tokens):
                if start >= match.end():
                    token_index = idx
                    break
            if token_index is None:
                continue
            best = None
            for length in range(1, max_place_tokens + 1):
                if token_index + length > len(tokens):
                    break
                candidate_tokens = tokens[token_index : token_index + length]
                candidate = " ".join(token for token, _, _ in candidate_tokens)
                first_char = candidate[0] if candidate else ""
                buckets = place_index.get(length, {})
                variants = buckets.get(first_char) or buckets.get("_all", [])
                for variant, canonical in variants:
                    distance = levenshtein(candidate, variant)
                    if distance > max_distance(variant):
                        continue
                    if best is None or distance < best[2]:
                        best = (
                            candidate_tokens[0][1],
                            canonical,
                            distance,
                        )
            if best is None:
                continue
            key = (best[0], best[1])
            if key not in seen:
                candidates.append((best[0], best[1]))
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


def extract_places_fuzzy(
    sentence_norm: str,
    place_index: dict[int, dict[str, list[tuple[str, str]]]],
    max_place_tokens: int,
) -> list:
    tokens = tokenize_with_positions(sentence_norm)
    matches = []
    seen = set()
    for idx in range(len(tokens)):
        best = None
        for length in range(1, max_place_tokens + 1):
            if idx + length > len(tokens):
                break
            candidate_tokens = tokens[idx : idx + length]
            candidate = " ".join(token for token, _, _ in candidate_tokens)
            first_char = candidate[0] if candidate else ""
            buckets = place_index.get(length, {})
            variants = buckets.get(first_char) or buckets.get("_all", [])
            for variant, canonical in variants:
                distance = levenshtein(candidate, variant)
                if distance > max_distance(variant):
                    continue
                if best is None or distance < best[2]:
                    best = (candidate_tokens[0][1], canonical, distance)
        if best is None:
            continue
        key = (best[0], best[1])
        if key not in seen:
            matches.append((best[0], best[1]))
            seen.add(key)
    return sorted(matches, key=lambda item: item[0])


def extract_place_spans(sentence_norm: str, place_pattern: str) -> list[tuple[int, int]]:
    regex = re.compile(rf"(?P<place>{place_pattern})")
    return [(match.start("place"), match.end("place")) for match in regex.finditer(sentence_norm)]


def is_in_spans(position: int, spans: list[tuple[int, int]]) -> bool:
    for start, end in spans:
        if start <= position < end:
            return True
    return False


def resolve_order(
    sentence: str,
    mapping: dict,
    place_pattern: str,
    place_index: dict[int, dict[str, list[tuple[str, str]]]] | None = None,
    max_place_tokens: int | None = None,
) -> tuple:
    sentence_norm = normalize(sentence)
    origin_specs = [
        (r"\bdepuis\b", 3),
        (r"\ben\s+partant\s+de\b", 1),
        (r"\bpartant\s+de\b", 1),
        (r"\bdepart\b", 1),
        (r"\bde\b", 1),
    ]
    dest_specs = [
        (r"\ba\b", 1),
        (r"\bvers\b", 1),
        (r"\bpour\b", 1),
        (r"\bjusqu\s*a\b", 1),
        (r"\bdestination\b", 1),
    ]
    fallback_markers = {
        "je",
        "veux",
        "voudrais",
        "souhaite",
        "aller",
        "rendre",
        "train",
        "trains",
        "trajet",
        "depart",
        "destination",
        "besoin",
        "gare",
        "billet",
        "partir",
        "partant",
        "depuis",
        "faire",
    }
    english_markers = {"from", "to", "going", "any"}
    french_markers = {
        "depuis",
        "vers",
        "pour",
        "aller",
        "rendre",
        "billet",
        "partir",
        "partant",
        "gare",
        "trajet",
        "depart",
        "destination",
        "besoin",
        "voudrais",
        "souhaite",
    }

    place_spans = extract_place_spans(sentence_norm, place_pattern)
    if place_index is None or max_place_tokens is None:
        place_index, max_place_tokens = build_place_index(mapping)
    origin_candidates = collect_candidates(
        sentence_norm, origin_specs, place_pattern, mapping, place_spans
    )
    dest_candidates = collect_candidates(
        sentence_norm, dest_specs, place_pattern, mapping, place_spans
    )
    if not origin_candidates:
        origin_candidates = collect_fuzzy_candidates(
            sentence_norm, origin_specs, place_index, max_place_tokens, place_spans
        )
    if not dest_candidates:
        dest_candidates = collect_fuzzy_candidates(
            sentence_norm, dest_specs, place_index, max_place_tokens, place_spans
        )

    all_places = extract_places(sentence_norm, place_pattern, mapping)
    tokens = set(sentence_norm.split())
    marker_hit = bool(tokens & fallback_markers)
    english_only = bool(tokens & english_markers) and not bool(tokens & french_markers)
    if english_only and not (origin_candidates or dest_candidates):
        return None, None
    fallback_allowed = bool(origin_candidates or dest_candidates) or marker_hit
    if fallback_allowed and len(all_places) < 2:
        fuzzy_places = extract_places_fuzzy(sentence_norm, place_index, max_place_tokens)
        known = {place for _, place in all_places}
        for pos, place in fuzzy_places:
            if place not in known:
                all_places.append((pos, place))
                known.add(place)
        all_places.sort(key=lambda item: item[0])

    ordered = []
    for _, place in sorted(all_places, key=lambda item: item[0]):
        if place not in ordered:
            ordered.append(place)

    origin = origin_candidates[-1][1] if origin_candidates else None
    destination = dest_candidates[-1][1] if dest_candidates else None

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
    place_index, max_place_tokens = build_place_index(mapping)

    for line in iter_input_lines(args.inputs):
        if not line.strip():
            continue
        if "," not in line:
            continue
        sentence_id, sentence = line.split(",", 1)
        origin, destination = resolve_order(
            sentence, mapping, place_pattern, place_index, max_place_tokens
        )
        if origin and destination:
            print(f"{sentence_id},{origin},{destination}")
        else:
            print(f"{sentence_id},INVALID,")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
