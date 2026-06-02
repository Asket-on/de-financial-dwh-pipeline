from src.config import load_settings
from src.extract import read_sources


def build_global_metrics_preview() -> None:
    settings = load_settings()
    transactions, currencies = read_sources()
    joined = transactions.merge(
        currencies,
        left_on=["currency_code", transactions["transaction_dt"].dt.date],
        right_on=["currency_code", currencies["date_update"].dt.date],
        how="left",
        suffixes=("", "_currency"),
    )
    joined["amount_usd"] = joined["amount"] * joined["currency_with_div"]
    mart = (
        joined.groupby([transactions["transaction_dt"].dt.date, "currency_code"], as_index=False)
        .agg(amount_total=("amount", "sum"), amount_usd_total=("amount_usd", "sum"), transaction_count=("operation_id", "count"))
        .rename(columns={"transaction_dt": "date_update", "currency_code": "currency_from"})
    )
    print(f"target_schema={settings.dwh_schema}")
    print(mart.to_string(index=False))


if __name__ == "__main__":
    build_global_metrics_preview()
