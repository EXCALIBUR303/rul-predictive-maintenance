#!/usr/bin/env python3
"""Download C-MAPSS and extract the three files required for a supported subset."""

from __future__ import annotations

import argparse
import hashlib
import shutil
import sys
import tempfile
import urllib.request
import zipfile
from pathlib import Path


NASA_CMAPSS_URL = "https://phm-datasets.s3.amazonaws.com/NASA/6.+Turbofan+Engine+Degradation+Simulation+Data+Set.zip"
SUPPORTED_SUBSETS = ("FD001", "FD004")
FD004_MIRROR_COMMIT = "2b562334f2114d9dadfc0861dededc16cf2550d9"
FD004_MIRROR_BASE_URL = f"https://raw.githubusercontent.com/PunVas/nasa-c-mapss/{FD004_MIRROR_COMMIT}"
FD004_SHA256 = {
    "train_FD004.txt": "27ef6160b6a1dcb2613a88de9c239f763b223f02cdc41dc5cdedc5dc189b6218",
    "test_FD004.txt": "1dc675fff0624bac10786927c6715b37d1297657137400d2b1a3138d777a3ba5",
    "RUL_FD004.txt": "196b836b85a95ac7fdbbf29c5fdf1657382eafa445644d114ffaaf50dc2975e1",
}


def _required_files(subset: str) -> tuple[str, str, str]:
    normalized = subset.upper()
    if normalized not in SUPPORTED_SUBSETS:
        raise ValueError(f"Unsupported subset: {subset}. Expected one of {', '.join(SUPPORTED_SUBSETS)}.")
    return (f"train_{normalized}.txt", f"test_{normalized}.txt", f"RUL_{normalized}.txt")


def _extract_subset(archive: Path, destination: Path, subset: str, force: bool) -> None:
    required_files = _required_files(subset)
    with zipfile.ZipFile(archive) as bundle:
        members = {Path(member.filename).name: member for member in bundle.infolist()}
        missing = [name for name in required_files if name not in members]
        if missing:
            raise RuntimeError(f"Archive does not contain required {subset.upper()} files: {', '.join(missing)}")
        destination.mkdir(parents=True, exist_ok=True)
        for name in required_files:
            target = destination / name
            if target.exists() and not force:
                print(f"Keeping existing {target}")
                continue
            with bundle.open(members[name]) as source, target.open("wb") as output:
                shutil.copyfileobj(source, output)
            print(f"Extracted {target}")


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for block in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _download_fd004_from_verified_mirror(destination: Path, force: bool) -> None:
    """Fetch FD004 from a pinned mirror while NASA's full archive is unavailable."""
    destination.mkdir(parents=True, exist_ok=True)
    for name, expected_sha256 in FD004_SHA256.items():
        target = destination / name
        if target.exists() and not force:
            if _sha256(target) != expected_sha256:
                raise RuntimeError(f"Existing {target} does not match the expected FD004 SHA-256. Use --force to replace it.")
            print(f"Keeping verified {target}")
            continue
        url = f"{FD004_MIRROR_BASE_URL}/{name}"
        try:
            with urllib.request.urlopen(url) as response, target.open("wb") as output:
                shutil.copyfileobj(response, output)
        except OSError as error:
            target.unlink(missing_ok=True)
            raise RuntimeError(f"Download failed for {url}: {error}") from error
        actual_sha256 = _sha256(target)
        if actual_sha256 != expected_sha256:
            target.unlink(missing_ok=True)
            raise RuntimeError(f"SHA-256 mismatch for {name}: expected {expected_sha256}, got {actual_sha256}")
        print(f"Downloaded and verified {target}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--subset", default="FD001", choices=SUPPORTED_SUBSETS, help="C-MAPSS subset to extract.")
    parser.add_argument("--destination", type=Path, default=Path("data/raw/CMAPSSData"))
    parser.add_argument("--url", default=NASA_CMAPSS_URL, help="NASA-hosted C-MAPSS ZIP URL (used for FD001 only).")
    parser.add_argument("--force", action="store_true", help="Replace existing files for the selected subset.")
    args = parser.parse_args()

    if args.subset == "FD004":
        print(f"Downloading FD004 from the pinned mirror commit {FD004_MIRROR_COMMIT}")
        try:
            _download_fd004_from_verified_mirror(args.destination, args.force)
        except (OSError, RuntimeError) as error:
            print(f"Extraction failed: {error}", file=sys.stderr)
            return 1
    else:
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
                _extract_subset(archive, args.destination, args.subset, args.force)
            except (OSError, RuntimeError, zipfile.BadZipFile) as error:
                print(f"Extraction failed: {error}", file=sys.stderr)
                return 1

    print(f"{args.subset} is ready. Verify the files with: make eda-{args.subset.lower()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
