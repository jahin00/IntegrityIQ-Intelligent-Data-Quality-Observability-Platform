import pandas as pd

from src.profiling.rules import (
    detect_category_inconsistencies,
    detect_date_anomalies,
    detect_domain_violations,
)


def test_domain_rules_flag_bad_values():
    df = pd.DataFrame({"discount": [0.1, 1.2, -0.2], "age": [20, 150, 30]})
    summary, evidence = detect_domain_violations(
        df,
        {"discount": {"min": 0, "max": 1}, "age": {"min": 0, "max": 120}},
    )
    assert len(summary) == 3
    assert len(evidence) == 3


def test_category_variants_are_detected():
    df = pd.DataFrame({"region": ["Dhaka", "dhaka", "DHAKA", "Sylhet"]})
    summary, evidence = detect_category_inconsistencies(df, ["region"])
    assert len(summary) == 1
    assert summary.iloc[0]["affected_count"] == 3
    assert len(evidence) == 2


def test_date_anomalies_are_detected():
    df = pd.DataFrame({"date": ["2026-01-01", "2026-15-45", "2028-01-01"]})
    summary, evidence = detect_date_anomalies(
        df, ["date"], reference_date=pd.Timestamp("2026-09-30")
    )
    assert len(summary) == 2
    assert len(evidence) == 2
