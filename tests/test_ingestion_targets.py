from __future__ import annotations

import numpy as np

from rul_pm.data.io import COLUMNS, load_training_data, read_cmapss_table, read_rul_file
from rul_pm.data.targets import add_reconstructed_test_rul, add_train_rul, capped_test_last_rul


def test_read_cmapss_table_handles_trailing_whitespace(tmp_path, synthetic_cmapss_frame, write_cmapss_table):
    path = tmp_path / "train_FD001.txt"
    write_cmapss_table(path, synthetic_cmapss_frame(n_units=2, cycles=3))
    frame = read_cmapss_table(path)
    assert list(frame.columns) == COLUMNS
    assert frame.shape == (6, 26)
    assert frame["unit_number"].dtype.kind in {"i", "u"}


def test_read_rul_file(tmp_path):
    path = tmp_path / "RUL_FD001.txt"
    path.write_text("112   \n98\n", encoding="utf-8")
    rul = read_rul_file(path)
    assert rul.tolist() == [112.0, 98.0]


def test_load_training_data_does_not_require_official_test_files(tmp_path, synthetic_cmapss_frame, write_cmapss_table):
    train = synthetic_cmapss_frame(n_units=2, cycles=3)
    write_cmapss_table(tmp_path / "train_FD001.txt", train)
    loaded = load_training_data(tmp_path, "fd001")
    assert list(loaded.columns) == COLUMNS
    np.testing.assert_allclose(loaded.to_numpy(dtype=float), train.to_numpy(dtype=float))


def test_train_and_test_rul_are_capped(synthetic_cmapss_frame):
    frame = synthetic_cmapss_frame(n_units=1, cycles=10)
    labeled = add_train_rul(frame, rul_cap=5)
    assert labeled.loc[labeled["time_in_cycles"] == 1, "RUL"].item() == 5
    assert labeled.loc[labeled["time_in_cycles"] == 10, "RUL"].item() == 0
    test_last = capped_test_last_rul(frame, provided_rul=np.array([12]), rul_cap=5)
    assert test_last["RUL"].item() == 5
    reconstructed = add_reconstructed_test_rul(frame, provided_rul=np.array([3]), rul_cap=5)
    assert reconstructed.loc[reconstructed["time_in_cycles"] == 10, "RUL"].item() == 3
    assert reconstructed["RUL"].max() == 5
