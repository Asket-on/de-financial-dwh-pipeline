do $$
declare
    failure_count integer;
    mart_rows integer;
begin
    select count(*) into failure_count
    from staging.transactions
    where operation_id is null;
    if failure_count <> 0 then
        raise exception 'missing_operation_ids=%', failure_count;
    end if;

    select count(*) into failure_count
    from staging.transactions
    where amount < 0;
    if failure_count <> 0 then
        raise exception 'negative_amounts=%', failure_count;
    end if;

    select count(*) into failure_count
    from dwh.global_metrics
    where amount_usd_total is null;
    if failure_count <> 0 then
        raise exception 'missing_exchange_rates=%', failure_count;
    end if;

    select count(*) into failure_count
    from (
        select date_update, currency_from
        from dwh.global_metrics
        group by date_update, currency_from
        having count(*) > 1
    ) duplicate_mart_grain;
    if failure_count <> 0 then
        raise exception 'duplicate_mart_grain=%', failure_count;
    end if;

    select count(*) into failure_count
    from (
        select currency_code, currency_code_with, date_update
        from staging.currency_rates_current
        group by currency_code, currency_code_with, date_update
        having count(*) > 1
    ) duplicate_current_rates;
    if failure_count <> 0 then
        raise exception 'duplicate_current_currency_rates=%', failure_count;
    end if;

    select count(*) - count(distinct transactions.operation_id) into failure_count
    from staging.transactions as transactions
    left join staging.currency_rates_current as rates
        on transactions.currency_code = rates.currency_code
        and cast(transactions.transaction_dt as date) = rates.date_update;
    if failure_count <> 0 then
        raise exception 'join_fanout_rows=%', failure_count;
    end if;

    select count(*) into mart_rows
    from dwh.global_metrics;
    if mart_rows <> 3 then
        raise exception 'unexpected_mart_rows=%', mart_rows;
    end if;
end $$;
