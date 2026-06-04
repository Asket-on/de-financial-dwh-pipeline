delete from staging_currency_rates_current;

insert into staging_currency_rates_current (
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
    from staging_currencies as currencies
)
where rn = 1;
