from __future__ import annotations

import importlib.util
import zipfile
from pathlib import Path


def _load_downloader():
    script = Path(__file__).parents[1] / "scripts" / "download_cmapss.py"
    spec = importlib.util.spec_from_file_location("download_cmapss", script)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_subset_extractor_selects_only_required_files(tmp_path):
    archive = tmp_path / "CMAPSSData.zip"
    with zipfile.ZipFile(archive, "w") as bundle:
        bundle.writestr("CMAPSSData/train_FD001.txt", "train")
        bundle.writestr("CMAPSSData/test_FD001.txt", "test")
        bundle.writestr("CMAPSSData/RUL_FD001.txt", "rul")
        bundle.writestr("CMAPSSData/train_FD004.txt", "not FD001")

    destination = tmp_path / "data"
    _load_downloader()._extract_subset(archive, destination, "FD001", force=False)

    assert {path.name for path in destination.iterdir()} == {
        "train_FD001.txt",
        "test_FD001.txt",
        "RUL_FD001.txt",
    }
    assert (destination / "train_FD001.txt").read_text(encoding="utf-8") == "train"


def test_fd004_extraction_keeps_fd001_files_out(tmp_path):
    archive = tmp_path / "CMAPSSData.zip"
    with zipfile.ZipFile(archive, "w") as bundle:
        bundle.writestr("CMAPSSData/train_FD001.txt", "not FD004")
        bundle.writestr("CMAPSSData/train_FD004.txt", "train")
        bundle.writestr("CMAPSSData/test_FD004.txt", "test")
        bundle.writestr("CMAPSSData/RUL_FD004.txt", "rul")

    destination = tmp_path / "data"
    _load_downloader()._extract_subset(archive, destination, "FD004", force=False)

    assert {path.name for path in destination.iterdir()} == {
        "train_FD004.txt",
        "test_FD004.txt",
        "RUL_FD004.txt",
    }


def test_fd004_sha256_helper_detects_content_changes(tmp_path):
    script = _load_downloader()
    sample = tmp_path / "sample.txt"
    sample.write_text("verified data", encoding="utf-8")
    assert script._sha256(sample) == "0bc6c3e7f8adcb0a21f06418f14b6b589840b138533ccc8eff89bd785fc7c026"
