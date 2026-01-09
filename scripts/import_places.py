#!/usr/bin/env python3
import argparse
import csv
from pathlib import Path

DEFAULT_COLUMNS = [
    "name",
    "nom",
    "libelle",
    "label",
    "station_name",
    "stop_name",
    "gare",
]


def select_column(header: list[str], preferred: str | None) -> str | None:
    lowered = {col.lower(): col for col in header}
    if preferred:
        return lowered.get(preferred.lower())
    for candidate in DEFAULT_COLUMNS:
        if candidate in lowered:
            return lowered[candidate]
    return None


def main() -> int:
    parser = argparse.ArgumentParser(description="Import place names from CSV.")
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output", type=Path, default=Path("data/places_imported.txt"))
    parser.add_argument("--column", type=str, default=None)
    parser.add_argument("--add-gare-alias", action="store_true")
    parser.add_argument("--limit", type=int, default=None)
    args = parser.parse_args()

    if not args.input.exists():
        return 1

    names = []
    with args.input.open("r", encoding="utf-8") as handle:
        sample = handle.read(2048)
        handle.seek(0)
        try:
            dialect = csv.Sniffer().sniff(sample, delimiters=";,\t")
        except csv.Error:
            dialect = csv.excel
        reader = csv.DictReader(handle, dialect=dialect)
        if not reader.fieldnames:
            return 1
        column = select_column(reader.fieldnames, args.column)
        if not column:
            return 1
        for row in reader:
            value = row.get(column, "").strip()
            if not value:
                continue
            names.append(value)
            if args.limit and len(names) >= args.limit:
                break

    unique = []
    seen = set()
    for name in names:
        if name in seen:
            continue
        unique.append(name)
        seen.add(name)

    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", encoding="utf-8") as handle:
        for name in unique:
            handle.write(name + "\n")
            if args.add_gare_alias:
                handle.write(f"Gare de {name}|{name}\n")
                handle.write(f"Gare {name}|{name}\n")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
