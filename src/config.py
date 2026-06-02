import os
from dataclasses import dataclass


@dataclass(frozen=True)
class Settings:
    transactions_path: str
    currencies_path: str
    local_warehouse_path: str
    warehouse_host: str
    warehouse_port: int
    warehouse_user: str
    warehouse_password: str
    warehouse_database: str
    staging_schema: str
    dwh_schema: str


def load_settings() -> Settings:
    return Settings(
        transactions_path=os.getenv("SOURCE_TRANSACTIONS_PATH", "sample_data/transactions_sample.csv"),
        currencies_path=os.getenv("SOURCE_CURRENCIES_PATH", "sample_data/currencies_sample.csv"),
        local_warehouse_path=os.getenv("LOCAL_WAREHOUSE_PATH", ".local/financial_dwh.sqlite"),
        warehouse_host=os.getenv("WAREHOUSE_HOST", "localhost"),
        warehouse_port=int(os.getenv("WAREHOUSE_PORT", "5433")),
        warehouse_user=os.getenv("WAREHOUSE_USER", "demo_user"),
        warehouse_password=os.getenv("WAREHOUSE_PASSWORD", "change_me"),
        warehouse_database=os.getenv("WAREHOUSE_DATABASE", "demo"),
        staging_schema=os.getenv("STAGING_SCHEMA", "staging"),
        dwh_schema=os.getenv("DWH_SCHEMA", "dwh"),
    )
