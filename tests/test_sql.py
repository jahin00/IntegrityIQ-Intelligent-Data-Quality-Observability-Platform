import sqlite3
from pathlib import Path

import pandas as pd

from src.sql.quality_checks import (
    list_tables,
    null_violations,
    orphan_records,
    primary_key_duplicates,
    reconciliation_check,
)


def make_db(tmp_path: Path):
    path = tmp_path / "test.db"
    with sqlite3.connect(path) as conn:
        pd.DataFrame({"customer_id": ["C1", "C2"], "name": ["A", "B"]}).to_sql("customers", conn, index=False)
        pd.DataFrame({
            "transaction_id": ["T1", "T1", "T2"],
            "customer_id": ["C1", "C999", "C2"],
            "amount": [10.0, -5.0, 20.0],
            "expected": [10.0, 10.0, 20.0],
            "actual": [10.0, 11.5, 20.0],
        }).to_sql("orders", conn, index=False)
    return path


def test_list_tables(tmp_path):
    from src.sql.quality_checks import create_sqlite_engine
    engine = create_sqlite_engine(str(make_db(tmp_path)))
    assert list_tables(engine) == ["customers", "orders"]


def test_relational_and_reconciliation_checks(tmp_path):
    from src.sql.quality_checks import create_sqlite_engine
    engine = create_sqlite_engine(str(make_db(tmp_path)))
    assert len(primary_key_duplicates(engine, "orders", ["transaction_id"])) == 1
    assert len(orphan_records(engine, "orders", "customer_id", "customers", "customer_id")) == 1
    assert int(null_violations(engine, "orders", ["customer_id"]).loc[0, "null_or_blank_count"]) == 0
    assert len(reconciliation_check(engine, "orders", "expected", "actual", tolerance=0.1)) == 1
