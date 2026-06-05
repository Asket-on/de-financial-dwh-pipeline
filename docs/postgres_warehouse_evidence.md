---
updated: 2026-06-05T20:01:14+02:00
---
# PostgreSQL-Compatible Warehouse SQL Evidence

`docker-compose.postgres.yml` verifies the publication-oriented warehouse SQL against PostgreSQL `16-alpine`.

The verifier runs:

```bash
docker compose -f docker-compose.postgres.yml up --abort-on-container-exit --exit-code-from warehouse-verifier
```

It applies:

- `sql/01_create_staging.sql`
- `sql/02_create_dwh.sql`
- `sql/03_build_global_metrics.sql`
- `sql/postgres_quality_assertions.sql`

The check loads the synthetic CSV sources into `staging.transactions` and `staging.currencies`, builds `staging.currency_rates_current`, refreshes `dwh.global_metrics` for `2024-01-01` through `2024-01-02`, and raises if any quality gate fails.

Expected verifier marker:

```text
postgres_warehouse=verified
```

Observed local run on 2026-06-05 built `3` mart rows and returned verifier exit code `0`.

This proves that the public warehouse SQL runs on a real schema-capable analytical database target. It does not claim live Vertica execution or production source ingestion.
