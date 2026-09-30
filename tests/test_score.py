import pandas as pd

from src.scoring.quality_score import calculate_quality_scorecard


def test_quality_scorecard_is_bounded_and_weighted():
    df = pd.DataFrame({
        "a": [1, 2, None, 4],
        "b": ["x", "x", "y", "x"],
    })
    issues = pd.DataFrame([
        {"issue_type": "Rule Violation", "affected_count": 1},
        {"issue_type": "Category Inconsistency", "affected_count": 1},
        {"issue_type": "Date Anomaly", "affected_count": 1},
    ])
    weights = {
        "completeness": 0.2,
        "consistency": 0.2,
        "validity": 0.25,
        "uniqueness": 0.15,
        "timeliness": 0.2,
    }
    scorecard, overall = calculate_quality_scorecard(df, issues, weights)
    assert len(scorecard) == 5
    assert 0 <= overall <= 100
    assert round(scorecard["weight"].sum(), 6) == 1.0
