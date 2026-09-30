from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Any

import pandas as pd
import yaml


@dataclass
class ContractViolation:
    rule_id: str
    column: str
    check: str
    severity: str
    affected_rows: int
    affected_pct: float
    evidence: str
    recommendation: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def load_contract(path: str = "data_contract.yaml") -> dict[str, Any]:
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def _severity(pct: float, cfg: dict[str, Any]) -> str:
    if pct >= cfg.get("critical_pct", 10):
        return "Critical"
    if pct >= cfg.get("high_pct", 5):
        return "High"
    if pct >= cfg.get("medium_pct", 1):
        return "Medium"
    return cfg.get("default_severity", "Low")


def validate_contract(df: pd.DataFrame, contract: dict[str, Any]) -> pd.DataFrame:
    violations: list[ContractViolation] = []
    n = max(len(df), 1)
    schema = contract.get("schema", {})

    expected = schema.get("columns", {})
    missing_cols = [c for c in expected if c not in df.columns]
    for col in missing_cols:
        cfg = expected[col]
        violations.append(ContractViolation(
            rule_id=f"SCHEMA-MISSING-{col}",
            column=col,
            check="required_column",
            severity=cfg.get("severity", "Critical"),
            affected_rows=len(df),
            affected_pct=100.0,
            evidence=f"Required column '{col}' is missing from the incoming dataset.",
            recommendation="Restore the expected column upstream or update the contract intentionally.",
        ))

    expected_types = {c: v.get("dtype") for c, v in expected.items() if v.get("dtype")}
    for col, expected_dtype in expected_types.items():
        if col not in df.columns:
            continue
        actual = str(df[col].dtype)
        allowed = set(v for v in expected[col].get("accepted_dtypes", [expected_dtype]) if v)
        if actual not in allowed:
            violations.append(ContractViolation(
                rule_id=f"SCHEMA-TYPE-{col}",
                column=col,
                check="dtype",
                severity=expected[col].get("severity", "High"),
                affected_rows=len(df),
                affected_pct=100.0,
                evidence=f"Expected dtype {sorted(allowed)}, observed {actual}.",
                recommendation="Validate the upstream schema and enforce a stable data type before ingestion.",
            ))

        if expected[col].get("nullable") is False:
            mask = df[col].isna()
            count = int(mask.sum())
            if count:
                pct = count / n * 100
                violations.append(ContractViolation(
                    rule_id=f"NULL-{col}",
                    column=col,
                    check="non_nullable",
                    severity=_severity(pct, expected[col]),
                    affected_rows=count,
                    affected_pct=round(pct, 4),
                    evidence=f"{count:,} records ({pct:.2f}%) violate the non-null requirement.",
                    recommendation="Investigate the source field and prevent nulls before loading the dataset.",
                ))

        if expected[col].get("unique") is True:
            mask = df[col].duplicated(keep=False) & df[col].notna()
            count = int(mask.sum())
            if count:
                pct = count / n * 100
                violations.append(ContractViolation(
                    rule_id=f"UNIQUE-{col}",
                    column=col,
                    check="unique",
                    severity=expected[col].get("severity", "High"),
                    affected_rows=count,
                    affected_pct=round(pct, 4),
                    evidence=f"{count:,} records ({pct:.2f}%) belong to duplicated non-null values.",
                    recommendation="Check source-system key generation and deduplication logic.",
                ))

        min_value = expected[col].get("min")
        max_value = expected[col].get("max")
        if min_value is not None or max_value is not None:
            numeric = pd.to_numeric(df[col], errors="coerce")
            mask = numeric.notna()
            if min_value is not None:
                mask &= numeric >= min_value
            if max_value is not None:
                mask &= numeric <= max_value
            violations_mask = df[col].notna() & ~mask
            count = int(violations_mask.sum())
            if count:
                pct = count / n * 100
                bounds = f"min={min_value}" if max_value is None else f"max={max_value}" if min_value is None else f"{min_value}..{max_value}"
                violations.append(ContractViolation(
                    rule_id=f"RANGE-{col}",
                    column=col,
                    check="range",
                    severity=expected[col].get("severity", "High"),
                    affected_rows=count,
                    affected_pct=round(pct, 4),
                    evidence=f"{count:,} records fall outside the configured range ({bounds}).",
                    recommendation="Validate the business rule and upstream value transformation.",
                ))

        allowed_values = expected[col].get("allowed_values")
        if allowed_values:
            mask = df[col].isna() | df[col].isin(allowed_values)
            violations_mask = df[col].notna() & ~mask
            count = int(violations_mask.sum())
            if count:
                pct = count / n * 100
                violations.append(ContractViolation(
                    rule_id=f"ENUM-{col}",
                    column=col,
                    check="allowed_values",
                    severity=expected[col].get("severity", "Medium"),
                    affected_rows=count,
                    affected_pct=round(pct, 4),
                    evidence=f"{count:,} records contain values outside the configured category set.",
                    recommendation="Normalize categories or update the contract when a new category is legitimate.",
                ))

        if expected[col].get("date"):
            parsed = pd.to_datetime(df[col], errors="coerce")
            invalid_mask = df[col].notna() & parsed.isna()
            count = int(invalid_mask.sum())
            if count:
                pct = count / n * 100
                violations.append(ContractViolation(
                    rule_id=f"DATE-{col}",
                    column=col,
                    check="parseable_date",
                    severity=expected[col].get("severity", "High"),
                    affected_rows=count,
                    affected_pct=round(pct, 4),
                    evidence=f"{count:,} non-null values could not be parsed as dates.",
                    recommendation="Standardize date formatting upstream and reject malformed records.",
                ))

    # Detect undeclared columns as schema drift, but allow configured extensions.
    allowed_extra = set(schema.get("allowed_extra_columns", []))
    undeclared = [c for c in df.columns if c not in expected and c not in allowed_extra]
    for col in undeclared:
        violations.append(ContractViolation(
            rule_id=f"SCHEMA-EXTRA-{col}",
            column=col,
            check="undeclared_column",
            severity=schema.get("extra_column_severity", "Medium"),
            affected_rows=len(df),
            affected_pct=100.0,
            evidence=f"Column '{col}' is present but is not declared in the contract.",
            recommendation="Confirm whether the column is intentional; update the contract or remove the unexpected field.",
        ))

    if not violations:
        return pd.DataFrame(columns=[
            "rule_id", "column", "check", "severity", "affected_rows",
            "affected_pct", "evidence", "recommendation"
        ])

    return pd.DataFrame([v.to_dict() for v in violations])


def quality_gate(
    score: float,
    contract_df: pd.DataFrame,
    issue_df: pd.DataFrame | None = None,
    thresholds: dict[str, Any] | None = None,
) -> dict[str, Any]:
    thresholds = thresholds or {}
    fail_score = float(thresholds.get("fail_score", 70))
    warn_score = float(thresholds.get("warning_score", 85))
    fail_on_critical = bool(thresholds.get("fail_on_critical_contract_violation", True))
    fail_on_high_count = int(thresholds.get("fail_on_high_contract_violations", 3))

    critical_contract = int((contract_df["severity"] == "Critical").sum()) if not contract_df.empty else 0
    high_contract = int((contract_df["severity"].isin(["High", "Critical"])).sum()) if not contract_df.empty else 0

    overall_status = "PASS"
    reasons: list[str] = []
    if score < fail_score:
        overall_status = "FAIL"
        reasons.append(f"quality score {score:.2f} is below the fail threshold {fail_score:.2f}")
    elif score < warn_score:
        overall_status = "WARNING"
        reasons.append(f"quality score {score:.2f} is below the warning threshold {warn_score:.2f}")

    if fail_on_critical and critical_contract:
        overall_status = "FAIL"
        reasons.append(f"{critical_contract} critical contract violation(s) detected")
    elif high_contract >= fail_on_high_count:
        overall_status = "FAIL"
        reasons.append(f"{high_contract} high-severity contract violations meet the fail rule")
    elif high_contract:
        if overall_status == "PASS":
            overall_status = "WARNING"
        reasons.append(f"{high_contract} high-severity contract violation(s) detected")

    if issue_df is not None and not issue_df.empty:
        p0 = int((issue_df.get("priority") == "P0").sum()) if "priority" in issue_df else 0
        if p0:
            overall_status = "FAIL"
            reasons.append(f"{p0} P0 investigation issue(s) detected")

    return {
        "status": overall_status,
        "score": round(float(score), 2),
        "reasons": reasons or ["All configured quality-gate checks passed."],
        "critical_contract_violations": critical_contract,
        "high_contract_violations": high_contract,
    }
