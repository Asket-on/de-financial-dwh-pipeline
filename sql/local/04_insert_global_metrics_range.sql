insert into dwh_global_metrics (
    date_update,
    currency_from,
    amount_total,
    amount_usd_total,
    transaction_count
)
select
    date(t.transaction_dt) as date_update,
    t.currency_code as currency_from,
    sum(t.amount) as amount_total,
    sum(t.amount * c.currency_with_div) as amount_usd_total,
    count(*) as transaction_count
from staging_transactions as t
left join staging_currency_rates_current as c
    on t.currency_code = c.currency_code
    and date(t.transaction_dt) = c.date_update
where date(t.transaction_dt) between :start_date and :end_date
group by
    date(t.transaction_dt),
    t.currency_code;
