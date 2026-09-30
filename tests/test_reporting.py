import pandas as pd

from src.reporting.intelligence import build_issue_register, build_markdown_report


def test_issue_register_adds_missing_and_duplicate_findings():
    issues = pd.DataFrame([
        {
            "issue_type": "Invalid Value",
            "method": "Range",
            "column": "age",
            "severity": "High",
            "affected_count": 2,
            "affected_pct": 2.0,
            "evidence": "Two ages above max.",
            "recommendation": "Investigate source validation.",
        }
    ])
    missing = pd.DataFrame([
        {"column": "email", "missing_count": 3, "missing_pct": 3.0, "severity": "Medium"}
    ])
    duplicates = {"duplicate_row_count": 2, "duplicate_percentage": 2.0}

    register = build_issue_register(issues, missing, duplicates)
    assert len(register) == 3
    assert set(register["priority"]) == {"P1", "P2"}
    assert "potential_impact" in register.columns
    assert register.iloc[0]["issue_id"].startswith("DQ-")


def test_markdown_report_contains_investigation_sections():
    register = pd.DataFrame([
        {
            "issue_id": "DQ-ABC12345",
            "severity": "High",
            "priority": "P1",
            "dimension": "Validity",
            "issue_type": "Invalid Value",
            "method": "Range",
            "column": "age",
            "affected_count": 2,
            "affected_pct": 2.0,
            "evidence": "Two invalid ages.",
            "potential_impact": "Can distort analysis.",
            "investigation_area": "Source validation",
            "recommendation": "Check upstream rules.",
            "status": "Open",
        }
    ])
    scorecard = pd.DataFrame([
        {"dimension": "Validity", "score": 95, "weight": 0.2, "interpretation": "Strong"}
    ])
    report = build_markdown_report(register, scorecard, 95.0, "demo.csv", 100, 5)
    assert "Executive summary" in report
    assert "DQ-ABC12345" in report
    assert "Investigation queue" in report
