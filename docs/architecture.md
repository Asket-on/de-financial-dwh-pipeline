---
updated: 2026-06-02T22:09:22+02:00
---
# Architecture Notes

## Layers

- Source: synthetic transaction and currency CSV files.
- Local staging: SQLite tables `staging_transactions` and `staging_currencies`.
- Local DWH: SQLite table `dwh_global_metrics`.
- Publication-oriented warehouse mapping: `staging.transactions`, `staging.currencies`, and `dwh.global_metrics`.
- Quality: SQL checks for nulls, negative amounts, rate coverage, and grain uniqueness.

## Local Execution

`python -m src.local_warehouse` provides the reproducible local path:

1. create SQLite tables;
2. load synthetic CSV rows;
3. rebuild the global metrics mart;
4. query the quality-check view;
5. fail the run if any check is non-zero.

`dags/financial_dwh_pipeline.py` exposes the same load and build steps as Airflow tasks when Airflow is installed and as directly runnable Python callables otherwise.

## Publication Notes

This package is derived from private course work. Keep the original notebook and assignment notes private. Publish only sanitized code, synthetic samples, and generic schema names.
