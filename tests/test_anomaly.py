import numpy as np
import pandas as pd

from src.anomaly.detector import detect_isolation_forest_anomalies


def test_isolation_forest_detects_multivariate_anomalies():
    rng = np.random.default_rng(123)
    normal = pd.DataFrame({
        "amount": rng.normal(100, 5, 200),
        "quantity": rng.normal(5, 1, 200),
    })
    anomalies = pd.DataFrame({
        "amount": [500, 600, 700],
        "quantity": [40, 50, 60],
    })
    df = pd.concat([normal, anomalies], ignore_index=True)
    summary, evidence = detect_isolation_forest_anomalies(
        df,
        ["amount", "quantity"],
        contamination=0.03,
        random_state=42,
        min_samples=50,
    )
    assert not summary.empty
    assert summary.iloc[0]["affected_count"] >= 3
    assert set(range(200, 203)).issubset(set(evidence["row_index"]))
