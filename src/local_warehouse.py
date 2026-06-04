from __future__ import annotations

import argparse
import csv
import sqlite3
from contextlib import closing
from datetime import date
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
    currency_columns = {
        row["name"] for row in connection.execute("pragma table_info(staging_currencies)")
    }
    if "source_row_number" not in currency_columns:
        connection.execute("alter table staging_currencies add column source_row_number integer")
    if "rate_updated_at" not in currency_columns:
        connection.execute("alter table staging_currencies add column rate_updated_at text")


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
            source_row_number,
            currency_code,
            currency_code_with,
            date_update,
            currency_with_div,
            rate_updated_at
        ) values (?, ?, ?, ?, ?, ?)
        """,
        [
            (
                source_row_number,
                int(row["currency_code"]),
                int(row["currency_code_with"]),
                row["date_update"],
                float(row["currency_with_div"]),
                row["rate_updated_at"],
            )
            for source_row_number, row in enumerate(currencies, start=1)
        ],
    )
    connection.commit()
    return {"transactions_rows": len(transactions), "currencies_rows": len(currencies)}


def parse_iso_date(value: str | date) -> str:
    if isinstance(value, date):
        return value.isoformat()
    return date.fromisoformat(value).isoformat()


def source_date_range(connection: sqlite3.Connection) -> tuple[str, str]:
    row = connection.execute(
        """
        select
            min(date(transaction_dt)) as start_date,
            max(date(transaction_dt)) as end_date
        from staging_transactions
        """
    ).fetchone()
    if not row["start_date"] or not row["end_date"]:
        raise RuntimeError("Cannot refresh mart without staged transactions")
    return row["start_date"], row["end_date"]


def refresh_global_metrics_mart(
    connection: sqlite3.Connection,
    start_date: str | date | None = None,
    end_date: str | date | None = None,
) -> dict[str, object]:
    ensure_schema(connection)
    connection.executescript(read_sql("02_build_global_metrics.sql"))
    source_start, source_end = source_date_range(connection)
    refresh_start = parse_iso_date(start_date or source_start)
    refresh_end = parse_iso_date(end_date or (refresh_start if start_date else source_end))
    if refresh_start > refresh_end:
        raise ValueError("start_date must be on or before end_date")
    parameters = {"start_date": refresh_start, "end_date": refresh_end}
    connection.execute(read_sql("03_delete_global_metrics_range.sql"), parameters)
    connection.execute(read_sql("04_insert_global_metrics_range.sql"), parameters)
    connection.commit()
    refreshed_rows = connection.execute(
        """
        select count(*)
        from dwh_global_metrics
        where date_update between :start_date and :end_date
        """,
        parameters,
    ).fetchone()[0]
    return {
        "refresh_start": refresh_start,
        "refresh_end": refresh_end,
        "refreshed_rows": refreshed_rows,
        "mart_rows": table_row_count(connection, "dwh_global_metrics"),
    }


def build_global_metrics_mart(connection: sqlite3.Connection) -> int:
    return int(refresh_global_metrics_mart(connection)["mart_rows"])


def run_quality_checks(connection: sqlite3.Connection) -> dict[str, int]:
    connection.executescript(read_sql("03_quality_checks.sql"))
    rows = connection.execute(
        "select check_name, failure_count from quality_check_results order by check_name"
    ).fetchall()
    return {row["check_name"]: row["failure_count"] for row in rows}


def run_profiling(connection: sqlite3.Connection) -> dict[str, object]:
    rows = connection.execute(
        "select metric_name, metric_value from profiling_results order by metric_name"
    ).fetchall()
    return {row["metric_name"]: row["metric_value"] for row in rows}


def assert_quality_checks(checks: dict[str, int]) -> None:
    failures = {name: count for name, count in checks.items() if count}
    if failures:
        raise RuntimeError(f"Data quality checks failed: {failures}")


def table_row_count(connection: sqlite3.Connection, table_name: str) -> int:
    allowed_tables = {
        "staging_transactions",
        "staging_currencies",
        "staging_currency_rates_current",
        "dwh_global_metrics",
    }
    if table_name not in allowed_tables:
        raise ValueError(f"Unsupported table name: {table_name}")
    return connection.execute(f"select count(*) from {table_name}").fetchone()[0]


def run_pipeline(
    database_path: str | Path | None = None,
    start_date: str | date | None = None,
    end_date: str | date | None = None,
) -> dict[str, object]:
    with closing(connect_local_warehouse(database_path)) as connection:
        source_counts = load_sources_to_staging(connection)
        refresh = refresh_global_metrics_mart(connection, start_date, end_date)
        checks = run_quality_checks(connection)
        assert_quality_checks(checks)
        profile = run_profiling(connection)
        return {
            **source_counts,
            **refresh,
            "quality_checks": checks,
            "profile": profile,
        }


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the local financial DWH pipeline")
    parser.add_argument("--start-date", help="Inclusive mart refresh start date (YYYY-MM-DD)")
    parser.add_argument("--end-date", help="Inclusive mart refresh end date (YYYY-MM-DD)")
    args = parser.parse_args()
    settings = load_settings()
    summary = run_pipeline(start_date=args.start_date, end_date=args.end_date)
    print(f"local_warehouse_path={resolve_project_path(settings.local_warehouse_path)}")
    print(f"transactions_rows={summary['transactions_rows']}")
    print(f"currencies_rows={summary['currencies_rows']}")
    print(f"mart_rows={summary['mart_rows']}")
    print(f"refresh_start={summary['refresh_start']}")
    print(f"refresh_end={summary['refresh_end']}")
    print(f"refreshed_rows={summary['refreshed_rows']}")
    for name, count in summary["quality_checks"].items():
        print(f"quality_check.{name}={count}")
    for name, value in summary["profile"].items():
        print(f"profile.{name}={value}")


if __name__ == "__main__":
    main()
