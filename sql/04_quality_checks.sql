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
