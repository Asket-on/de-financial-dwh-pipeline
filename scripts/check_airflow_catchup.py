from __future__ import annotations

import argparse
import time
from datetime import datetime, timezone

from airflow.models.dagrun import DagRun
from airflow.models.taskinstance import TaskInstance
from airflow.utils.session import create_session
from airflow.utils.state import DagRunState, TaskInstanceState

DAG_ID = "financial_dwh_pipeline"
EXPECTED_LOGICAL_DATES = {
    datetime(2024, 1, 1, tzinfo=timezone.utc),
    datetime(2024, 1, 2, tzinfo=timezone.utc),
}
EXPECTED_TASK_IDS = {"load_sources_to_staging", "build_global_metrics_mart"}


def catchup_status() -> dict[str, object]:
    with create_session() as session:
        runs = (
            session.query(DagRun)
            .filter(DagRun.dag_id == DAG_ID)
            .order_by(DagRun.execution_date)
            .all()
        )
        run_rows = [
            {"run_id": run.run_id, "logical_date": run.logical_date, "state": run.state}
            for run in runs
            if run.logical_date in EXPECTED_LOGICAL_DATES
        ]
        task_rows = (
            session.query(TaskInstance)
            .filter(
                TaskInstance.dag_id == DAG_ID,
                TaskInstance.run_id.in_([run["run_id"] for run in run_rows]),
            )
            .all()
            if run_rows
            else []
        )

    successful_dates = {
        run["logical_date"]
        for run in run_rows
        if run["state"] == DagRunState.SUCCESS
    }
    successful_tasks = {
        (task.run_id, task.task_id)
        for task in task_rows
        if task.state == TaskInstanceState.SUCCESS
    }
    expected_tasks = {
        (run["run_id"], task_id)
        for run in run_rows
        for task_id in EXPECTED_TASK_IDS
        if run["logical_date"] in EXPECTED_LOGICAL_DATES
    }
    return {
        "run_rows": run_rows,
        "successful_dates": successful_dates,
        "successful_tasks": successful_tasks,
        "expected_tasks": expected_tasks,
    }


def assert_complete(status: dict[str, object]) -> None:
    if status["successful_dates"] != EXPECTED_LOGICAL_DATES:
        raise RuntimeError(
            f"Expected successful logical dates {sorted(EXPECTED_LOGICAL_DATES)}, "
            f"found {sorted(status['successful_dates'])}"
        )
    if status["successful_tasks"] != status["expected_tasks"]:
        raise RuntimeError(
            f"Expected successful task instances {sorted(status['expected_tasks'])}, "
            f"found {sorted(status['successful_tasks'])}"
        )


def main() -> None:
    parser = argparse.ArgumentParser(description="Verify bounded Airflow catchup task instances")
    parser.add_argument("--timeout", type=int, default=240)
    args = parser.parse_args()
    deadline = time.monotonic() + args.timeout
    latest: dict[str, object] | None = None

    while time.monotonic() < deadline:
        latest = catchup_status()
        try:
            assert_complete(latest)
        except RuntimeError:
            time.sleep(5)
            continue
        print("airflow_catchup=verified")
        for run in latest["run_rows"]:
            print(
                f"dag_run.logical_date={run['logical_date'].date()} "
                f"run_id={run['run_id']} state={run['state']}"
            )
        print(f"successful_task_instances={len(latest['successful_tasks'])}")
        return

    raise RuntimeError(f"Airflow catchup did not complete before timeout: {latest}")


if __name__ == "__main__":
    main()
