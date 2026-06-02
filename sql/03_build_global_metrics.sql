truncate table dwh.global_metrics;

insert into dwh.global_metrics (
    date_update,
    currency_from,
    amount_total,
    amount_usd_total,
    transaction_count
)
select
    cast(t.transaction_dt as date) as date_update,
    t.currency_code as currency_from,
    sum(t.amount) as amount_total,
    sum(t.amount * c.currency_with_div) as amount_usd_total,
    count(*) as transaction_count
from staging.transactions as t
left join staging.currencies as c
    on t.currency_code = c.currency_code
    and cast(t.transaction_dt as date) = c.date_update
group by
    cast(t.transaction_dt as date),
    t.currency_code;
