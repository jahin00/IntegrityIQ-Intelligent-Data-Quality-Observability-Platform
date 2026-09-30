from __future__ import annotations

import argparse

import pandas as pd

from src.contracts import load_contract, quality_gate, validate_contract
from src.reporting.intelligence import build_issue_register


def main() -> int:
    parser = argparse.ArgumentParser(description="Run the AI Data Quality Detective quality gate.")
    parser.add_argument("csv", help="Incoming CSV file")
    parser.add_argument("--contract", default="data_contract.yaml")
    args = parser.parse_args()

    df = pd.read_csv(args.csv)
    contract = load_contract(args.contract)
    violations = validate_contract(df, contract)

    # Minimal score proxy for a standalone gate. The Streamlit app uses the full scorecard.
    score_df = pd.DataFrame({"column": df.columns, "missing_percentage": df.isna().mean().mul(100)})
    completeness = float(max(0, 100 - score_df["missing_percentage"].mean()))
    gate = quality_gate(completeness, violations, thresholds=contract.get("quality_gate", {}))

    print(f"Status: {gate['status']}")
    print(f"Score: {gate['score']:.2f}")
    for reason in gate["reasons"]:
        print(f"- {reason}")
    print(f"Contract violations: {len(violations)}")
    return 0 if gate["status"] != "FAIL" else 1


if __name__ == "__main__":
    raise SystemExit(main())
