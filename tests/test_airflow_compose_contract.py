import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]


class AirflowComposeContractTest(unittest.TestCase):
    def test_airflow_compose_uses_persistent_scheduler_and_local_executor(self) -> None:
        compose = (PROJECT_ROOT / "docker-compose.airflow.yml").read_text(encoding="utf-8")

        self.assertIn("AIRFLOW__CORE__EXECUTOR: LocalExecutor", compose)
        self.assertIn("airflow-scheduler:", compose)
        self.assertIn("airflow-webserver:", compose)
        self.assertIn("postgres:", compose)
        self.assertIn("airflow_postgres:", compose)

    def test_bounded_pipeline_serializes_shared_sqlite_writes(self) -> None:
        dag_source = (PROJECT_ROOT / "dags" / "financial_dwh_pipeline.py").read_text(
            encoding="utf-8"
        )

        self.assertIn("end_date=datetime(2024, 1, 3)", dag_source)
        self.assertIn("catchup=True", dag_source)
        self.assertIn("max_active_runs=1", dag_source)

    def test_catchup_verifier_requires_two_dates_and_four_task_instances(self) -> None:
        verifier = (PROJECT_ROOT / "scripts" / "check_airflow_catchup.py").read_text(
            encoding="utf-8"
        )

        self.assertIn("datetime(2024, 1, 1", verifier)
        self.assertIn("datetime(2024, 1, 2", verifier)
        self.assertIn("EXPECTED_TASK_IDS", verifier)
        self.assertIn("successful_task_instances", verifier)


if __name__ == "__main__":
    unittest.main()
