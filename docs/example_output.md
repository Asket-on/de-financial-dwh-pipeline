# Example Output

The synthetic sample produces three daily currency-level mart rows:

| date_update | currency_from | amount_total | amount_usd_total | transaction_count |
|---|---:|---:|---:|---:|
| `2024-01-01` | `840` | `120.50` | `120.50` | `1` |
| `2024-01-01` | `978` | `85.00` | `92.65` | `1` |
| `2024-01-02` | `840` | `200.00` | `200.00` | `1` |

All five local quality checks return `0` failures:

| Check | Failures |
|---|---:|
| `duplicate_currency_rates` | `0` |
| `duplicate_mart_grain` | `0` |
| `missing_exchange_rates` | `0` |
| `missing_operation_ids` | `0` |
| `negative_amounts` | `0` |

