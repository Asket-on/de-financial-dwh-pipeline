#!/bin/sh
set -eu

START_DATE="${START_DATE:-2024-01-01}"
END_DATE="${END_DATE:-2024-01-02}"

psql -v ON_ERROR_STOP=1 -f sql/01_create_staging.sql
psql -v ON_ERROR_STOP=1 -f sql/02_create_dwh.sql

psql -v ON_ERROR_STOP=1 <<'SQL'
truncate table staging.transactions;
truncate table staging.currencies;
truncate table staging.currency_rates_current;
truncate table dwh.global_metrics;
SQL

psql -v ON_ERROR_STOP=1 <<'SQL'
\copy staging.transactions (operation_id, account_number_from, currency_code, country, status, transaction_type, amount, transaction_dt) from 'sample_data/transactions_sample.csv' with (format csv, header true);
\copy staging.currencies (currency_code, currency_code_with, date_update, currency_with_div, rate_updated_at) from 'sample_data/currencies_sample.csv' with (format csv, header true);
SQL

psql -v ON_ERROR_STOP=1 <<'SQL'
with numbered as (
    select
        ctid,
        row_number() over (
            order by currency_code, currency_code_with, date_update, rate_updated_at
        ) as source_row_number
    from staging.currencies
)
update staging.currencies as currencies
set source_row_number = numbered.source_row_number
from numbered
where currencies.ctid = numbered.ctid;
SQL

sed \
  -e "s/:start_date/'$START_DATE'/g" \
  -e "s/:end_date/'$END_DATE'/g" \
  sql/03_build_global_metrics.sql > /tmp/build_global_metrics.sql
psql -v ON_ERROR_STOP=1 -f /tmp/build_global_metrics.sql
psql -v ON_ERROR_STOP=1 -f sql/postgres_quality_assertions.sql

psql -v ON_ERROR_STOP=1 -P pager=off <<'SQL'
select
    date_update,
    currency_from,
    amount_total,
    amount_usd_total,
    transaction_count
from dwh.global_metrics
order by date_update, currency_from;
SQL

echo "postgres_warehouse=verified"
