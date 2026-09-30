from __future__ import annotations

from typing import Iterable

import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import StandardScaler


SUMMARY_COLUMNS = [
    "issue_type",
    "method",
    "column",
    "severity",
    "affected_count",
    "affected_pct",
    "statistic",
    "p_value",
    "threshold",
    "evidence",
    "recommendation",
]

EVIDENCE_COLUMNS = [
    "row_index",
    "issue_type",
    "method",
    "column",
    "reason",
    "anomaly_score",
]


def _severity_from_pct(pct: float) -> str:
    if pct < 1:
        return "Low"
    if pct < 5:
        return "Medium"
    if pct < 20:
        return "High"
    return "Critical"


def detect_isolation_forest_anomalies(
    df: pd.DataFrame,
    columns: Iterable[str] | None = None,
    contamination: float = 0.02,
    n_estimators: int = 200,
    random_state: int = 42,
    min_samples: int = 50,
    top_n: int | None = None,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Detect multivariate numeric anomalies with Isolation Forest.

    Missing numeric values are median-imputed and features are standardized before
    fitting. Rows predicted as -1 are treated as candidate anomalies, not automatic
    data errors. The returned score is the Isolation Forest decision function where
    lower values indicate greater anomaly likelihood.
    """
    if len(df) < min_samples:
        empty_summary = pd.DataFrame(columns=SUMMARY_COLUMNS)
        empty_evidence = pd.DataFrame(columns=EVIDENCE_COLUMNS)
        return empty_summary, empty_evidence

    if columns is None:
        selected = df.select_dtypes(include=np.number).columns.tolist()
    else:
        selected = [c for c in columns if c in df.columns]

    if not selected:
        return pd.DataFrame(columns=SUMMARY_COLUMNS), pd.DataFrame(columns=EVIDENCE_COLUMNS)

    numeric = df[selected].apply(pd.to_numeric, errors="coerce")
    usable = [c for c in numeric.columns if numeric[c].notna().sum() >= min_samples]
    if not usable:
        return pd.DataFrame(columns=SUMMARY_COLUMNS), pd.DataFrame(columns=EVIDENCE_COLUMNS)

    numeric = numeric[usable]
    imputer = SimpleImputer(strategy="median")
    scaler = StandardScaler()
    matrix = scaler.fit_transform(imputer.fit_transform(numeric))

    model = IsolationForest(
        n_estimators=n_estimators,
        contamination=contamination,
        random_state=random_state,
        n_jobs=-1,
    )
    predictions = model.fit_predict(matrix)
    scores = model.decision_function(matrix)
    anomaly_mask = predictions == -1
    affected_count = int(anomaly_mask.sum())

    if affected_count == 0:
        return pd.DataFrame(columns=SUMMARY_COLUMNS), pd.DataFrame(columns=EVIDENCE_COLUMNS)

    affected_pct = affected_count / len(df) * 100
    selected_indices = np.flatnonzero(anomaly_mask)
    order = selected_indices[np.argsort(scores[selected_indices])]
    if top_n is not None:
        order = order[:top_n]

    evidence = pd.DataFrame({
        "row_index": df.index[order],
        "issue_type": "Anomaly",
        "method": "Isolation Forest",
        "column": ", ".join(usable),
        "reason": "Multivariate pattern isolated as anomalous by the trained Isolation Forest model.",
        "anomaly_score": np.round(scores[order], 6),
    })

    summary = pd.DataFrame([{
        "issue_type": "Anomaly",
        "method": "Isolation Forest",
        "column": ", ".join(usable),
        "severity": _severity_from_pct(affected_pct),
        "affected_count": affected_count,
        "affected_pct": round(affected_pct, 2),
        "statistic": round(float(scores[anomaly_mask].mean()), 6),
        "p_value": np.nan,
        "threshold": f"contamination={contamination:.3f}",
        "evidence": (
            f"Detected {affected_count:,} candidate anomalies across {len(usable)} numeric features. "
            "Lower decision-function scores indicate greater anomaly likelihood."
        ),
        "recommendation": (
            "Investigate the highest-ranked records and determine whether the pattern reflects a real event, "
            "data-entry error, pipeline issue, or a previously unseen valid segment."
        ),
    }], columns=SUMMARY_COLUMNS)
    return summary, evidence
