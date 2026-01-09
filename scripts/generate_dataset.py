#!/usr/bin/env python3
import argparse
import random
import sys
import unicodedata
from pathlib import Path


def load_places(path: Path) -> list[str]:
    places = []
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            name = line.strip()
            if not name or name.startswith("#"):
                continue
            places.append(name)
    return places


def remove_accents(text: str) -> str:
    normalized = unicodedata.normalize("NFD", text)
    return "".join(ch for ch in normalized if unicodedata.category(ch) != "Mn")


def introduce_typo(text: str, rng: random.Random) -> str:
    letters = [idx for idx, ch in enumerate(text) if ch.isalpha()]
    if len(letters) < 4:
        return text
    idx = rng.choice(letters)
    op = rng.choice(["delete", "swap", "replace"])
    chars = list(text)
    if op == "delete":
        del chars[idx]
        return "".join(chars)
    if op == "swap":
        next_idx = None
        for j in range(idx + 1, len(chars)):
            if chars[j].isalpha():
                next_idx = j
                break
        if next_idx is None:
            return text
        chars[idx], chars[next_idx] = chars[next_idx], chars[idx]
        return "".join(chars)
    replacement = rng.choice("abcdefghijklmnopqrstuvwxyz")
    chars[idx] = replacement
    return "".join(chars)


def maybe_typo(text: str, rng: random.Random, ratio: float) -> str:
    if ratio <= 0:
        return text
    if rng.random() >= ratio:
        return text
    return introduce_typo(text, rng)


def degrade(text: str, rng: random.Random) -> str:
    if rng.random() < 0.7:
        text = text.lower()
    if rng.random() < 0.4:
        text = remove_accents(text)
    if rng.random() < 0.3:
        text = text.replace("-", " ")
    if rng.random() < 0.2:
        text = text.replace("'", " ")
    return text


def pick_two_distinct(places: list[str], rng: random.Random) -> tuple[str, str]:
    origin = rng.choice(places)
    destination = rng.choice(places)
    while destination == origin:
        destination = rng.choice(places)
    return origin, destination


def build_valid_sentence(
    origin: str, destination: str, rng: random.Random, typo_ratio: float
) -> str:
    templates = [
        "je voudrais aller de {origin} a {destination}",
        "comment aller a {destination} depuis {origin}",
        "billet {origin} {destination}",
        "je veux aller a {destination} en partant de {origin}",
        "depuis {origin} je veux aller a {destination}",
        "y a t il un train de {origin} a {destination}",
        "aller de {origin} vers {destination}",
        "je souhaite me rendre a {destination} depuis {origin}",
        "trains {origin} {destination}",
        "je pars de {origin} pour {destination}",
        "depart {origin} destination {destination}",
        "besoin d un trajet {origin} {destination}",
        "je veux un billet de {origin} pour {destination}",
        "est ce quil y a des trains vers {destination} depuis {origin}",
    ]
    origin_text = maybe_typo(origin, rng, typo_ratio)
    destination_text = maybe_typo(destination, rng, typo_ratio)
    sentence = rng.choice(templates).format(
        origin=origin_text, destination=destination_text
    )
    return degrade(sentence, rng)


def build_invalid_sentence(place: str, rng: random.Random) -> str:
    templates = [
        "une phrase sans trajet",
        "bonjour je voulais juste demander",
        "{place}",
        "je parle de {place} mais sans voyage",
        "train en retard",
        "horaires pour demain",
        "merci pour {place}",
        "photo de {place}",
        "je connais {place}",
    ]
    sentence = rng.choice(templates).format(place=place)
    return degrade(sentence, rng)


def write_lines(handle, lines: list[str]) -> None:
    for line in lines:
        handle.write(line + "\n")


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate synthetic NLP dataset.")
    parser.add_argument("--places", type=Path, default=Path("data/places.txt"))
    parser.add_argument("--count", type=int, default=200)
    parser.add_argument("--valid-ratio", type=float, default=0.8)
    parser.add_argument("--intermediate-ratio", type=float, default=0.1)
    parser.add_argument("--typo-ratio", type=float, default=0.0)
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--output", default="-")
    parser.add_argument("--expected", default=None)
    args = parser.parse_args()

    places = load_places(args.places)
    if not places:
        return 1

    rng = random.Random(args.seed)
    input_lines = []
    expected_lines = []

    for idx in range(1, args.count + 1):
        sentence_id = str(idx)
        if rng.random() < args.valid_ratio and len(places) >= 2:
            origin, destination = pick_two_distinct(places, rng)
            sentence = build_valid_sentence(origin, destination, rng, args.typo_ratio)
            if rng.random() < args.intermediate_ratio and len(places) >= 3:
                intermediate = rng.choice([p for p in places if p not in (origin, destination)])
                intermediate = maybe_typo(intermediate, rng, args.typo_ratio)
                sentence = f"{sentence} en passant par {intermediate}"
            input_lines.append(f"{sentence_id},{sentence}")
            expected_lines.append(f"{sentence_id},{origin},{destination}")
        else:
            place = rng.choice(places)
            sentence = build_invalid_sentence(place, rng)
            input_lines.append(f"{sentence_id},{sentence}")
            expected_lines.append(f"{sentence_id},INVALID,")

    if args.output == "-":
        write_lines(sys.stdout, input_lines)
    else:
        output_path = Path(args.output)
        with output_path.open("w", encoding="utf-8") as handle:
            write_lines(handle, input_lines)

    if args.expected:
        expected_path = Path(args.expected)
        with expected_path.open("w", encoding="utf-8") as handle:
            write_lines(handle, expected_lines)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
