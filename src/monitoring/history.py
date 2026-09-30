from __future__ import annotations

import hashlib
import sqlite3
from pathlib import Path
from typing import Any

import pandas as pd

SCHEMA = """
CREATE TABLE IF NOT EXISTS quality_runs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    run_id TEXT UNIQUE NOT NULL,
    run_at TEXT NOT NULL,
    dataset_name TEXT NOT NULL,
    dataset_hash TEXT NOT NULL,
    row_count INTEGER NOT NULL,
    column_count INTEGER NOT NULL,
    quality_score REAL NOT NULL,
    gate_status TEXT NOT NULL,
    total_findings INTEGER NOT NULL,
    critical_high_findings INTEGER NOT NULL,
    p0_findings INTEGER NOT NULL,
    contract_violations INTEGER NOT NULL,
    completeness_score REAL,
    consistency_score REAL,
    validity_score REAL,
    uniqueness_score REAL,
    timeliness_score REAL
);
CREATE INDEX IF NOT EXISTS idx_quality_runs_run_at ON quality_runs(run_at);
"""


def fingerprint_dataframe(df: pd.DataFrame) -> str:
    normalized = df.copy()
    normalized.columns = [str(c) for c in normalized.columns]
    payload = pd.util.hash_pandas_object(normalized, index=True).values.tobytes()
    schema = "|".join(f"{c}:{normalized[c].dtype}" for c in normalized.columns).encode()
    return hashlib.sha256(schema + payload).hexdigest()


def init_history_db(path: str | Path) -> Path:
    db_path = Path(path)
    db_path.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(db_path) as conn:
        conn.executescript(SCHEMA)
    return db_path


def record_quality_run(
    path: str | Path,
    *,
    dataset_name: str,
    dataset_hash: str,
    row_count: int,
    column_count: int,
    quality_score: float,
    gate_status: str,
    total_findings: int,
    critical_high_findings: int,
    p0_findings: int,
    contract_violations: int,
    scorecard: pd.DataFrame,
    run_id: str | None = None,
    run_at: str | None = None,
) -> str:
    db_path = init_history_db(path)
    from datetime import datetime, timezone

    run_id = run_id or f"RUN-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S%f')}"
    run_at = run_at or datetime.now(timezone.utc).isoformat()

    dimension_scores = {}
    if scorecard is not None and not scorecard.empty:
        dimension_scores = {
            str(row["dimension"]).strip().lower(): float(row["score"])
            for _, row in scorecard.iterrows()
        }

    values: dict[str, Any] = {
        "run_id": run_id,
        "run_at": run_at,
        "dataset_name": dataset_name,
        "dataset_hash": dataset_hash,
        "row_count": int(row_count),
        "column_count": int(column_count),
        "quality_score": float(quality_score),
        "gate_status": gate_status,
        "total_findings": int(total_findings),
        "critical_high_findings": int(critical_high_findings),
        "p0_findings": int(p0_findings),
        "contract_violations": int(contract_violations),
        "completeness_score": dimension_scores.get("completeness"),
        "consistency_score": dimension_scores.get("consistency"),
        "validity_score": dimension_scores.get("validity"),
        "uniqueness_score": dimension_scores.get("uniqueness"),
        "timeliness_score": dimension_scores.get("timeliness"),
    }

    columns = ", ".join(values.keys())
    placeholders = ", ".join([f":{k}" for k in values])
    with sqlite3.connect(db_path) as conn:
        conn.execute(
            f"INSERT OR REPLACE INTO quality_runs ({columns}) VALUES ({placeholders})",
            values,
        )
        conn.commit()
    return run_id


def load_quality_history(path: str | Path, limit: int = 100) -> pd.DataFrame:
    db_path = Path(path)
    if not db_path.exists():
        return pd.DataFrame()
    init_history_db(db_path)
    with sqlite3.connect(db_path) as conn:
        return pd.read_sql_query(
            "SELECT * FROM quality_runs ORDER BY run_at DESC LIMIT ?",
            conn,
            params=(int(limit),),
        )


def compare_latest_runs(history: pd.DataFrame) -> dict[str, Any]:
    if history is None or len(history) < 2:
        return {"available": False}
    work = history.sort_values("run_at").reset_index(drop=True)
    previous = work.iloc[-2]
    latest = work.iloc[-1]
    return {
        "available": True,
        "previous_run_id": previous["run_id"],
        "latest_run_id": latest["run_id"],
        "score_delta": round(float(latest["quality_score"]) - float(previous["quality_score"]), 2),
        "finding_delta": int(latest["total_findings"] - previous["total_findings"]),
        "critical_high_delta": int(latest["critical_high_findings"] - previous["critical_high_findings"]),
        "gate_changed": str(previous["gate_status"]) != str(latest["gate_status"]),
        "previous_gate": previous["gate_status"],
        "latest_gate": latest["gate_status"],
    }
