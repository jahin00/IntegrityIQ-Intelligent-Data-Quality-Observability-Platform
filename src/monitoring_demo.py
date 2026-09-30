from __future__ import annotations

from pathlib import Path

import pandas as pd

from src.contracts import load_contract
from src.monitoring.history import fingerprint_dataframe, record_quality_run
from src.monitoring.pipeline import load_yaml, run_quality_analysis

ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data" / "raw"
DB = ROOT / "data" / "monitoring" / "quality_history.db"


def build_variants(base: pd.DataFrame) -> list[tuple[str, pd.DataFrame]]:
    variants: list[tuple[str, pd.DataFrame]] = [("baseline_clean", base.copy())]

    v1 = base.copy()
    v1.loc[v1.index[:10], "region"] = "Dhaka "
    variants.append(("minor_category_drift", v1))

    v2 = v1.copy()
    v2.loc[v2.index[:25], "discount"] = 1.4
    variants.append(("validity_degradation", v2))

    v3 = v2.copy()
    v3.loc[v3.index[:40], "customer_age"] = None
    variants.append(("completeness_degradation", v3))

    v4 = v3.copy()
    v4 = pd.concat([v4, v4.iloc[:75]], ignore_index=True)
    variants.append(("duplicate_increase", v4))

    dirty = pd.read_csv(DATA_DIR / "retail_transactions_dirty.csv", low_memory=False)
    variants.append(("dirty_incident", dirty))
    return variants


def main() -> None:
    DB.parent.mkdir(parents=True, exist_ok=True)
    base = pd.read_csv(DATA_DIR / "retail_transactions_reference.csv", low_memory=False)
    config = load_yaml(ROOT / "config.yaml")
    contract = load_contract(ROOT / "data_contract.yaml")

    for name, df in build_variants(base):
        result = run_quality_analysis(
            df,
            config,
            reference_df=base,
            contract=contract,
            dataset_name=name,
        )
        register = result["issue_register"]
        record_quality_run(
            DB,
            dataset_name=name,
            dataset_hash=fingerprint_dataframe(df),
            row_count=len(df),
            column_count=len(df.columns),
            quality_score=result["overall_quality_score"],
            gate_status=result["gate"]["status"],
            total_findings=result["summary"]["total_findings"],
            critical_high_findings=result["summary"]["critical_high_findings"],
            p0_findings=int((register["priority"] == "P0").sum()) if not register.empty else 0,
            contract_violations=len(result["contract_results"]),
            scorecard=result["scorecard"],
        )
        print(f"{name}: score={result['overall_quality_score']:.2f}, gate={result['gate']['status']}")

    print(f"History written to {DB}")


if __name__ == "__main__":
    main()
