import pandas as pd

from src.profiling.basic import detect_exact_duplicates, detect_missing_values


def test_missing_values():
    df = pd.DataFrame({"a": [1, None, 3], "b": [1, 2, 3]})
    result = detect_missing_values(df)
    row = result[result["column"] == "a"].iloc[0]
    assert row["missing_count"] == 1
    assert row["missing_pct"] == 33.33


def test_exact_duplicates():
    df = pd.DataFrame({"a": [1, 1, 2], "b": ["x", "x", "y"]})
    result = detect_exact_duplicates(df)
    assert result["duplicate_row_count"] == 2
    assert result["duplicate_group_count"] == 1
