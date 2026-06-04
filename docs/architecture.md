---
updated: 2026-06-04T22:19:21+02:00
---
# Architecture Notes

## Layers

- Source: synthetic transaction and currency CSV files.
- Local raw staging: SQLite tables `staging_transactions` and `staging_currencies`.
- Local curated staging: `staging_currency_rates_current`, selected deterministically by rate update time and source row number.
- Local DWH: SQLite table `dwh_global_metrics`.
- Publication-oriented warehouse mapping: `staging.transactions`, `staging.currencies`, and `dwh.global_metrics`.
- Quality: SQL checks for nulls, negative amounts, rate coverage, grain uniqueness, and join fanout.
- Profiling: row counts, distinct operation IDs, date coverage, and raw-to-current currency-version counts.

## Local Execution

`python -m src.local_warehouse` provides the reproducible local path:

1. create SQLite tables;
2. load synthetic CSV rows;
3. select one current currency-rate version per declared grain;
4. replace only the requested inclusive mart date range without join fanout;
5. query profiling and quality-check views;
6. fail the run if any check is non-zero.

`dags/financial_dwh_pipeline.py` exposes the same load and build steps as Airflow tasks when Airflow is installed and as directly runnable Python callables otherwise.

The Airflow mart task maps `{{ ds }}` to an idempotent one-day refresh. Bounded `catchup=True` demonstrates backfill across the synthetic source period, while `max_active_runs=1` serializes writes to the shared SQLite demo warehouse. Manual local runs can pass a wider inclusive range.

`docker-compose.airflow.yml` provides a persistent local verification stack with a PostgreSQL metadata database, LocalExecutor scheduler, and webserver. `scripts/run_airflow_catchup.py` unpauses only the bounded pipeline DAG and verifies both successful DAG runs and all four expected task instances.

## Publication Notes

This package is derived from private course work. Keep the original notebook and assignment notes private. Publish only sanitized code, synthetic samples, and generic schema names.
