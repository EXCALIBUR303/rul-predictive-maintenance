from __future__ import annotations

import numpy as np
import pytest

from rul_pm.data.preprocess import CmapssPreprocessor
from rul_pm.data.targets import add_train_rul
from rul_pm.data.windows import build_sequence_windows, build_xgb_window_features
from rul_pm.evaluation.metrics import mae, nasa_score, regression_metrics, rmse
from rul_pm.experiment import prepare_splits


def test_preprocessor_drops_constant_sensors_and_is_train_only(synthetic_cmapss_frame):
    train = add_train_rul(synthetic_cmapss_frame(n_units=4, cycles=12), rul_cap=10)
    test = synthetic_cmapss_frame(n_units=2, cycles=12)
    pre_a = CmapssPreprocessor(n_regimes=1, low_unique_threshold=2).fit(train)
    params_before = pre_a.scalers_[0].data_min_.copy()
    transformed = pre_a.transform(test)
    assert "sensor_1" not in pre_a.feature_columns
    assert "sensor_5" not in pre_a.feature_columns
    assert "RUL" not in transformed.columns
    perturbed_test = test.copy()
    perturbed_test["sensor_2"] = perturbed_test["sensor_2"] + 10000
    pre_b = CmapssPreprocessor(n_regimes=1, low_unique_threshold=2).fit(train)
    np.testing.assert_allclose(params_before, pre_b.scalers_[0].data_min_)
    pre_b.transform(perturbed_test)
    np.testing.assert_allclose(params_before, pre_b.scalers_[0].data_min_)


def test_persisted_preprocessor_reproduces_transform(tmp_path, synthetic_cmapss_frame):
    train = add_train_rul(synthetic_cmapss_frame(n_units=4, cycles=12), rul_cap=10)
    held_out = synthetic_cmapss_frame(n_units=2, cycles=12)
    original = CmapssPreprocessor(n_regimes=1, low_unique_threshold=2).fit(train)
    original.save(tmp_path / "preprocessor.joblib")
    restored = CmapssPreprocessor.load(tmp_path / "preprocessor.joblib")
    assert original.feature_columns == restored.feature_columns
    np.testing.assert_allclose(
        original.transform(held_out)[original.feature_columns].to_numpy(),
        restored.transform(held_out)[restored.feature_columns].to_numpy(),
    )


def test_training_split_does_not_load_official_test_data(tmp_path, monkeypatch, synthetic_cmapss_frame, write_cmapss_table):
    train = synthetic_cmapss_frame(n_units=5, cycles=12)
    write_cmapss_table(tmp_path / "train_FD001.txt", train)
    config = {
        "experiment": {"subset": "FD001", "data_dir": str(tmp_path)},
        "data": {
            "rul_cap": 10,
            "validation_fraction": 0.2,
            "scaler": "minmax",
            "low_variance_threshold": 1.0e-8,
            "low_unique_threshold": 2,
            "n_regimes": 1,
        },
    }
    monkeypatch.setattr("rul_pm.experiment.load_subset", lambda *_: pytest.fail("official test data was loaded during training"))
    splits = prepare_splits(config, seed=7)
    assert set(splits["train_units"]).isdisjoint(splits["val_units"])
    assert "test" not in splits


def test_sequence_windows_never_cross_units_and_use_last_cycle_target(synthetic_cmapss_frame):
    labeled = add_train_rul(synthetic_cmapss_frame(n_units=2, cycles=5), rul_cap=10)
    pre = CmapssPreprocessor(n_regimes=1, low_unique_threshold=1).fit(labeled)
    processed = pre.transform(labeled)
    windows = build_sequence_windows(processed, pre.feature_columns, window_length=3, target_column="RUL")
    assert len(windows.x) == 6
    assert set(windows.end_cycles.tolist()) == {3, 4, 5}
    unit_one_last = np.where((windows.unit_numbers == 1) & (windows.end_cycles == 5))[0][0]
    assert windows.y[unit_one_last] == 0


def test_short_engine_left_padding(synthetic_cmapss_frame):
    labeled = add_train_rul(synthetic_cmapss_frame(n_units=1, cycles=2), rul_cap=10)
    pre = CmapssPreprocessor(n_regimes=1, low_unique_threshold=1).fit(labeled)
    processed = pre.transform(labeled)
    windows = build_sequence_windows(processed, pre.feature_columns, window_length=5, target_column="RUL", last_only=True)
    assert windows.x.shape == (1, 5, len(pre.feature_columns))
    assert windows.mask.tolist() == [[False, False, False, True, True]]


def test_xgb_feature_names_align_with_matrix(synthetic_cmapss_frame):
    labeled = add_train_rul(synthetic_cmapss_frame(n_units=1, cycles=5), rul_cap=10)
    pre = CmapssPreprocessor(n_regimes=1, low_unique_threshold=1).fit(labeled)
    processed = pre.transform(labeled)
    x, y, names, meta = build_xgb_window_features(processed, pre.feature_columns, window_length=3)
    assert x.shape[1] == len(names)
    assert len(y) == len(meta)


def test_xgb_short_window_statistics_ignore_left_padding():
    import pandas as pd

    frame = pd.DataFrame(
        {
            "unit_number": [1, 1],
            "time_in_cycles": [1, 2],
            "sensor": [2.0, 4.0],
            "RUL": [1.0, 0.0],
        }
    )
    matrix, targets, names, _ = build_xgb_window_features(frame, ["sensor"], window_length=4, last_only=True)
    assert targets.tolist() == [0.0]
    expected = {"sensor__mean": 3.0, "sensor__std": 1.0, "sensor__min": 2.0, "sensor__max": 4.0, "sensor__last": 4.0, "sensor__slope": 2.0, "sensor__delta": 2.0}
    assert dict(zip(names, matrix[0], strict=True)) == pytest.approx(expected)


def test_metrics_and_nasa_asymmetry():
    y_true = np.array([50.0, 50.0])
    early = np.array([40.0, 50.0])
    late = np.array([60.0, 50.0])
    assert mae(y_true, late) == 5.0
    assert rmse(y_true, late) > mae(y_true, late)
    assert nasa_score(y_true, late) > nasa_score(y_true, early)
    metrics = regression_metrics(y_true, np.array([-5.0, 200.0]), rul_cap=125)
    assert metrics.mae == 62.5
