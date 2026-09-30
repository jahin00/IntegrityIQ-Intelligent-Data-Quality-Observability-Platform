from __future__ import annotations

from dataclasses import dataclass
import re
from typing import Any

import numpy as np
import pandas as pd


@dataclass(frozen=True)
class QualityRule:
    column: str
    rule: str
    check: str
    severity: str = "Medium"


def _issue_frame(df: pd.DataFrame, mask: pd.Series, issue_type: str, rule: str,
                 column: str, severity: str, evidence: str, recommendation: str) -> pd.DataFrame:
    mask = mask.fillna(False).astype(bool)
    affected = int(mask.sum())
    pct = round((affected / len(df)) * 100, 2) if len(df) else 0.0
    summary = pd.DataFrame([{
        "issue_type": issue_type,
        "rule": rule,
        "column": column,
        "severity": severity,
        "affected_count": affected,
        "affected_pct": pct,
        "evidence": evidence,
        "recommendation": recommendation,
    }])
    return summary


def detect_domain_violations(
    df: pd.DataFrame,
    rules: dict[str, dict[str, Any]],
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Apply numeric/range/domain rules and return summaries + row-level evidence."""
    summaries: list[pd.DataFrame] = []
    evidence_rows: list[pd.DataFrame] = []

    for column, spec in rules.items():
        if column not in df.columns:
            continue

        series = df[column]
        numeric = pd.to_numeric(series, errors="coerce")
        valid_numeric = numeric.notna() | series.isna()

        min_value = spec.get("min")
        max_value = spec.get("max")
        if min_value is not None:
            mask = valid_numeric & numeric.notna() & (numeric < min_value)
            if mask.any():
                summaries.append(_issue_frame(
                    df, mask, "Invalid Value", f"{column} >= {min_value}", column,
                    spec.get("severity", "High"),
                    f"Observed values below minimum {min_value}.",
                    f"Investigate {column} values below the permitted minimum and upstream validation.",
                ))
                evidence_rows.append(_evidence(df, mask, column, "Invalid Value", f"{column} < {min_value}"))

        if max_value is not None:
            mask = valid_numeric & numeric.notna() & (numeric > max_value)
            if mask.any():
                summaries.append(_issue_frame(
                    df, mask, "Invalid Value", f"{column} <= {max_value}", column,
                    spec.get("severity", "High"),
                    f"Observed values above maximum {max_value}.",
                    f"Investigate {column} values above the permitted maximum and upstream validation.",
                ))
                evidence_rows.append(_evidence(df, mask, column, "Invalid Value", f"{column} > {max_value}"))

        allowed = spec.get("allowed")
        if allowed:
            mask = series.notna() & ~series.astype(str).isin([str(v) for v in allowed])
            if mask.any():
                summaries.append(_issue_frame(
                    df, mask, "Invalid Value", f"{column} in allowed set", column,
                    spec.get("severity", "High"),
                    f"Observed values outside the configured allowed set: {allowed}.",
                    "Validate source-system mappings and reject or quarantine unsupported values.",
                ))
                evidence_rows.append(_evidence(df, mask, column, "Invalid Value", "Outside allowed set"))

    summary = pd.concat(summaries, ignore_index=True) if summaries else _empty_summary()
    evidence = pd.concat(evidence_rows, ignore_index=True) if evidence_rows else _empty_evidence()
    return summary, evidence


def detect_category_inconsistencies(
    df: pd.DataFrame,
    columns: list[str],
    min_variant_count: int = 2,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Find likely spelling/case/whitespace variants within categorical columns."""
    summaries: list[pd.DataFrame] = []
    evidence_rows: list[pd.DataFrame] = []

    for column in columns:
        if column not in df.columns:
            continue
        raw = df[column].dropna().astype(str)
        if raw.empty:
            continue

        normalized = raw.str.strip().str.casefold()
        groups = pd.DataFrame({"raw": raw, "normalized": normalized}).groupby("normalized")
        for canonical, group in groups:
            variants = sorted(group["raw"].unique().tolist())
            if len(variants) < min_variant_count:
                continue

            variant_mask = df[column].notna() & df[column].astype(str).str.strip().str.casefold().eq(canonical)
            affected = int(variant_mask.sum())
            pct = round((affected / len(df)) * 100, 2) if len(df) else 0.0
            summaries.append(pd.DataFrame([{
                "issue_type": "Category Inconsistency",
                "rule": f"Normalize {column} with strip + casefold",
                "column": column,
                "severity": "Medium",
                "affected_count": affected,
                "affected_pct": pct,
                "evidence": f"Variants map to normalized category '{canonical}': {variants}.",
                "recommendation": "Standardize category values at ingestion and maintain a controlled vocabulary.",
            }]))
            mask = variant_mask & ~df[column].astype(str).eq(canonical)
            evidence_rows.append(_evidence(df, mask, column, "Category Inconsistency", f"Variants of '{canonical}'"))

    summary = pd.concat(summaries, ignore_index=True) if summaries else _empty_summary()
    evidence = pd.concat(evidence_rows, ignore_index=True) if evidence_rows else _empty_evidence()
    return summary, evidence


def detect_date_anomalies(
    df: pd.DataFrame,
    date_columns: list[str],
    reference_date: pd.Timestamp | None = None,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Detect unparseable and future dates."""
    summaries: list[pd.DataFrame] = []
    evidence_rows: list[pd.DataFrame] = []
    reference_date = reference_date or pd.Timestamp.today().normalize()

    for column in date_columns:
        if column not in df.columns:
            continue

        parsed = pd.to_datetime(df[column], errors="coerce")
        invalid_mask = df[column].notna() & parsed.isna()
        future_mask = parsed.notna() & (parsed > reference_date)

        if invalid_mask.any():
            summaries.append(_issue_frame(
                df, invalid_mask, "Date Anomaly", "Date must be parseable", column, "High",
                "Non-null records could not be parsed as dates.",
                "Validate date formatting upstream and quarantine malformed values.",
            ))
            evidence_rows.append(_evidence(df, invalid_mask, column, "Date Anomaly", "Unparseable date"))

        if future_mask.any():
            summaries.append(_issue_frame(
                df, future_mask, "Date Anomaly", "Date <= reference date", column, "Medium",
                f"Dates occur after reference date {reference_date.date()}.",
                "Confirm whether future-dated records are valid forecasts or ingestion errors.",
            ))
            evidence_rows.append(_evidence(df, future_mask, column, "Date Anomaly", "Future date"))

    summary = pd.concat(summaries, ignore_index=True) if summaries else _empty_summary()
    evidence = pd.concat(evidence_rows, ignore_index=True) if evidence_rows else _empty_evidence()
    return summary, evidence


def detect_email_anomalies(df: pd.DataFrame, columns: list[str]) -> tuple[pd.DataFrame, pd.DataFrame]:
    pattern = re.compile(r"^[^\s@]+@[^\s@]+\.[^\s@]+$")
    summaries: list[pd.DataFrame] = []
    evidence_rows: list[pd.DataFrame] = []

    for column in columns:
        if column not in df.columns:
            continue
        mask = df[column].notna() & ~df[column].astype(str).map(pattern.fullmatch).notna()
        if mask.any():
            summaries.append(_issue_frame(
                df, mask, "Invalid Format", "Email must match basic email pattern", column, "Medium",
                "Non-null email values fail a basic format validation.",
                "Validate and normalize email addresses before downstream use.",
            ))
            evidence_rows.append(_evidence(df, mask, column, "Invalid Format", "Invalid email format"))

    summary = pd.concat(summaries, ignore_index=True) if summaries else _empty_summary()
    evidence = pd.concat(evidence_rows, ignore_index=True) if evidence_rows else _empty_evidence()
    return summary, evidence


def _evidence(df: pd.DataFrame, mask: pd.Series, column: str, issue_type: str, reason: str) -> pd.DataFrame:
    selected = df.loc[mask].copy()
    if selected.empty:
        return _empty_evidence()
    selected.insert(0, "row_index", selected.index)
    selected.insert(1, "issue_type", issue_type)
    selected.insert(2, "column", column)
    selected.insert(3, "reason", reason)
    return selected.reset_index(drop=True)


def _empty_summary() -> pd.DataFrame:
    return pd.DataFrame(columns=[
        "issue_type", "rule", "column", "severity", "affected_count", "affected_pct",
        "evidence", "recommendation",
    ])


def _empty_evidence() -> pd.DataFrame:
    return pd.DataFrame(columns=["row_index", "issue_type", "column", "reason"])
