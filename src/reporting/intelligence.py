from __future__ import annotations

from hashlib import sha1
from typing import Any

import pandas as pd

ISSUE_COLUMNS = [
    "issue_id",
    "severity",
    "priority",
    "dimension",
    "issue_type",
    "method",
    "column",
    "affected_count",
    "affected_pct",
    "evidence",
    "potential_impact",
    "investigation_area",
    "recommendation",
    "status",
]

SEVERITY_RANK = {"Critical": 0, "High": 1, "Medium": 2, "Low": 3, "None": 4, "Info": 5}
PRIORITY_BY_SEVERITY = {
    "Critical": "P0",
    "High": "P1",
    "Medium": "P2",
    "Low": "P3",
    "None": "P4",
    "Info": "P4",
}


def _empty_register() -> pd.DataFrame:
    return pd.DataFrame(columns=ISSUE_COLUMNS)


def _normalize_severity(value: Any) -> str:
    value = str(value) if value is not None else "Medium"
    return value if value in PRIORITY_BY_SEVERITY else "Medium"


def _map_dimension(issue_type: str) -> str:
    mapping = {
        "Missing Values": "Completeness",
        "Duplicate Rows": "Uniqueness",
        "Duplicate Primary Key": "Uniqueness",
        "Category Inconsistency": "Consistency",
        "Distribution Shift": "Consistency",
        "Invalid Value": "Validity",
        "Rule Violation": "Validity",
        "Outlier": "Validity",
        "Anomaly": "Validity",
        "Date Anomaly": "Timeliness",
        "Invalid Format": "Validity",
        "Required Field Null": "Completeness",
        "Referential Integrity": "Consistency",
        "Reconciliation": "Validity",
        "Schema Drift": "Consistency",
    }
    return mapping.get(issue_type, "Investigation")


def _impact(issue_type: str, affected_pct: float) -> str:
    if issue_type in {"Duplicate Rows", "Duplicate Primary Key"}:
        return "May double-count records, distort aggregates, and create unreliable joins or KPIs."
    if issue_type == "Missing Values":
        return "Missing fields may reduce analytical coverage and cause downstream filtering, aggregation, or model-input loss."
    if issue_type in {"Invalid Value", "Rule Violation", "Invalid Format"}:
        return "Invalid values can propagate incorrect business metrics and reduce trust in downstream analysis."
    if issue_type == "Category Inconsistency":
        return "Multiple representations of the same category can fragment group-by results and produce misleading segment totals."
    if issue_type == "Distribution Shift":
        return "A changed distribution may indicate a real business event, source-system change, pipeline issue, or population shift."
    if issue_type in {"Outlier", "Anomaly"}:
        return "Rare records may be valid events or data errors and should be reviewed before exclusion or correction."
    if issue_type == "Date Anomaly":
        return "Malformed or future dates can break time-based reporting, period comparisons, and recency calculations."
    if issue_type == "Referential Integrity":
        return "Orphan records can break relational joins and create incomplete or misleading downstream datasets."
    if issue_type == "Reconciliation":
        return "Unreconciled values may indicate transformation, aggregation, calculation, or source-system discrepancies."
    if issue_type == "Required Field Null":
        return "Missing required values can prevent reliable joins, filtering, and downstream processing."
    return f"Potential impact should be assessed for the affected {affected_pct:.2f}% of records."


def _investigation_area(issue_type: str) -> str:
    mapping = {
        "Missing Values": "Upstream ingestion and source completeness",
        "Duplicate Rows": "Deduplication and ingestion controls",
        "Duplicate Primary Key": "Primary-key generation and ingestion controls",
        "Category Inconsistency": "Reference data / controlled vocabulary",
        "Distribution Shift": "Data pipeline, population mix, and business change",
        "Invalid Value": "Source validation and domain constraints",
        "Rule Violation": "Source validation and domain constraints",
        "Outlier": "Extreme-value handling and business events",
        "Anomaly": "Multivariate anomaly review and upstream process behavior",
        "Date Anomaly": "Timestamp parsing, business dates, and ingestion timing",
        "Invalid Format": "Field formatting and upstream validation",
        "Referential Integrity": "Master-data relationships and ETL joins",
        "Reconciliation": "Transformation logic and source-to-target controls",
        "Required Field Null": "Required-field contracts and ingestion controls",
        "Schema Drift": "Upstream schema contracts and release changes",
    }
    return mapping.get(issue_type, "Source and downstream data consumers")


def _issue_id(row: pd.Series) -> str:
    raw = "|".join(
        str(row.get(k, ""))
        for k in ["issue_type", "method", "column", "severity", "rule", "evidence"]
    )
    return f"DQ-{sha1(raw.encode('utf-8')).hexdigest()[:8].upper()}"


def build_issue_register(
    issues: pd.DataFrame | None,
    missing: pd.DataFrame | None = None,
    duplicates: dict[str, Any] | None = None,
) -> pd.DataFrame:
    """Combine all detected findings into an incident-style issue register."""
    frames: list[pd.DataFrame] = []

    if missing is not None and not missing.empty:
        missing = missing.copy()
        missing = missing[missing["missing_count"].fillna(0) > 0]
        if not missing.empty:
            frames.append(pd.DataFrame({
                "issue_type": "Missing Values",
                "method": "Profile",
                "column": missing["column"],
                "severity": missing["severity"],
                "affected_count": missing["missing_count"],
                "affected_pct": missing["missing_pct"],
                "evidence": missing.apply(
                    lambda r: f"{int(r['missing_count']):,} missing values ({float(r['missing_pct']):.2f}% of records).",
                    axis=1,
                ),
                "recommendation": missing["severity"].map(
                    lambda s: "Investigate source completeness and decide whether imputation, correction, or exclusion is appropriate."
                ),
                "rule": "Non-null expected for analytical completeness",
            }))

    if duplicates and duplicates.get("duplicate_row_count", 0) > 0:
        count = int(duplicates["duplicate_row_count"])
        pct = float(duplicates.get("duplicate_percentage", 0.0))
        severity = "Critical" if pct >= 5 else "High" if pct >= 2 else "Medium" if pct >= 0.5 else "Low"
        frames.append(pd.DataFrame([{
            "issue_type": "Duplicate Rows",
            "method": "Exact duplicate detection",
            "column": "__row__",
            "severity": severity,
            "affected_count": count,
            "affected_pct": pct,
            "evidence": f"{count:,} rows are part of exact duplicate groups.",
            "recommendation": "Trace the ingestion path, define the deduplication key, and prevent repeated loads.",
            "rule": "Rows should be unique under the configured record grain",
        }]))

    if issues is not None and not issues.empty:
        work = issues.copy()
        for col in ["method", "column", "severity", "evidence", "recommendation"]:
            if col not in work.columns:
                work[col] = ""
        if "affected_count" not in work.columns:
            work["affected_count"] = 0
        if "affected_pct" not in work.columns:
            work["affected_pct"] = 0.0
        if "issue_type" not in work.columns:
            work["issue_type"] = "Investigation"
        if "rule" not in work.columns:
            work["rule"] = ""
        frames.append(work[[
            "issue_type", "method", "column", "severity", "affected_count",
            "affected_pct", "evidence", "recommendation", "rule",
        ]])

    if not frames:
        return _empty_register()

    combined = pd.concat(frames, ignore_index=True)
    combined["severity"] = combined["severity"].apply(_normalize_severity)
    combined["affected_count"] = pd.to_numeric(combined["affected_count"], errors="coerce").fillna(0).astype(int)
    combined["affected_pct"] = pd.to_numeric(combined["affected_pct"], errors="coerce").fillna(0.0).round(2)
    combined["issue_id"] = combined.apply(_issue_id, axis=1)
    combined["priority"] = combined["severity"].map(PRIORITY_BY_SEVERITY)
    combined["dimension"] = combined["issue_type"].map(_map_dimension)
    combined["potential_impact"] = combined.apply(lambda r: _impact(r["issue_type"], float(r["affected_pct"])), axis=1)
    combined["investigation_area"] = combined["issue_type"].map(_investigation_area)
    combined["status"] = "Open"

    register = combined[ISSUE_COLUMNS].drop_duplicates(subset=["issue_id"]).copy()
    register["severity_rank"] = register["severity"].map(SEVERITY_RANK).fillna(99)
    register = register.sort_values(["severity_rank", "affected_count"], ascending=[True, False]).drop(columns="severity_rank")
    return register.reset_index(drop=True)


def build_investigation_summary(
    register: pd.DataFrame,
    overall_quality_score: float,
    dataset_name: str,
    row_count: int,
    column_count: int,
) -> dict[str, Any]:
    critical_high = int(register["severity"].isin(["Critical", "High"]).sum()) if not register.empty else 0
    return {
        "dataset": dataset_name,
        "rows": int(row_count),
        "columns": int(column_count),
        "overall_quality_score": round(float(overall_quality_score), 2),
        "total_findings": int(len(register)),
        "critical_high_findings": critical_high,
        "open_findings": int((register["status"] == "Open").sum()) if not register.empty else 0,
        "top_issue_types": register["issue_type"].value_counts().head(5).to_dict() if not register.empty else {},
    }


def build_markdown_report(
    register: pd.DataFrame,
    scorecard: pd.DataFrame,
    overall_quality_score: float,
    dataset_name: str,
    row_count: int,
    column_count: int,
) -> str:
    summary = build_investigation_summary(register, overall_quality_score, dataset_name, row_count, column_count)
    lines = [
        "# AI Data Quality Detective - Investigation Report",
        "",
        f"**Dataset:** {summary['dataset']}",
        f"**Rows:** {summary['rows']:,}  ",
        f"**Columns:** {summary['columns']:,}  ",
        f"**Overall quality score:** {summary['overall_quality_score']:.2f} / 100",
        f"**Total findings:** {summary['total_findings']}",
        f"**Critical/High findings:** {summary['critical_high_findings']}",
        "",
        "## Executive summary",
        "",
        "The report consolidates deterministic validation, statistical detection, and machine-learning anomaly findings into an investigation queue. Statistical shifts and ML anomalies are investigation signals, not proof of incorrect data.",
        "",
        "## Quality scorecard",
        "",
    ]

    if scorecard is not None and not scorecard.empty:
        lines.append("| Dimension | Score | Weight | Interpretation |")
        lines.append("|---|---:|---:|---|")
        for _, row in scorecard.iterrows():
            lines.append(
                f"| {row['dimension']} | {float(row['score']):.2f} | {float(row['weight']):.3f} | {row['interpretation']} |"
            )
    else:
        lines.append("No scorecard was generated.")

    lines.extend(["", "## Findings", ""])
    if register.empty:
        lines.append("No configured findings were detected.")
    else:
        lines.extend([
            "| ID | Priority | Severity | Dimension | Issue | Column | Affected | Impact |",
            "|---|---|---|---|---|---|---:|---|",
        ])
        for _, row in register.iterrows():
            lines.append(
                f"| {row['issue_id']} | {row['priority']} | {row['severity']} | {row['dimension']} | "
                f"{row['issue_type']} | {row['column']} | {int(row['affected_count']):,} ({float(row['affected_pct']):.2f}%) | {row['potential_impact']} |"
            )

        lines.extend(["", "## Investigation queue", ""])
        for _, row in register.iterrows():
            lines.append(f"### {row['issue_id']} - {row['issue_type']}")
            lines.append(f"**Severity:** {row['severity']} | **Priority:** {row['priority']} | **Status:** {row['status']}")
            lines.append(f"**Evidence:** {row['evidence']}")
            lines.append(f"**Potential impact:** {row['potential_impact']}")
            lines.append(f"**Investigation area:** {row['investigation_area']}")
            lines.append(f"**Recommended action:** {row['recommendation']}")
            lines.append("")

    lines.extend([
        "## Methodology note",
        "",
        "The quality score is a transparent, project-specific metric. It should be interpreted alongside the underlying evidence and business context rather than treated as a universal industry standard.",
    ])
    return "\n".join(lines) + "\n"
