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
from src.local_warehouse import refresh_global_metrics_mart
from src.local_warehouse import run_quality_checks
from src.local_warehouse import run_pipeline


class LocalPipelineTest(unittest.TestCase):
    def test_full_pipeline_builds_checked_mart(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            database_path = Path(temp_dir) / "financial_dwh.sqlite"
            summary = run_pipeline(database_path)

        self.assertEqual(summary["transactions_rows"], 3)
        self.assertEqual(summary["currencies_rows"], 4)
        self.assertEqual(summary["mart_rows"], 3)
        self.assertTrue(all(count == 0 for count in summary["quality_checks"].values()))
        self.assertEqual(summary["profile"]["currencies.superseded_versions"], 1)

    def test_airflow_entrypoint_callables_run_without_airflow(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            database_path = Path(temp_dir) / "financial_dwh.sqlite"
            source_counts = load_sources_to_staging(database_path)
            mart_summary = build_global_metrics_mart(database_path)

        self.assertEqual(source_counts["transactions_rows"], 3)
        self.assertEqual(source_counts["currencies_rows"], 4)
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

    def test_latest_currency_rate_wins_without_join_fanout(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            database_path = Path(temp_dir) / "financial_dwh.sqlite"
            with closing(connect_local_warehouse(database_path)) as connection:
                load_local_sources(connection)
                build_local_mart(connection)
                rate = connection.execute(
                    """
                    select currency_with_div
                    from staging_currency_rates_current
                    where currency_code = 978 and date_update = '2024-01-01'
                    """
                ).fetchone()[0]
                usd_total = connection.execute(
                    """
                    select amount_usd_total
                    from dwh_global_metrics
                    where currency_from = 978 and date_update = '2024-01-01'
                    """
                ).fetchone()[0]
                checks = run_quality_checks(connection)

        self.assertAlmostEqual(rate, 1.09)
        self.assertAlmostEqual(usd_total, 92.65)
        self.assertEqual(checks["join_fanout_rows"], 0)

    def test_quality_gate_rejects_join_fanout(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            database_path = Path(temp_dir) / "financial_dwh.sqlite"
            with closing(connect_local_warehouse(database_path)) as connection:
                load_local_sources(connection)
                build_local_mart(connection)
                connection.execute(
                    """
                    insert into staging_currency_rates_current
                    select *
                    from staging_currency_rates_current
                    where currency_code = 978 and date_update = '2024-01-01'
                    """
                )
                checks = run_quality_checks(connection)

        self.assertEqual(checks["duplicate_current_currency_rates"], 1)
        self.assertEqual(checks["join_fanout_rows"], 1)
        with self.assertRaises(RuntimeError):
            assert_quality_checks(checks)

    def test_daily_refresh_is_idempotent_and_preserves_other_dates(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            database_path = Path(temp_dir) / "financial_dwh.sqlite"
            with closing(connect_local_warehouse(database_path)) as connection:
                load_local_sources(connection)
                refresh_global_metrics_mart(connection)
                before = [
                    tuple(row)
                    for row in connection.execute(
                        "select * from dwh_global_metrics order by date_update, currency_from"
                    )
                ]
                first = refresh_global_metrics_mart(connection, "2024-01-01", "2024-01-01")
                second = refresh_global_metrics_mart(connection, "2024-01-01", "2024-01-01")
                after = [
                    tuple(row)
                    for row in connection.execute(
                        "select * from dwh_global_metrics order by date_update, currency_from"
                    )
                ]

        self.assertEqual(first, second)
        self.assertEqual(first["refreshed_rows"], 2)
        self.assertEqual(first["mart_rows"], 3)
        self.assertEqual(before, after)

    def test_backfill_range_rebuilds_missing_partitions(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            database_path = Path(temp_dir) / "financial_dwh.sqlite"
            with closing(connect_local_warehouse(database_path)) as connection:
                load_local_sources(connection)
                first_day = refresh_global_metrics_mart(
                    connection, "2024-01-01", "2024-01-01"
                )
                backfill = refresh_global_metrics_mart(
                    connection, "2024-01-01", "2024-01-02"
                )

        self.assertEqual(first_day["mart_rows"], 2)
        self.assertEqual(backfill["refreshed_rows"], 3)
        self.assertEqual(backfill["mart_rows"], 3)

    def test_refresh_rejects_inverted_date_range(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            database_path = Path(temp_dir) / "financial_dwh.sqlite"
            with closing(connect_local_warehouse(database_path)) as connection:
                load_local_sources(connection)
                with self.assertRaises(ValueError):
                    refresh_global_metrics_mart(connection, "2024-01-02", "2024-01-01")


if __name__ == "__main__":
    unittest.main()
