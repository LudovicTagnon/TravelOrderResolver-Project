#!/usr/bin/env python3
import argparse
import sys
import urllib.request
import zipfile
from pathlib import Path

CHUNK_SIZE = 1024 * 1024

DEFAULT_URL = (
    "https://eu.ftp.opendatasoft.com/sncf/plandata/"
    "export-opendata-sncf-gtfs.zip"
)


def download(url: str, destination: Path) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    with urllib.request.urlopen(url) as response, destination.open("wb") as handle:
        while True:
            chunk = response.read(CHUNK_SIZE)
            if not chunk:
                break
            handle.write(chunk)


def extract(zip_path: Path, output_dir: Path, only: list[str] | None) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(zip_path) as archive:
        names = archive.namelist()
        if only:
            names = [name for name in names if Path(name).name in only]
        for name in names:
            if name.endswith("/"):
                continue
            target_name = Path(name).name
            target_path = output_dir / target_name
            with archive.open(name) as source, target_path.open("wb") as target:
                target.write(source.read())


def main() -> int:
    parser = argparse.ArgumentParser(description="Download and extract SNCF GTFS data.")
    parser.add_argument("--url", default=DEFAULT_URL)
    parser.add_argument("--zip", type=Path, default=Path("data/gtfs/gtfs.zip"))
    parser.add_argument("--output-dir", type=Path, default=Path("data/gtfs"))
    parser.add_argument("--extract", action="store_true")
    parser.add_argument(
        "--only",
        nargs="*",
        default=["stop_times.txt", "stops.txt", "trips.txt", "routes.txt"],
    )
    parser.add_argument("--skip-download", action="store_true")
    args = parser.parse_args()

    if not args.skip_download:
        print(f"Downloading {args.url}...")
        download(args.url, args.zip)
        print(f"Saved to {args.zip}")

    if args.extract:
        print(f"Extracting to {args.output_dir}...")
        extract(args.zip, args.output_dir, args.only)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
