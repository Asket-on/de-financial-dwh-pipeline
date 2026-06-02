from __future__ import annotations

from contextlib import closing
from datetime import datetime
from pathlib import Path

from src.local_warehouse import connect_local_warehouse
from src.local_warehouse import load_sources_to_staging as load_local_sources


def load_sources_to_staging(database_path: str | Path | None = None) -> dict[str, int]:
    with closing(connect_local_warehouse(database_path)) as connection:
        return load_local_sources(connection)


try:
    from airflow import DAG
    from airflow.operators.python import PythonOperator
except ModuleNotFoundError:
    dag = None
else:
    with DAG(
        dag_id="load_financial_sources_to_staging",
        start_date=datetime(2026, 1, 1),
        schedule=None,
        catchup=False,
        tags=["portfolio", "financial-dwh"],
    ) as dag:
        PythonOperator(
            task_id="load_sources_to_staging",
            python_callable=load_sources_to_staging,
        )


if __name__ == "__main__":
    print(load_sources_to_staging())
