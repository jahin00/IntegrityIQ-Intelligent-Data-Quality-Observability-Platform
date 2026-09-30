from __future__ import annotations

from pathlib import Path
from typing import Any

import pandas as pd
import yaml

from src.anomaly.detector import detect_isolation_forest_anomalies
from src.contracts import quality_gate, validate_contract
from src.profiling.basic import detect_exact_duplicates, detect_missing_values, profile_dataframe
from src.profiling.rules import (
    detect_category_inconsistencies,
    detect_date_anomalies,
    detect_domain_violations,
)
from src.profiling.statistics import (
    detect_distribution_shift,
    detect_iqr_outliers,
    detect_zscore_outliers,
)
from src.reporting.intelligence import build_investigation_summary, build_issue_register
from src.scoring.quality_score import calculate_quality_scorecard


def load_yaml(path: str | Path) -> dict[str, Any]:
    with open(path, "r", encoding="utf-8") as fh:
        return yaml.safe_load(fh) or {}


def run_quality_analysis(
    df: pd.DataFrame,
    config: dict[str, Any],
    *,
    reference_df: pd.DataFrame | None = None,
    contract: dict[str, Any] | None = None,
    dataset_name: str = "dataset",
) -> dict[str, Any]:
    profile = profile_dataframe(df)
    missing = detect_missing_values(df)
    duplicates = detect_exact_duplicates(df)

    numeric_summary, numeric_evidence = detect_domain_violations(
        df, config.get("rules", {}).get("numeric", {})
    )
    category_summary, category_evidence = detect_category_inconsistencies(
        df, config.get("rules", {}).get("categories", [])
    )
    date_summary, date_evidence = detect_date_anomalies(
        df, config.get("rules", {}).get("dates", [])
    )

    iqr_summary, iqr_evidence = detect_iqr_outliers(
        df,
        columns=config.get("statistical", {}).get("outlier_columns"),
        multiplier=config.get("statistical", {}).get("iqr_multiplier", 1.5),
        min_samples=config.get("statistical", {}).get("min_samples", 30),
    )
    z_summary, z_evidence = detect_zscore_outliers(
        df,
        columns=config.get("statistical", {}).get("outlier_columns"),
        threshold=config.get("statistical", {}).get("zscore_threshold", 3.0),
        min_samples=config.get("statistical", {}).get("min_samples", 30),
    )

    ml_summary, ml_evidence = detect_isolation_forest_anomalies(
        df,
        columns=config.get("anomaly", {}).get("columns"),
        contamination=config.get("anomaly", {}).get("contamination", 0.02),
        n_estimators=config.get("anomaly", {}).get("n_estimators", 200),
        random_state=config.get("anomaly", {}).get("random_state", 42),
        min_samples=config.get("anomaly", {}).get("min_samples", 50),
        top_n=config.get("anomaly", {}).get("top_n", 1000),
    )

    if reference_df is not None:
        shift_summary, shift_evidence = detect_distribution_shift(
            reference_df,
            df,
            columns=config.get("statistical", {}).get("distribution_columns"),
            alpha=config.get("statistical", {}).get("alpha", 0.05),
            psi_threshold=config.get("statistical", {}).get("psi_threshold", 0.20),
            min_samples=config.get("statistical", {}).get("min_samples", 30),
        )
    else:
        shift_summary, shift_evidence = pd.DataFrame(), pd.DataFrame()

    def _concat_nonempty(frames: list[pd.DataFrame]) -> pd.DataFrame:
        nonempty = [frame for frame in frames if frame is not None and not frame.empty]
        return pd.concat(nonempty, ignore_index=True) if nonempty else pd.DataFrame()

    rule_issues = _concat_nonempty([numeric_summary, category_summary, date_summary])
    statistical_issues = _concat_nonempty([iqr_summary, z_summary, shift_summary])
    issues = _concat_nonempty([rule_issues, statistical_issues, ml_summary])
    evidence = _concat_nonempty(
        [numeric_evidence, category_evidence, date_evidence, iqr_evidence, z_evidence, shift_evidence, ml_evidence]
    )

    scorecard, overall_quality_score = calculate_quality_scorecard(
        df, issues, config.get("score_weights", {})
    )
    issue_register = build_issue_register(issues, missing=missing, duplicates=duplicates)

    contract_results = pd.DataFrame()
    gate = {"status": "UNKNOWN", "score": overall_quality_score, "reasons": []}
    if contract is not None:
        contract_results = validate_contract(df, contract)
        gate = quality_gate(
            overall_quality_score,
            contract_results,
            issue_df=issue_register,
            thresholds=contract.get("quality_gate", {}),
        )

    summary = build_investigation_summary(
        issue_register,
        overall_quality_score,
        dataset_name,
        len(df),
        len(df.columns),
    )

    return {
        "profile": profile,
        "missing": missing,
        "duplicates": duplicates,
        "numeric_summary": numeric_summary,
        "numeric_evidence": numeric_evidence,
        "category_summary": category_summary,
        "category_evidence": category_evidence,
        "date_summary": date_summary,
        "date_evidence": date_evidence,
        "iqr_summary": iqr_summary,
        "iqr_evidence": iqr_evidence,
        "z_summary": z_summary,
        "z_evidence": z_evidence,
        "shift_summary": shift_summary,
        "shift_evidence": shift_evidence,
        "ml_summary": ml_summary,
        "ml_evidence": ml_evidence,
        "issues": issues,
        "evidence": evidence,
        "scorecard": scorecard,
        "overall_quality_score": overall_quality_score,
        "issue_register": issue_register,
        "contract_results": contract_results,
        "gate": gate,
        "summary": summary,
    }
