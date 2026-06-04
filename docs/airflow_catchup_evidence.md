---
updated: 2026-06-04T22:27:00+02:00
---
# Airflow Bounded Catchup Evidence

The persistent local Airflow Compose stack was verified with:

```bash
python scripts/run_airflow_catchup.py
```

Observed verifier output:

```text
airflow_catchup=verified
dag_run.logical_date=2024-01-01 run_id=scheduled__2024-01-01T00:00:00+00:00 state=success
dag_run.logical_date=2024-01-02 run_id=scheduled__2024-01-02T00:00:00+00:00 state=success
successful_task_instances=4
```

The verification requires:

- a healthy PostgreSQL metadata database;
- a healthy persistent LocalExecutor scheduler;
- a healthy Airflow webserver;
- exactly the two bounded scheduled logical dates;
- successful `load_sources_to_staging` and `build_global_metrics_mart` task instances for both runs.

`max_active_runs=1` serializes writes to the shared SQLite demo warehouse. This demonstrates the bounded orchestration and backfill contract, not production-scale Airflow deployment.
