import tempfile
import unittest
from contextlib import closing
from pathlib import Path

from dags.build_global_metrics_mart import build_global_metrics_mart
from dags.load_sources_to_staging import load_sources_to_staging
from src.local_warehouse import assert_quality_checks
from src.local_warehouse import build_global_metrics_mart as build_local_mart
from src.local_warehouse import connect_local_warehouse
from src.local_warehouse import load_sources_to_staging as load_local_sources
from src.local_warehouse import run_quality_checks
from src.local_warehouse import run_pipeline


class LocalPipelineTest(unittest.TestCase):
    def test_full_pipeline_builds_checked_mart(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            database_path = Path(temp_dir) / "financial_dwh.sqlite"
            summary = run_pipeline(database_path)

        self.assertEqual(summary["transactions_rows"], 3)
        self.assertEqual(summary["currencies_rows"], 3)
        self.assertEqual(summary["mart_rows"], 3)
        self.assertTrue(all(count == 0 for count in summary["quality_checks"].values()))

    def test_airflow_entrypoint_callables_run_without_airflow(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            database_path = Path(temp_dir) / "financial_dwh.sqlite"
            source_counts = load_sources_to_staging(database_path)
            mart_summary = build_global_metrics_mart(database_path)

        self.assertEqual(source_counts["transactions_rows"], 3)
        self.assertEqual(source_counts["currencies_rows"], 3)
        self.assertEqual(mart_summary["mart_rows"], 3)
        self.assertTrue(all(count == 0 for count in mart_summary["quality_checks"].values()))

    def test_quality_gate_rejects_missing_exchange_rate(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            database_path = Path(temp_dir) / "financial_dwh.sqlite"
            with closing(connect_local_warehouse(database_path)) as connection:
                load_local_sources(connection)
                connection.execute(
                    "delete from staging_currencies where currency_code = 978 and date_update = '2024-01-01'"
                )
                connection.commit()
                build_local_mart(connection)
                checks = run_quality_checks(connection)

        self.assertEqual(checks["missing_exchange_rates"], 1)
        with self.assertRaises(RuntimeError):
            assert_quality_checks(checks)


if __name__ == "__main__":
    unittest.main()
