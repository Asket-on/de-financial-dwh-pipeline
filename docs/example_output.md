---
updated: 2026-06-04T18:42:30+02:00
---
# Example Output

The synthetic sample produces three daily currency-level mart rows:

| date_update | currency_from | amount_total | amount_usd_total | transaction_count |
|---|---:|---:|---:|---:|
| `2024-01-01` | `840` | `120.50` | `120.50` | `1` |
| `2024-01-01` | `978` | `85.00` | `92.65` | `1` |
| `2024-01-02` | `840` | `200.00` | `200.00` | `1` |

The source contains four raw currency-rate rows. Deterministic deduplication keeps three current rows and records one superseded version.

All six local quality checks return `0` failures:

| Check | Failures |
|---|---:|
| `duplicate_current_currency_rates` | `0` |
| `duplicate_mart_grain` | `0` |
| `join_fanout_rows` | `0` |
| `missing_exchange_rates` | `0` |
| `missing_operation_ids` | `0` |
| `negative_amounts` | `0` |

The compact profile reports:

| Metric | Value |
|---|---:|
| `currencies.raw_row_count` | `4` |
| `currencies.current_row_count` | `3` |
| `currencies.superseded_versions` | `1` |
| `transactions.row_count` | `3` |
| `transactions.distinct_operation_ids` | `3` |
| `transactions.min_date` | `2024-01-01` |
| `transactions.max_date` | `2024-01-02` |

The default local run reports the inclusive refresh window:

| Metric | Value |
|---|---:|
| `refresh_start` | `2024-01-01` |
| `refresh_end` | `2024-01-02` |
| `refreshed_rows` | `3` |

Refreshing `2024-01-01` twice produces the same two rows for that date and preserves the `2024-01-02` mart row.
