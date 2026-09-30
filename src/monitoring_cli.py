from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

from src.contracts import load_contract
from src.ingestion.loaders import load_file
from src.monitoring.history import fingerprint_dataframe, record_quality_run
from src.monitoring.pipeline import load_yaml, run_quality_analysis


def main() -> int:
    parser = argparse.ArgumentParser(description="Run and record an AI Data Quality Detective monitoring batch.")
    parser.add_argument("csv", help="Incoming CSV/XLSX file")
    parser.add_argument("--reference", help="Reference/historical CSV/XLSX file")
    parser.add_argument("--config", default="config.yaml")
    parser.add_argument("--contract", default="data_contract.yaml")
    parser.add_argument("--history-db", default="data/monitoring/quality_history.db")
    parser.add_argument("--dataset-name", default=None)
    parser.add_argument("--no-record", action="store_true")
    args = parser.parse_args()

    df = load_file(Path(args.csv))
    reference_df = load_file(Path(args.reference)) if args.reference else None
    config = load_yaml(args.config)
    contract = load_contract(args.contract)
    dataset_name = args.dataset_name or Path(args.csv).name

    result = run_quality_analysis(
        df,
        config,
        reference_df=reference_df,
        contract=contract,
        dataset_name=dataset_name,
    )

    summary = result["summary"]
    gate = result["gate"]
    print(f"Dataset: {dataset_name}")
    print(f"Rows: {len(df):,} | Columns: {len(df.columns):,}")
    print(f"Quality score: {result['overall_quality_score']:.2f}")
    print(f"Gate: {gate['status']}")
    print(f"Findings: {summary['total_findings']} | Critical/High: {summary['critical_high_findings']}")
    print("Reasons:")
    for reason in gate.get("reasons", []):
        print(f"- {reason}")

    if not args.no_record:
        run_id = record_quality_run(
            args.history_db,
            dataset_name=dataset_name,
            dataset_hash=fingerprint_dataframe(df),
            row_count=len(df),
            column_count=len(df.columns),
            quality_score=result["overall_quality_score"],
            gate_status=gate["status"],
            total_findings=summary["total_findings"],
            critical_high_findings=summary["critical_high_findings"],
            p0_findings=int((result["issue_register"]["priority"] == "P0").sum()) if not result["issue_register"].empty else 0,
            contract_violations=len(result["contract_results"]),
            scorecard=result["scorecard"],
        )
        print(f"Recorded run: {run_id}")

    return 0 if gate["status"] != "FAIL" else 1


if __name__ == "__main__":
    raise SystemExit(main())
