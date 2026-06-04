create schema if not exists staging;

create table if not exists staging.transactions (
    operation_id varchar(64) primary key,
    account_number_from varchar(64),
    currency_code integer,
    country varchar(64),
    status varchar(32),
    transaction_type varchar(64),
    amount numeric(18, 4),
    transaction_dt timestamp
);

create table if not exists staging.currencies (
    source_row_number integer,
    currency_code integer,
    currency_code_with integer,
    date_update date,
    currency_with_div numeric(18, 8),
    rate_updated_at timestamp
);

create table if not exists staging.currency_rates_current (
    source_row_number integer,
    currency_code integer,
    currency_code_with integer,
    date_update date,
    currency_with_div numeric(18, 8),
    rate_updated_at timestamp
);
