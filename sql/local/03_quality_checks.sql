drop view if exists quality_check_results;

create view quality_check_results as
select
    'duplicate_current_currency_rates' as check_name,
    count(*) as failure_count
from (
    select currency_code, date_update
    from staging_currency_rates_current
    group by currency_code, date_update
    having count(*) > 1
)
union all
select
    'join_fanout_rows' as check_name,
    max(joined_rows - transaction_rows, 0) as failure_count
from (
    select
        (
            select count(*)
            from staging_transactions as transactions
            left join staging_currency_rates_current as rates
                on transactions.currency_code = rates.currency_code
                and date(transactions.transaction_dt) = rates.date_update
        ) as joined_rows,
        (select count(*) from staging_transactions) as transaction_rows
)
union all
select
    'duplicate_mart_grain' as check_name,
    count(*) as failure_count
from (
    select date_update, currency_from
    from dwh_global_metrics
    group by date_update, currency_from
    having count(*) > 1
)
union all
select
    'missing_exchange_rates' as check_name,
    count(*) as failure_count
from dwh_global_metrics
where amount_usd_total is null
union all
select
    'missing_operation_ids' as check_name,
    count(*) as failure_count
from staging_transactions
where operation_id is null
union all
select
    'negative_amounts' as check_name,
    count(*) as failure_count
from staging_transactions
where amount < 0;

drop view if exists profiling_results;

create view profiling_results as
select 'transactions.row_count' as metric_name, count(*) as metric_value
from staging_transactions
union all
select 'transactions.distinct_operation_ids', count(distinct operation_id)
from staging_transactions
union all
select 'transactions.min_date', min(date(transaction_dt))
from staging_transactions
union all
select 'transactions.max_date', max(date(transaction_dt))
from staging_transactions
union all
select 'currencies.raw_row_count', count(*)
from staging_currencies
union all
select 'currencies.current_row_count', count(*)
from staging_currency_rates_current
union all
select 'currencies.superseded_versions', (
    select count(*) from staging_currencies
) - (
    select count(*) from staging_currency_rates_current
);
