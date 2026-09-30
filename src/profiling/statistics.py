from __future__ import annotations

from typing import Iterable

import numpy as np
import pandas as pd
from scipy.stats import chi2_contingency, ks_2samp, zscore


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

EVIDENCE_COLUMNS = ["row_index", "issue_type", "method", "column", "reason"]


def _empty_summary() -> pd.DataFrame:
    return pd.DataFrame(columns=SUMMARY_COLUMNS)


def _empty_evidence() -> pd.DataFrame:
    return pd.DataFrame(columns=EVIDENCE_COLUMNS)


def _severity_from_pct(pct: float) -> str:
    if pct < 1:
        return "Low"
    if pct < 5:
        return "Medium"
    if pct < 20:
        return "High"
    return "Critical"


def detect_iqr_outliers(
    df: pd.DataFrame,
    columns: Iterable[str] | None = None,
    multiplier: float = 1.5,
    min_samples: int = 20,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Detect univariate numeric outliers using the IQR rule."""
    numeric_columns = list(columns) if columns is not None else df.select_dtypes(include=np.number).columns.tolist()
    summaries: list[dict] = []
    evidence: list[pd.DataFrame] = []

    for column in numeric_columns:
        if column not in df.columns:
            continue
        series = pd.to_numeric(df[column], errors="coerce")
        valid = series.dropna()
        if len(valid) < min_samples:
            continue

        q1 = float(valid.quantile(0.25))
        q3 = float(valid.quantile(0.75))
        iqr = q3 - q1
        if iqr == 0:
            continue

        lower = q1 - multiplier * iqr
        upper = q3 + multiplier * iqr
        mask = series.notna() & ((series < lower) | (series > upper))
        count = int(mask.sum())
        if count == 0:
            continue
        pct = count / len(df) * 100
        summaries.append({
            "issue_type": "Outlier",
            "method": "IQR",
            "column": column,
            "severity": _severity_from_pct(pct),
            "affected_count": count,
            "affected_pct": round(pct, 2),
            "statistic": round(float(count / len(valid)), 4),
            "p_value": np.nan,
            "threshold": f"[{lower:.4g}, {upper:.4g}]",
            "evidence": f"Q1={q1:.4g}, Q3={q3:.4g}, IQR={iqr:.4g}; {count:,} values fall outside the IQR fences.",
            "recommendation": "Investigate extreme records and confirm whether they reflect genuine business events or data-entry problems.",
        })
        selected = df.loc[mask, [column]].copy()
        selected.insert(0, "row_index", selected.index)
        selected.insert(1, "issue_type", "Outlier")
        selected.insert(2, "method", "IQR")
        selected.insert(3, "column", column)
        selected.insert(4, "reason", f"Outside IQR fences [{lower:.4g}, {upper:.4g}]")
        evidence.append(selected)

    summary = pd.DataFrame(summaries, columns=SUMMARY_COLUMNS) if summaries else _empty_summary()
    evidence_df = pd.concat(evidence, ignore_index=True) if evidence else _empty_evidence()
    return summary, evidence_df


def detect_zscore_outliers(
    df: pd.DataFrame,
    columns: Iterable[str] | None = None,
    threshold: float = 3.0,
    min_samples: int = 20,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Detect numeric outliers using absolute standardized z-score."""
    numeric_columns = list(columns) if columns is not None else df.select_dtypes(include=np.number).columns.tolist()
    summaries: list[dict] = []
    evidence: list[pd.DataFrame] = []

    for column in numeric_columns:
        if column not in df.columns:
            continue
        series = pd.to_numeric(df[column], errors="coerce")
        valid = series.dropna()
        if len(valid) < min_samples or valid.std(ddof=0) == 0:
            continue

        scores = pd.Series(zscore(valid, nan_policy="omit"), index=valid.index)
        z_all = scores.reindex(series.index).fillna(0)
        mask = series.notna() & z_all.abs().gt(threshold)
        count = int(mask.sum())
        if count == 0:
            continue
        pct = count / len(df) * 100
        summaries.append({
            "issue_type": "Outlier",
            "method": "Z-score",
            "column": column,
            "severity": _severity_from_pct(pct),
            "affected_count": count,
            "affected_pct": round(pct, 2),
            "statistic": round(float(scores.abs()[scores.abs() > threshold].max()), 4),
            "p_value": np.nan,
            "threshold": f"|z| > {threshold}",
            "evidence": f"{count:,} values exceed the absolute z-score threshold of {threshold}.",
            "recommendation": "Review extreme standardized deviations alongside business context before removing records.",
        })
        selected = df.loc[mask, [column]].copy()
        selected.insert(0, "row_index", selected.index)
        selected.insert(1, "issue_type", "Outlier")
        selected.insert(2, "method", "Z-score")
        selected.insert(3, "column", column)
        selected.insert(4, "reason", f"Absolute z-score > {threshold}")
        evidence.append(selected)

    summary = pd.DataFrame(summaries, columns=SUMMARY_COLUMNS) if summaries else _empty_summary()
    evidence_df = pd.concat(evidence, ignore_index=True) if evidence else _empty_evidence()
    return summary, evidence_df


def _psi(reference: pd.Series, current: pd.Series, bins: int = 10) -> float:
    reference = pd.to_numeric(reference, errors="coerce").dropna()
    current = pd.to_numeric(current, errors="coerce").dropna()
    if len(reference) < 2 or len(current) < 2:
        return np.nan
    quantiles = np.linspace(0, 1, bins + 1)
    edges = np.unique(reference.quantile(quantiles).to_numpy())
    if len(edges) < 3:
        lo = float(reference.min())
        hi = float(reference.max())
        if lo == hi:
            return 0.0
        edges = np.linspace(lo, hi, bins + 1)
    edges[0] = -np.inf
    edges[-1] = np.inf

    ref_counts = pd.cut(reference, bins=edges, include_lowest=True).value_counts(sort=False).to_numpy(dtype=float)
    cur_counts = pd.cut(current, bins=edges, include_lowest=True).value_counts(sort=False).to_numpy(dtype=float)

    eps = 1e-6
    ref_pct = np.clip(ref_counts / ref_counts.sum(), eps, None)
    cur_pct = np.clip(cur_counts / cur_counts.sum(), eps, None)
    return float(np.sum((cur_pct - ref_pct) * np.log(cur_pct / ref_pct)))


def _psi_categorical(reference: pd.Series, current: pd.Series) -> float:
    ref = reference.dropna().astype(str).value_counts(normalize=True)
    cur = current.dropna().astype(str).value_counts(normalize=True)
    categories = ref.index.union(cur.index)
    ref_p = ref.reindex(categories, fill_value=0).to_numpy(dtype=float)
    cur_p = cur.reindex(categories, fill_value=0).to_numpy(dtype=float)
    eps = 1e-6
    ref_p = np.clip(ref_p, eps, None)
    cur_p = np.clip(cur_p, eps, None)
    return float(np.sum((cur_p - ref_p) * np.log(cur_p / ref_p)))


def detect_distribution_shift(
    reference_df: pd.DataFrame,
    current_df: pd.DataFrame,
    columns: Iterable[str] | None = None,
    alpha: float = 0.05,
    psi_threshold: float = 0.20,
    min_samples: int = 30,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Compare a reference batch to a current batch.

    Numeric columns use KS + PSI. Categorical columns use chi-square + PSI.
    A shift is flagged when either the statistical test or PSI crosses its threshold.
    """
    common = reference_df.columns.intersection(current_df.columns)
    selected = list(columns) if columns is not None else common.tolist()
    summaries: list[dict] = []

    for column in selected:
        if column not in common:
            continue
        reference = reference_df[column]
        current = current_df[column]
        combined_numeric = pd.concat([pd.to_numeric(reference, errors="coerce"), pd.to_numeric(current, errors="coerce")])
        numeric_ratio = combined_numeric.notna().mean()

        if pd.api.types.is_numeric_dtype(reference) or pd.api.types.is_numeric_dtype(current) or numeric_ratio >= 0.95:
            ref = pd.to_numeric(reference, errors="coerce").dropna()
            cur = pd.to_numeric(current, errors="coerce").dropna()
            if len(ref) < min_samples or len(cur) < min_samples:
                continue
            ks_stat, p_value = ks_2samp(ref, cur, alternative="two-sided", mode="auto")
            psi_value = _psi(ref, cur)
            detected = (p_value < alpha) or (psi_value >= psi_threshold)
            if not detected:
                continue
            severity = "High" if psi_value >= 0.25 or p_value < 0.01 else "Medium"
            summaries.append({
                "issue_type": "Distribution Shift",
                "method": "KS + PSI",
                "column": column,
                "severity": severity,
                "affected_count": int(len(cur)),
                "affected_pct": round(float(len(cur) / len(current_df) * 100), 2) if len(current_df) else 0,
                "statistic": round(float(ks_stat), 4),
                "p_value": round(float(p_value), 6),
                "threshold": f"p < {alpha}; PSI >= {psi_threshold} (PSI={psi_value:.4f})",
                "evidence": f"Reference n={len(ref):,}, current n={len(cur):,}; KS={ks_stat:.4f}, p={p_value:.6g}, PSI={psi_value:.4f}.",
                "recommendation": "Check for genuine business changes, upstream source changes, unit changes, or pipeline regressions.",
            })
        else:
            ref = reference.dropna().astype(str)
            cur = current.dropna().astype(str)
            if len(ref) < min_samples or len(cur) < min_samples:
                continue
            categories = ref.to_frame("value").assign(source="reference").groupby("value").size().rename("reference")
            cur_counts = cur.to_frame("value").assign(source="current").groupby("value").size().rename("current")
            table = pd.concat([categories, cur_counts], axis=1).fillna(0).to_numpy()
            if table.shape[0] < 2:
                continue
            chi2, p_value, _, _ = chi2_contingency(table)
            psi_value = _psi_categorical(ref, cur)
            detected = (p_value < alpha) or (psi_value >= psi_threshold)
            if not detected:
                continue
            severity = "High" if psi_value >= 0.25 or p_value < 0.01 else "Medium"
            summaries.append({
                "issue_type": "Distribution Shift",
                "method": "Chi-square + PSI",
                "column": column,
                "severity": severity,
                "affected_count": int(len(cur)),
                "affected_pct": round(float(len(cur) / len(current_df) * 100), 2) if len(current_df) else 0,
                "statistic": round(float(chi2), 4),
                "p_value": round(float(p_value), 6),
                "threshold": f"p < {alpha}; PSI >= {psi_threshold} (PSI={psi_value:.4f})",
                "evidence": f"Reference n={len(ref):,}, current n={len(cur):,}; chi2={chi2:.4f}, p={p_value:.6g}, PSI={psi_value:.4f}.",
                "recommendation": "Review category-mix changes and upstream mapping logic before treating the shift as a data defect.",
            })

    if not summaries:
        return _empty_summary(), _empty_evidence()
    return pd.DataFrame(summaries, columns=SUMMARY_COLUMNS), _empty_evidence()
