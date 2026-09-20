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


def test_fd001_extractor_selects_only_required_files(tmp_path):
    archive = tmp_path / "CMAPSSData.zip"
    with zipfile.ZipFile(archive, "w") as bundle:
        bundle.writestr("CMAPSSData/train_FD001.txt", "train")
        bundle.writestr("CMAPSSData/test_FD001.txt", "test")
        bundle.writestr("CMAPSSData/RUL_FD001.txt", "rul")
        bundle.writestr("CMAPSSData/train_FD004.txt", "not FD001")

    destination = tmp_path / "data"
    _load_downloader()._extract_fd001(archive, destination, force=False)

    assert {path.name for path in destination.iterdir()} == {
        "train_FD001.txt",
        "test_FD001.txt",
        "RUL_FD001.txt",
    }
    assert (destination / "train_FD001.txt").read_text(encoding="utf-8") == "train"
