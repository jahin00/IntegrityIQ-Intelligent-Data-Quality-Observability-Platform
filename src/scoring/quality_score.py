from __future__ import annotations

from typing import Mapping, Sequence

import pandas as pd


DIMENSIONS = ["completeness", "consistency", "validity", "uniqueness", "timeliness"]


def _bounded(value: float) -> float:
    return max(0.0, min(100.0, float(value)))


def _issue_pct(issues: pd.DataFrame, issue_types: Sequence[str], row_count: int) -> float:
    if issues is None or issues.empty or row_count <= 0:
        return 0.0
    selected = issues[issues["issue_type"].isin(issue_types)]
    if selected.empty:
        return 0.0
    affected = float(pd.to_numeric(selected["affected_count"], errors="coerce").fillna(0).sum())
    return min(100.0, affected / row_count * 100.0)


def calculate_quality_scorecard(
    df: pd.DataFrame,
    issues: pd.DataFrame,
    weights: Mapping[str, float],
) -> tuple[pd.DataFrame, float]:
    """Calculate a transparent 0-100 quality scorecard.

    Dimension logic:
    - Completeness: non-missing cell percentage.
    - Consistency: penalties from category inconsistency and distribution-shift findings.
    - Validity: penalties from configured rule violations and outlier findings.
    - Uniqueness: duplicate-row percentage.
    - Timeliness: penalties from date anomalies.

    Penalties use affected-row percentages and are capped at zero. This is a
    pragmatic portfolio metric, not a universal industry standard.
    """
    row_count = len(df)
    cell_count = max(1, df.shape[0] * df.shape[1])
    missing_cells = int(df.isna().sum().sum())

    completeness = 100.0 * (1 - missing_cells / cell_count)
    category_penalty = _issue_pct(issues, ["Category Inconsistency"], row_count)
    shift_findings = int((issues["issue_type"] == "Distribution Shift").sum()) if issues is not None and not issues.empty else 0
    # Distribution shifts are dataset-level signals rather than row-level defects.
    # Apply a controlled per-finding penalty instead of counting every current row as affected.
    consistency_penalty = min(100.0, category_penalty + 8.0 * shift_findings)
    validity_penalty = _issue_pct(issues, ["Rule Violation", "Outlier", "Anomaly"], row_count)

    duplicate_rows = int(df.duplicated(keep=False).sum())
    uniqueness = 100.0 * (1 - duplicate_rows / max(1, row_count))

    timeliness_penalty = _issue_pct(issues, ["Date Anomaly"], row_count)

    scores = {
        "completeness": _bounded(completeness),
        "consistency": _bounded(100 - consistency_penalty),
        "validity": _bounded(100 - validity_penalty),
        "uniqueness": _bounded(uniqueness),
        "timeliness": _bounded(100 - timeliness_penalty),
    }

    normalized_weights = {d: float(weights.get(d, 0.0)) for d in DIMENSIONS}
    weight_total = sum(normalized_weights.values())
    if weight_total <= 0:
        normalized_weights = {d: 1 / len(DIMENSIONS) for d in DIMENSIONS}
    else:
        normalized_weights = {d: w / weight_total for d, w in normalized_weights.items()}

    overall = sum(scores[d] * normalized_weights[d] for d in DIMENSIONS)

    scorecard = pd.DataFrame([
        {
            "dimension": d.title(),
            "score": round(scores[d], 2),
            "weight": round(normalized_weights[d], 3),
            "weighted_score": round(scores[d] * normalized_weights[d], 2),
            "interpretation": "Strong" if scores[d] >= 90 else "Watch" if scores[d] >= 75 else "Needs investigation",
        }
        for d in DIMENSIONS
    ])
    return scorecard, round(overall, 2)
