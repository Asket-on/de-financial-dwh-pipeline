drop view if exists quality_check_results;

create view quality_check_results as
select
    'duplicate_currency_rates' as check_name,
    count(*) as failure_count
from (
    select currency_code, date_update
    from staging_currencies
    group by currency_code, date_update
    having count(*) > 1
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

