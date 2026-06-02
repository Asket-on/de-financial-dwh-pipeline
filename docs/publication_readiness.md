# Publication Readiness

## Ready

- Synthetic sample data only.
- Generic schemas and demo configuration only.
- Repeatable local SQLite pipeline.
- Visible SQL quality gates.
- Positive and negative unit-test scenarios.
- Airflow-compatible task callables.
- GitHub Actions CI workflow.
- Repeatable secrets audit.
- Generated `.local/`, `__pycache__/`, and SQLite files ignored.

## Verified Locally

```bash
python scripts/check_no_secrets.py
python -m unittest discover -s tests -v
python -m src.local_warehouse
python -m dags.financial_dwh_pipeline
python -m compileall -q src dags tests scripts
```

Observed result:

- secrets audit passed;
- `3` tests passed;
- `3` transaction rows loaded;
- `3` currency rows loaded;
- `3` mart rows built;
- `5` quality checks returned `0`;
- missing exchange-rate scenario was rejected.

## External Checks

- Run `docker compose up --abort-on-container-exit` on a machine with Docker.
- Load `dags/financial_dwh_pipeline.py` in a full Airflow installation and verify DAG discovery.
- Confirm GitHub Actions after the public repository is created.

## Publication Boundary

Publish this sanitized package only. Keep private course notes, notebooks, credentials, infrastructure identifiers, and raw assignment text outside the repository.

