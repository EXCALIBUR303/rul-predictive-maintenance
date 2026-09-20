from __future__ import annotations

from rul_pm.eda import _regime_reference


def test_regime_reference_reports_requested_operating_conditions(synthetic_cmapss_frame):
    frame = synthetic_cmapss_frame(n_units=6, cycles=4)
    for unit in frame["unit_number"].unique():
        frame.loc[frame["unit_number"] == unit, "op_setting_1"] = float(unit % 2) * 10.0

    reference = _regime_reference(frame, n_regimes=2)

    assert reference["expected_count"] == 2
    assert reference["observed_count"] == 2
    assert sum(reference["row_counts"].values()) == len(frame)
