from pathlib import Path

import pandas as pd

from src.config import load_settings


def read_sources() -> tuple[pd.DataFrame, pd.DataFrame]:
    settings = load_settings()
    transactions = pd.read_csv(Path(settings.transactions_path), parse_dates=["transaction_dt"])
    currencies = pd.read_csv(Path(settings.currencies_path), parse_dates=["date_update"])
    return transactions, currencies


def main() -> None:
    transactions, currencies = read_sources()
    print(f"transactions_rows={len(transactions)}")
    print(f"currencies_rows={len(currencies)}")


if __name__ == "__main__":
    main()
