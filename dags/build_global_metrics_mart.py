from __future__ import annotations

from contextlib import closing
from datetime import datetime
from pathlib import Path

from src.local_warehouse import assert_quality_checks
from src.local_warehouse import build_global_metrics_mart as build_local_mart
from src.local_warehouse import connect_local_warehouse
from src.local_warehouse import run_quality_checks


def build_global_metrics_mart(database_path: str | Path | None = None) -> dict[str, object]:
    with closing(connect_local_warehouse(database_path)) as connection:
        mart_rows = build_local_mart(connection)
        checks = run_quality_checks(connection)
        assert_quality_checks(checks)
        return {"mart_rows": mart_rows, "quality_checks": checks}


try:
    from airflow import DAG
    from airflow.operators.python import PythonOperator
except ModuleNotFoundError:
    dag = None
else:
    with DAG(
        dag_id="build_financial_global_metrics_mart",
        start_date=datetime(2026, 1, 1),
        schedule=None,
        catchup=False,
        tags=["portfolio", "financial-dwh"],
    ) as dag:
        PythonOperator(
            task_id="build_global_metrics_mart",
            python_callable=build_global_metrics_mart,
        )


if __name__ == "__main__":
    print(build_global_metrics_mart())
