truncate table staging.currency_rates_current;

insert into staging.currency_rates_current (
    source_row_number,
    currency_code,
    currency_code_with,
    date_update,
    currency_with_div,
    rate_updated_at
)
select
    source_row_number,
    currency_code,
    currency_code_with,
    date_update,
    currency_with_div,
    rate_updated_at
from (
    select
        currencies.*,
        row_number() over (
            partition by currency_code, currency_code_with, date_update
            order by rate_updated_at desc, source_row_number desc
        ) as rn
    from staging.currencies as currencies
) ranked
where rn = 1;

-- Bind :start_date and :end_date to the inclusive refresh window.
delete from dwh.global_metrics
where date_update between :start_date and :end_date;

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
left join staging.currency_rates_current as c
    on t.currency_code = c.currency_code
    and cast(t.transaction_dt as date) = c.date_update
where cast(t.transaction_dt as date) between :start_date and :end_date
group by
    cast(t.transaction_dt as date),
    t.currency_code;
