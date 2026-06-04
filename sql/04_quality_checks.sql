-- Check 1: transaction identifiers should be present.
select count(*) as missing_operation_ids
from staging.transactions
where operation_id is null;

-- Check 2: amounts should be non-negative.
select count(*) as negative_amounts
from staging.transactions
where amount < 0;

-- Check 3: all mart rows should have exchange-rate coverage.
select count(*) as missing_exchange_rates
from dwh.global_metrics
where amount_usd_total is null;

-- Check 4: mart grain should be unique.
select date_update, currency_from, count(*) as rows_at_grain
from dwh.global_metrics
group by date_update, currency_from
having count(*) > 1;

-- Check 5: deterministic deduplication should leave one current rate per grain.
select currency_code, currency_code_with, date_update, count(*) as rows_at_grain
from staging.currency_rates_current
group by currency_code, currency_code_with, date_update
having count(*) > 1;

-- Check 6: joining current rates should preserve transaction-level row count.
select
    count(*) - count(distinct transactions.operation_id) as join_fanout_rows
from staging.transactions as transactions
left join staging.currency_rates_current as rates
    on transactions.currency_code = rates.currency_code
    and cast(transactions.transaction_dt as date) = rates.date_update;
