"""SQL-backed data-quality checks for relational tables."""
from __future__ import annotations

from typing import Iterable, Optional

import pandas as pd
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine


def create_sqlite_engine(path: str) -> Engine:
    return create_engine(f"sqlite:///{path}")


def list_tables(engine: Engine) -> list[str]:
    query = "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
    return pd.read_sql_query(query, engine)["name"].tolist()


def fetch_table(engine: Engine, table_name: str, limit: Optional[int] = None) -> pd.DataFrame:
    safe_name = table_name.replace('"', '""')
    query = f'SELECT * FROM "{safe_name}"'
    if limit is not None:
        query += f" LIMIT {int(limit)}"
    return pd.read_sql_query(query, engine)


def primary_key_duplicates(engine: Engine, table: str, key_columns: Iterable[str]) -> pd.DataFrame:
    keys = list(key_columns)
    group_cols = ", ".join(f'"{c}"' for c in keys)
    return pd.read_sql_query(
        f'''SELECT {group_cols}, COUNT(*) AS occurrences
            FROM "{table}"
            GROUP BY {group_cols}
            HAVING COUNT(*) > 1
            ORDER BY occurrences DESC''',
        engine,
    )


def null_violations(engine: Engine, table: str, required_columns: Iterable[str]) -> pd.DataFrame:
    rows = []
    for column in required_columns:
        query = (
            "SELECT COUNT(*) AS count FROM '{table}' WHERE '{column}' IS NULL "
            "OR TRIM(CAST('{column}' AS TEXT)) = ''"
        ).format(table=table, column=column)
        result = pd.read_sql_query(query, engine)
        count = int(result.loc[0, "count"])
        rows.append({"table": table, "column": column, "null_or_blank_count": count})
    return pd.DataFrame(rows)


def orphan_records(
    engine: Engine,
    child_table: str,
    child_key: str,
    parent_table: str,
    parent_key: str,
) -> pd.DataFrame:
    query = f'''SELECT c.*
                FROM "{child_table}" c
                LEFT JOIN "{parent_table}" p
                  ON c."{child_key}" = p."{parent_key}"
                WHERE c."{child_key}" IS NOT NULL
                  AND p."{parent_key}" IS NULL'''
    return pd.read_sql_query(query, engine)


def value_rule_violations(
    engine: Engine,
    table: str,
    rules: dict[str, dict[str, float]],
) -> pd.DataFrame:
    rows = []
    for column, rule in rules.items():
        conditions = []
        if "min" in rule:
            conditions.append(f'"{column}" < {float(rule["min"])}')
        if "max" in rule:
            conditions.append(f'"{column}" > {float(rule["max"])}')
        if not conditions:
            continue
        where = " OR ".join(conditions)
        count = int(pd.read_sql_query(
            f'''SELECT COUNT(*) AS count FROM "{table}" WHERE {where}''', engine
        ).loc[0, "count"])
        rows.append({"table": table, "column": column, "violation_count": count, "rule": rule})
    return pd.DataFrame(rows)


def reconciliation_check(
    engine: Engine,
    table: str,
    expected_column: str,
    actual_column: str,
    tolerance: float = 0.01,
) -> pd.DataFrame:
    query = f'''SELECT *,
                       ABS("{expected_column}" - "{actual_column}") AS absolute_difference
                FROM "{table}"
                WHERE ABS("{expected_column}" - "{actual_column}") > {float(tolerance)}
                ORDER BY absolute_difference DESC'''
    return pd.read_sql_query(query, engine)


def sql_health_summary(
    engine: Engine,
    table: str,
    primary_key: str | None = None,
    required_columns: Iterable[str] = (),
    value_rules: dict[str, dict[str, float]] | None = None,
) -> pd.DataFrame:
    rows = []
    row_count = int(pd.read_sql_query(f'SELECT COUNT(*) AS n FROM "{table}"', engine).loc[0, "n"])
    rows.append({"check": "Row count", "affected_count": 0, "affected_pct": 0.0, "severity": "Info"})

    if primary_key:
        dupes = primary_key_duplicates(engine, table, [primary_key])
        affected = int(dupes["occurrences"].sum()) if not dupes.empty else 0
        rows.append({
            "check": "Duplicate primary-key records",
            "affected_count": affected,
            "affected_pct": round(affected / row_count * 100, 2) if row_count else 0.0,
            "severity": "High" if affected else "None",
        })

    nulls = null_violations(engine, table, required_columns)
    for _, r in nulls.iterrows():
        affected = int(r["null_or_blank_count"])
        rows.append({
            "check": f"Required-field nulls: {r['column']}",
            "affected_count": affected,
            "affected_pct": round(affected / row_count * 100, 2) if row_count else 0.0,
            "severity": "High" if affected else "None",
        })

    if value_rules:
        violations = value_rule_violations(engine, table, value_rules)
        for _, r in violations.iterrows():
            affected = int(r["violation_count"])
            rows.append({
                "check": f"Value-rule violations: {r['column']}",
                "affected_count": affected,
                "affected_pct": round(affected / row_count * 100, 2) if row_count else 0.0,
                "severity": "High" if affected else "None",
            })

    return pd.DataFrame(rows)
