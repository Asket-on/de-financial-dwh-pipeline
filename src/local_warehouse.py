from __future__ import annotations

import csv
import sqlite3
from contextlib import closing
from pathlib import Path

from src.config import load_settings

PROJECT_ROOT = Path(__file__).resolve().parents[1]
LOCAL_SQL_DIR = PROJECT_ROOT / "sql" / "local"


def resolve_project_path(path: str | Path) -> Path:
    resolved = Path(path)
    if resolved.is_absolute():
        return resolved
    return PROJECT_ROOT / resolved


def read_sql(filename: str) -> str:
    return (LOCAL_SQL_DIR / filename).read_text(encoding="utf-8")


def connect_local_warehouse(database_path: str | Path | None = None) -> sqlite3.Connection:
    settings = load_settings()
    target = resolve_project_path(database_path or settings.local_warehouse_path)
    target.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(target)
    connection.row_factory = sqlite3.Row
    return connection


def ensure_schema(connection: sqlite3.Connection) -> None:
    connection.executescript(read_sql("01_create_tables.sql"))


def load_sources_to_staging(connection: sqlite3.Connection) -> dict[str, int]:
    settings = load_settings()
    transactions_path = resolve_project_path(settings.transactions_path)
    currencies_path = resolve_project_path(settings.currencies_path)

    with transactions_path.open(newline="", encoding="utf-8") as source:
        transactions = list(csv.DictReader(source))

    with currencies_path.open(newline="", encoding="utf-8") as source:
        currencies = list(csv.DictReader(source))

    ensure_schema(connection)
    connection.execute("delete from staging_transactions")
    connection.execute("delete from staging_currencies")
    connection.executemany(
        """
        insert into staging_transactions (
            operation_id,
            account_number_from,
            currency_code,
            country,
            status,
            transaction_type,
            amount,
            transaction_dt
        ) values (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        [
            (
                row["operation_id"],
                row["account_number_from"],
                int(row["currency_code"]),
                row["country"],
                row["status"],
                row["transaction_type"],
                float(row["amount"]),
                row["transaction_dt"],
            )
            for row in transactions
        ],
    )
    connection.executemany(
        """
        insert into staging_currencies (
            currency_code,
            currency_code_with,
            date_update,
            currency_with_div
        ) values (?, ?, ?, ?)
        """,
        [
            (
                int(row["currency_code"]),
                int(row["currency_code_with"]),
                row["date_update"],
                float(row["currency_with_div"]),
            )
            for row in currencies
        ],
    )
    connection.commit()
    return {"transactions_rows": len(transactions), "currencies_rows": len(currencies)}


def build_global_metrics_mart(connection: sqlite3.Connection) -> int:
    ensure_schema(connection)
    connection.executescript(read_sql("02_build_global_metrics.sql"))
    connection.commit()
    return table_row_count(connection, "dwh_global_metrics")


def run_quality_checks(connection: sqlite3.Connection) -> dict[str, int]:
    connection.executescript(read_sql("03_quality_checks.sql"))
    rows = connection.execute(
        "select check_name, failure_count from quality_check_results order by check_name"
    ).fetchall()
    return {row["check_name"]: row["failure_count"] for row in rows}


def assert_quality_checks(checks: dict[str, int]) -> None:
    failures = {name: count for name, count in checks.items() if count}
    if failures:
        raise RuntimeError(f"Data quality checks failed: {failures}")


def table_row_count(connection: sqlite3.Connection, table_name: str) -> int:
    allowed_tables = {"staging_transactions", "staging_currencies", "dwh_global_metrics"}
    if table_name not in allowed_tables:
        raise ValueError(f"Unsupported table name: {table_name}")
    return connection.execute(f"select count(*) from {table_name}").fetchone()[0]


def run_pipeline(database_path: str | Path | None = None) -> dict[str, object]:
    with closing(connect_local_warehouse(database_path)) as connection:
        source_counts = load_sources_to_staging(connection)
        mart_rows = build_global_metrics_mart(connection)
        checks = run_quality_checks(connection)
        assert_quality_checks(checks)
        return {
            **source_counts,
            "mart_rows": mart_rows,
            "quality_checks": checks,
        }


def main() -> None:
    settings = load_settings()
    summary = run_pipeline()
    print(f"local_warehouse_path={resolve_project_path(settings.local_warehouse_path)}")
    print(f"transactions_rows={summary['transactions_rows']}")
    print(f"currencies_rows={summary['currencies_rows']}")
    print(f"mart_rows={summary['mart_rows']}")
    for name, count in summary["quality_checks"].items():
        print(f"quality_check.{name}={count}")


if __name__ == "__main__":
    main()
