create schema if not exists dwh;

create table if not exists dwh.global_metrics (
    date_update date,
    currency_from integer,
    amount_total numeric(18, 4),
    amount_usd_total numeric(18, 4),
    transaction_count integer
);
