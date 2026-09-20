#!/usr/bin/env python3
"""Download and extract the three FD001 files required by this project."""

from __future__ import annotations

import argparse
import shutil
import sys
import tempfile
import urllib.request
import zipfile
from pathlib import Path


NASA_CMAPSS_URL = "https://phm-datasets.s3.amazonaws.com/NASA/6.+Turbofan+Engine+Degradation+Simulation+Data+Set.zip"
FD001_FILES = ("train_FD001.txt", "test_FD001.txt", "RUL_FD001.txt")


def _extract_fd001(archive: Path, destination: Path, force: bool) -> None:
    with zipfile.ZipFile(archive) as bundle:
        members = {Path(member.filename).name: member for member in bundle.infolist()}
        missing = [name for name in FD001_FILES if name not in members]
        if missing:
            raise RuntimeError(f"Archive does not contain required FD001 files: {', '.join(missing)}")
        destination.mkdir(parents=True, exist_ok=True)
        for name in FD001_FILES:
            target = destination / name
            if target.exists() and not force:
                print(f"Keeping existing {target}")
                continue
            with bundle.open(members[name]) as source, target.open("wb") as output:
                shutil.copyfileobj(source, output)
            print(f"Extracted {target}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--subset", default="FD001", choices=["FD001"], help="C-MAPSS subset to extract.")
    parser.add_argument("--destination", type=Path, default=Path("data/raw/CMAPSSData"))
    parser.add_argument("--url", default=NASA_CMAPSS_URL, help="NASA-hosted C-MAPSS ZIP URL.")
    parser.add_argument("--force", action="store_true", help="Replace any existing FD001 files.")
    args = parser.parse_args()

    with tempfile.TemporaryDirectory(prefix="rulpm-cmapss-") as temp_dir:
        archive = Path(temp_dir) / "CMAPSSData.zip"
        print(f"Downloading C-MAPSS archive from {args.url}")
        try:
            with urllib.request.urlopen(args.url) as response, archive.open("wb") as output:
                shutil.copyfileobj(response, output)
        except OSError as error:
            print(f"Download failed: {error}", file=sys.stderr)
            return 1
        try:
            _extract_fd001(archive, args.destination, args.force)
        except (OSError, RuntimeError, zipfile.BadZipFile) as error:
            print(f"Extraction failed: {error}", file=sys.stderr)
            return 1

    print("FD001 is ready. Verify the files with: make eda-fd001")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
