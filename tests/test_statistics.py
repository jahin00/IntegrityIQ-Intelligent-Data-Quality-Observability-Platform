import numpy as np
import pandas as pd

from src.profiling.statistics import (
    detect_distribution_shift,
    detect_iqr_outliers,
    detect_zscore_outliers,
)


def test_iqr_detects_extreme_value():
    df = pd.DataFrame({"amount": [10, 11, 12, 13, 14, 15, 16, 17, 18, 500] * 4})
    summary, evidence = detect_iqr_outliers(df, ["amount"], min_samples=5)
    assert len(summary) == 1
    assert summary.iloc[0]["affected_count"] > 0
    assert len(evidence) == summary.iloc[0]["affected_count"]


def test_zscore_detects_extreme_value():
    rng = np.random.default_rng(7)
    values = np.concatenate([rng.normal(100, 3, 100), [180]])
    df = pd.DataFrame({"amount": values})
    summary, evidence = detect_zscore_outliers(df, ["amount"], threshold=3, min_samples=20)
    assert len(summary) == 1
    assert summary.iloc[0]["affected_count"] >= 1
    assert len(evidence) >= 1


def test_distribution_shift_detects_numeric_and_categorical_change():
    rng = np.random.default_rng(42)
    reference = pd.DataFrame({
        "amount": rng.normal(100, 5, 500),
        "region": rng.choice(["A", "B"], 500, p=[0.9, 0.1]),
    })
    current = pd.DataFrame({
        "amount": rng.normal(140, 5, 500),
        "region": rng.choice(["A", "B"], 500, p=[0.3, 0.7]),
    })
    summary, _ = detect_distribution_shift(reference, current, min_samples=30)
    assert set(summary["column"]) == {"amount", "region"}
    assert set(summary["method"]) == {"KS + PSI", "Chi-square + PSI"}
