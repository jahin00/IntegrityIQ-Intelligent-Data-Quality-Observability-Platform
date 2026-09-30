from __future__ import annotations

import pandas as pd


def profile_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """Create a column-level data profile."""
    rows = []

    for column in df.columns:
        series = df[column]
        non_null = series.dropna()
        unique_count = series.nunique(dropna=True)

        rows.append(
            {
                "column": column,
                "dtype": str(series.dtype),
                "rows": len(df),
                "missing_count": int(series.isna().sum()),
                "missing_pct": round(series.isna().mean() * 100, 2),
                "unique_count": int(unique_count),
                "unique_pct": round((unique_count / len(df)) * 100, 2) if len(df) else 0,
                "sample_values": non_null.astype(str).head(5).tolist(),
            }
        )

    return pd.DataFrame(rows)


def detect_exact_duplicates(df: pd.DataFrame) -> dict:
    mask = df.duplicated(keep=False)
    return {
        "duplicate_row_count": int(mask.sum()),
        "duplicate_group_count": int(df.duplicated().sum()),
        "duplicate_percentage": round(mask.mean() * 100, 2) if len(df) else 0,
    }


def assign_severity(percentage: float) -> str:
    if percentage == 0:
        return "None"
    if percentage < 1:
        return "Low"
    if percentage < 5:
        return "Medium"
    if percentage < 20:
        return "High"
    return "Critical"


def detect_missing_values(df: pd.DataFrame) -> pd.DataFrame:
    result = profile_dataframe(df)[["column", "missing_count", "missing_pct"]].copy()
    result["severity"] = result["missing_pct"].apply(assign_severity)
    return result.sort_values("missing_pct", ascending=False).reset_index(drop=True)
