# Project Walkthrough

This is the short interview-oriented explanation of the Financial DWH Pipeline project.

## One-Minute Summary

This project is a sanitized, reproducible financial data warehouse demo. It loads synthetic transaction and exchange-rate data, models staging and mart layers, builds a daily currency-level metrics mart, validates the output with SQL quality checks, and publishes a static dashboard from the checked mart.

The goal is to show the core Data Engineering pattern behind an analytical warehouse: source ingestion, deterministic transformation, idempotent refresh, data-quality gates, orchestration, CI, and a recruiter-visible reporting artifact.

## Business Goal

The business question is simple: how much transaction value was processed per day and currency, expressed both in native currency and USD equivalent?

The pipeline answers it by:

- loading transaction and currency-rate source files into staging;
- selecting the current exchange-rate version deterministically;
- building `dwh.global_metrics` at date and currency grain;
- checking for missing rates, duplicate mart grain, negative amounts, missing identifiers, and join fanout;
- publishing the result as a dashboard.

## Architecture Walkthrough

```text
sample_data/*.csv
  -> source extractors
  -> staging transactions and currencies
  -> current currency-rate table
  -> dwh.global_metrics mart
  -> SQL quality checks and profiling
  -> static dashboard / GitHub Pages
```

The public package keeps the warehouse-oriented naming convention (`staging.*`, `dwh.*`) while also providing a zero-dependency SQLite local adapter. PostgreSQL verification proves that the warehouse SQL can run against real schemas without relying only on SQLite table-name prefixes.

## What Makes It Data Engineering

- It separates source, staging, and analytical mart layers.
- It treats refresh boundaries as parameters, so the mart can rebuild one day or an inclusive backfill range.
- It makes the refresh idempotent by replacing only the requested date window.
- It checks data quality as part of the pipeline contract, not as a manual afterthought.
- It exposes Airflow-compatible task callables and verifies scheduler-created catchup runs.
- It uses CI to prove repeatability across tests, Docker Compose, Airflow, PostgreSQL SQL, dashboard freshness, and secret scanning.

## Proof Points

- GitHub Actions CI passes on `main`.
- Docker Compose runs the local warehouse pipeline in a clean container.
- Airflow DAG discovery is verified with the official `apache/airflow:2.10.5` image.
- A persistent Airflow LocalExecutor stack verifies bounded catchup for `2024-01-01` and `2024-01-02`.
- PostgreSQL creates `staging` and `dwh` schemas, runs the warehouse SQL, and verifies `3` mart rows.
- The static dashboard is generated deterministically and published through GitHub Pages.
- The public repository uses synthetic data and a repeatable secrets audit.

## Interview Answers

### What was the hardest part?

The hardest part was making the project credible without depending on private course infrastructure. I kept the warehouse design and orchestration contract, but replaced private sources with synthetic data and added local, Docker, Airflow, PostgreSQL, and CI verification so the claims remain demonstrable.

### How is the mart refresh idempotent?

The mart build receives a start date and optional end date. Before inserting new mart rows, it deletes only the requested date window. Re-running the same date range produces the same rows and leaves dates outside the window unchanged.

### How do you prevent bad joins or duplicated metrics?

The pipeline first selects current exchange-rate versions deterministically. Then quality checks assert mart grain uniqueness, current-rate grain uniqueness, missing exchange-rate coverage, and join fanout. If a join multiplies transaction rows or a rate is missing, the pipeline fails.

### Why verify PostgreSQL if the local adapter is SQLite?

SQLite makes the project easy to run anywhere, but it is not enough to prove warehouse-style schema behavior. The PostgreSQL verifier creates `staging` and `dwh` schemas, loads the same sources, runs the publication-oriented SQL, and checks the same mart contract in a more realistic relational target.

### What would you improve for production?

For production, I would replace synthetic CSV sources with real source connectors, move secrets to a managed secret store, add incremental source ingestion metadata, add observability around freshness and row-count changes, publish dashboard metrics to a BI tool, and run the warehouse SQL against the actual analytical target.

## Two-Minute Spoken Version

I built a reproducible financial DWH demo to show an end-to-end Data Engineering workflow. The pipeline loads synthetic transactions and exchange rates into staging, selects the current exchange-rate version deterministically, and builds a daily currency-level metrics mart with native and USD amounts.

The important part is not only the transformation, but the contract around it. The mart refresh is date-parameterized and idempotent, so I can rebuild one day or a bounded backfill window without touching unrelated dates. I also added SQL quality checks for missing identifiers, negative amounts, missing rates, duplicate mart grain, duplicate current rates, and join fanout.

To make the project credible as a public portfolio artifact, I verified it in several ways: local tests, Docker Compose execution, Airflow DAG discovery, a persistent Airflow scheduler catchup run, PostgreSQL-compatible warehouse SQL, dashboard freshness checks, and GitHub Actions CI. The output is published as a static dashboard through GitHub Pages, and the repository is sanitized with synthetic data and a secrets audit.

