from pathlib import Path

import pandas as pd

from src.contracts import load_contract
from src.monitoring.history import compare_latest_runs, fingerprint_dataframe, load_quality_history, record_quality_run
from src.monitoring.pipeline import load_yaml, run_quality_analysis


ROOT = Path(__file__).resolve().parents[1]


def test_monitoring_pipeline_runs_on_reference_batch():
    df = pd.read_csv(ROOT / "data/raw/retail_transactions_reference.csv")
    config = load_yaml(ROOT / "config.yaml")
    contract = load_contract(ROOT / "data_contract.yaml")

    result = run_quality_analysis(df, config, contract=contract, dataset_name="test")

    assert 0 <= result["overall_quality_score"] <= 100
    assert result["gate"]["status"] in {"PASS", "WARNING", "FAIL"}
    assert len(result["scorecard"]) == 5


def test_history_records_and_compares_runs(tmp_path):
    db = tmp_path / "history.db"
    scorecard = pd.DataFrame([
        {"dimension": "Completeness", "score": 100},
        {"dimension": "Consistency", "score": 100},
        {"dimension": "Validity", "score": 100},
        {"dimension": "Uniqueness", "score": 100},
        {"dimension": "Timeliness", "score": 100},
    ])
    df = pd.DataFrame({"x": [1, 2, 3]})

    record_quality_run(
        db,
        dataset_name="baseline",
        dataset_hash=fingerprint_dataframe(df),
        row_count=3,
        column_count=1,
        quality_score=98,
        gate_status="PASS",
        total_findings=0,
        critical_high_findings=0,
        p0_findings=0,
        contract_violations=0,
        scorecard=scorecard,
        run_id="RUN-1",
        run_at="2026-09-30T01:00:00+00:00",
    )
    record_quality_run(
        db,
        dataset_name="degraded",
        dataset_hash=fingerprint_dataframe(df),
        row_count=3,
        column_count=1,
        quality_score=82,
        gate_status="WARNING",
        total_findings=3,
        critical_high_findings=1,
        p0_findings=0,
        contract_violations=1,
        scorecard=scorecard.assign(score=[90, 90, 90, 90, 90]),
        run_id="RUN-2",
        run_at="2026-09-30T02:00:00+00:00",
    )

    history = load_quality_history(db)
    comparison = compare_latest_runs(history)

    assert len(history) == 2
    assert comparison["available"] is True
    assert comparison["score_delta"] == -16.0
    assert comparison["latest_gate"] == "WARNING"
