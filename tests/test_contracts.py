import pandas as pd

from src.contracts import quality_gate, validate_contract


def _contract():
    return {
        "schema": {
            "columns": {
                "id": {"dtype": "object", "nullable": False, "unique": True, "severity": "Critical"},
                "value": {"dtype": "float64", "nullable": False, "min": 0, "max": 10, "severity": "High"},
            },
            "allowed_extra_columns": [],
        }
    }


def test_contract_detects_null_duplicate_and_range():
    df = pd.DataFrame({"id": ["a", "a", None], "value": [1.0, 12.0, -1.0]})
    result = validate_contract(df, _contract())
    assert not result.empty
    assert set(result["check"]) >= {"non_nullable", "unique", "range"}


def test_quality_gate_fail_on_low_score():
    violations = pd.DataFrame(columns=["severity"])
    gate = quality_gate(65, violations, thresholds={"fail_score": 70, "warning_score": 85})
    assert gate["status"] == "FAIL"
