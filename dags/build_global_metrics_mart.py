from __future__ import annotations

from contextlib import closing
from datetime import datetime
from pathlib import Path

from src.local_warehouse import assert_quality_checks
from src.local_warehouse import connect_local_warehouse
from src.local_warehouse import refresh_global_metrics_mart
from src.local_warehouse import run_quality_checks


def build_global_metrics_mart(
    database_path: str | Path | None = None,
    start_date: str | None = None,
    end_date: str | None = None,
) -> dict[str, object]:
    with closing(connect_local_warehouse(database_path)) as connection:
        refresh = refresh_global_metrics_mart(connection, start_date, end_date)
        checks = run_quality_checks(connection)
        assert_quality_checks(checks)
        return {**refresh, "quality_checks": checks}


try:
    from airflow import DAG
    from airflow.operators.python import PythonOperator
except ModuleNotFoundError:
    dag = None
else:
    with DAG(
        dag_id="build_financial_global_metrics_mart",
        start_date=datetime(2024, 1, 1),
        end_date=datetime(2024, 1, 3),
        schedule="@daily",
        catchup=True,
        tags=["portfolio", "financial-dwh"],
    ) as dag:
        PythonOperator(
            task_id="build_global_metrics_mart",
            python_callable=build_global_metrics_mart,
            op_kwargs={"start_date": "{{ ds }}", "end_date": "{{ ds }}"},
        )


if __name__ == "__main__":
    print(build_global_metrics_mart())
