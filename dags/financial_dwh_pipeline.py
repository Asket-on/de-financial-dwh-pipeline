from __future__ import annotations

from datetime import datetime

from dags.build_global_metrics_mart import build_global_metrics_mart
from dags.load_sources_to_staging import load_sources_to_staging

try:
    from airflow import DAG
    from airflow.operators.python import PythonOperator
except ModuleNotFoundError:
    dag = None
else:
    with DAG(
        dag_id="financial_dwh_pipeline",
        start_date=datetime(2026, 1, 1),
        schedule=None,
        catchup=False,
        tags=["portfolio", "financial-dwh"],
    ) as dag:
        load_task = PythonOperator(
            task_id="load_sources_to_staging",
            python_callable=load_sources_to_staging,
        )
        build_task = PythonOperator(
            task_id="build_global_metrics_mart",
            python_callable=build_global_metrics_mart,
        )
        load_task >> build_task


if __name__ == "__main__":
    load_sources_to_staging()
    print(build_global_metrics_mart())

