CREATE OR ALTER PROCEDURE check_fact_table_nulls
AS
BEGIN
    SET NOCOUNT ON;

    /* fact_stop */

    -- Count NULL values
    SELECT
        SUM(CASE WHEN stop_id IS NULL THEN 1 ELSE 0 END) AS null_stop_id_count,
        SUM(CASE WHEN service_id IS NULL THEN 1 ELSE 0 END) AS null_service_id_count,
        SUM(CASE WHEN date_key IS NULL THEN 1 ELSE 0 END) AS null_date_key_count
    FROM fact_stop;

    -- Rows containing NULL values
    ;WITH fact_stop_rows_with_null_values AS
    (
        SELECT *
        FROM fact_stop
        WHERE stop_id IS NULL
           OR service_id IS NULL
           OR date_key IS NULL
    )
    SELECT *
    FROM fact_stop_rows_with_null_values;


    /* fact_stop_weather */

    -- Count NULL values
    SELECT
        SUM(CASE WHEN station_key IS NULL THEN 1 ELSE 0 END) AS null_station_key_count,
        SUM(CASE WHEN date_key IS NULL THEN 1 ELSE 0 END) AS null_date_key_count
    FROM fact_stop_weather;

    -- Rows containing NULL values
    ;WITH fact_stop_weather_rows_with_null_values AS
    (
        SELECT *
        FROM fact_stop_weather
        WHERE station_key IS NULL
           OR date_key IS NULL
    )
    SELECT *
    FROM fact_stop_weather_rows_with_null_values;


    /* Disruptions */ 
    
    -- Count NULL values 
    SELECT 
        SUM(CASE WHEN source_id = 9999999 THEN 1 ELSE 0 END) AS default_source_id_count, 
        SUM(CASE WHEN affected_route = 'missing' THEN 1 ELSE 0 END) AS default_route_count, 
        SUM(CASE WHEN affected_train_line_qty <= 0 THEN 1 ELSE 0 END) AS default_line_qty_count, 
        SUM(CASE WHEN cause = 'undefined' THEN 1 ELSE 0 END) AS default_cause_count, 
        SUM(CASE WHEN cause_group = 'undefined' THEN 1 ELSE 0 END) AS default_cause_group_count, 
        SUM(CASE WHEN d_date IS NULL THEN 1 ELSE 0 END) AS null_d_date, 
        SUM(CASE WHEN d_time IS NULL THEN 1 ELSE 0 END) AS null_d_time 
     FROM fact_disruption; 
     
     -- Gather the rows with nulls into a CTE 
     WITH rows_with_default_values AS ( 
        SELECT * 
        FROM fact_disruption 
        WHERE source_id = 9999999 
            OR affected_route = 'missing' 
            OR affected_train_line_qty = 0 
            OR cause = 'undefined' 
            OR cause_group = 'undefined' 
       ) 
     SELECT * 
     FROM rows_with_default_values;
END;
GO

exec check_fact_table_nulls