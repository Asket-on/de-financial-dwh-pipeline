delete from dwh_global_metrics
where date_update between :start_date and :end_date;
