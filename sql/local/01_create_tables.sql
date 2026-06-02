create table if not exists staging_transactions (
    operation_id text primary key,
    account_number_from text,
    currency_code integer,
    country text,
    status text,
    transaction_type text,
    amount real,
    transaction_dt text
);

create table if not exists staging_currencies (
    currency_code integer,
    currency_code_with integer,
    date_update text,
    currency_with_div real
);

create table if not exists dwh_global_metrics (
    date_update text,
    currency_from integer,
    amount_total real,
    amount_usd_total real,
    transaction_count integer
);

