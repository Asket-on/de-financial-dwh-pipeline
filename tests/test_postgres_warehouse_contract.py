import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]


class PostgresWarehouseContractTest(unittest.TestCase):
    def test_postgres_compose_has_verifier_and_healthcheck(self) -> None:
        compose = (PROJECT_ROOT / "docker-compose.postgres.yml").read_text(encoding="utf-8")

        self.assertIn("postgres:16-alpine", compose)
        self.assertIn("postgres-warehouse:", compose)
        self.assertIn("warehouse-verifier:", compose)
        self.assertIn("scripts/verify_postgres_warehouse.sh", compose)
        self.assertIn("condition: service_healthy", compose)

    def test_postgres_verifier_runs_public_warehouse_sql(self) -> None:
        verifier = (PROJECT_ROOT / "scripts" / "verify_postgres_warehouse.sh").read_text(
            encoding="utf-8"
        )

        self.assertIn("sql/01_create_staging.sql", verifier)
        self.assertIn("sql/02_create_dwh.sql", verifier)
        self.assertIn("sql/03_build_global_metrics.sql", verifier)
        self.assertIn("sql/postgres_quality_assertions.sql", verifier)
        self.assertIn("postgres_warehouse=verified", verifier)

    def test_postgres_assertions_cover_expected_quality_gates(self) -> None:
        assertions = (PROJECT_ROOT / "sql" / "postgres_quality_assertions.sql").read_text(
            encoding="utf-8"
        )

        for gate_name in [
            "missing_operation_ids",
            "negative_amounts",
            "missing_exchange_rates",
            "duplicate_mart_grain",
            "duplicate_current_currency_rates",
            "join_fanout_rows",
            "unexpected_mart_rows",
        ]:
            self.assertIn(gate_name, assertions)


if __name__ == "__main__":
    unittest.main()
