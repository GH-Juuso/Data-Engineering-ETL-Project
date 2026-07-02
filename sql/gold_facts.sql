/* ============================================================
   GOLD LAYER -- FACTS ONLY
   Rail x Weather (Amsterdam Centraal)
   Runs in Azure SQL Database. Run AFTER gold_dimensions.sql.

   Sources (Silver, already loaded):
     dbo.train_services_silver   (one row per stop)   [your table]
     dbo.weather_silver          (one row per hour)   [teammate]

   NOTE ON TIME: train times in Silver are stored as naive UTC.
   Weather times are Amsterdam local. We convert trains to Amsterdam
   here so the hourly join lines up (see fact_stop_weather).

   NOTE ON WEATHER: no dim_weather table. Weather has a 1:1
   relationship with the hourly grain -- one fresh reading per hour,
   never reused across multiple fact rows -- so it doesn't behave
   like a dimension (no independent reuse, no many:1 join). It's
   pulled directly into fact_stop_weather as columns instead.

   Two facts, two different grains, two different questions:
     fact_stop          -- one row per stop   (the punctuality story)
     fact_stop_weather  -- one row per hour   (the weather association)
   They are NOT merged: merging would either duplicate the hourly
   weather/rate columns across every stop in that hour, or collapse
   the per-stop detail the punctuality finding depends on.

   Re-runnable: each table is dropped and recreated.
   ============================================================ */


/* ------------------------------------------------------------
   1. fact_stop  -- one row per stop (raw punctuality grain)
      Keeps the "trains are punctual" finding visible in Power BI.
      The median delay is ~0; that IS a result, so we keep every stop.
   ------------------------------------------------------------ */

CREATE OR ALTER PROCEDURE dbo.refresh_fact_stop
AS
BEGIN
    SET NOCOUNT ON;

    IF OBJECT_ID('dbo.fact_stop', 'U') IS NOT NULL
        DROP TABLE dbo.fact_stop;

    SELECT
        s.stop_id,
        s.service_id,
        st.service_type_key,
        ds.station_key,
        -- Amsterdam-local date key for joining to dim_date
        CONVERT(INT, FORMAT(
            CONVERT(DATETIME2,
                COALESCE(s.departure_time, s.arrival_time)
                AT TIME ZONE 'UTC' AT TIME ZONE 'Central European Standard Time'
            ), 'yyyyMMdd'
        )) AS date_key,
        DATEPART(HOUR,
            CONVERT(DATETIME2,
                COALESCE(s.departure_time, s.arrival_time)
                AT TIME ZONE 'UTC' AT TIME ZONE 'Central European Standard Time'
            )
        ) AS stop_time_hour_local,
        s.arrival_delay,
        s.departure_delay,
        s.is_cancelled,
        -- a stop counts as "delayed" if departure delay exceeds the threshold
        CASE WHEN s.departure_delay > 3 THEN 1 ELSE 0 END AS is_delayed,
        s.source_year
    INTO dbo.fact_stop
    FROM dbo.silver_train_services_asd s
    LEFT JOIN dbo.dim_station     ds ON ds.station_code  = s.station_code
    LEFT JOIN dbo.dim_service_type st ON st.service_type = s.service_type;

END;
GO



/* ------------------------------------------------------------
   2. fact_stop_weather  -- one row per STATION-HOUR (the analysis grain)
      Aggregates fact_stop to the hour and pulls weather in directly
      as columns (no dim_weather -- see note above).
      This is the table the weather association analysis uses.
   ------------------------------------------------------------ */

CREATE OR ALTER PROCEDURE dbo.refresh_fact_stop_weather
AS
BEGIN
    SET NOCOUNT ON;

    IF OBJECT_ID('dbo.fact_stop_weather', 'U') IS NOT NULL
        DROP TABLE dbo.fact_stop_weather;

    WITH hourly AS (
        SELECT
            f.station_key,
            f.date_key,
            f.stop_time_hour_local,
            COUNT(*) AS n_stops,
            AVG(CAST(f.departure_delay AS FLOAT)) AS mean_departure_delay,
            -- delay rate = share of running stops delayed > 3 min
            AVG(CASE WHEN f.is_cancelled = 0
                     THEN CAST(f.is_delayed AS FLOAT) END) AS delay_rate,
            -- cancel rate = share of stops cancelled
            AVG(CAST(f.is_cancelled AS FLOAT)) AS cancel_rate
        FROM dbo.fact_stop f
        WHERE f.date_key IS NOT NULL
        GROUP BY f.station_key, f.date_key, f.stop_time_hour_local
    )
    SELECT
        h.station_key,
        h.date_key,
        h.stop_time_hour_local,
        h.n_stops,
        h.mean_departure_delay,
        h.delay_rate,
        h.cancel_rate,
        -- weather columns joined straight onto the fact (no dim_weather)
        w.temperature_2m,
        w.rain,
        w.snowfall,
        w.precipitation,
        w.wind_speed_10m,
        w.snow_depth
    INTO dbo.fact_stop_weather
    FROM hourly h
    LEFT JOIN dbo.silver_weather w
           ON  CONVERT(INT, CONVERT(CHAR(8), w.[time], 112)) = h.date_key
          AND  DATEPART(HOUR, w.[time])                      = h.stop_time_hour_local;

END;
GO

/* ------------------------------------------------------------
   3. fact_disruption  -- one row per reported disruption (raw disruption grain)
   ------------------------------------------------------------ */

CREATE OR ALTER PROCEDURE dbo.refresh_fact_disruption
AS
BEGIN
    SET NOCOUNT ON;

    /* Create table if it does not exist */
    IF OBJECT_ID('dbo.fact_disruption', 'U') IS NULL
    BEGIN
        CREATE TABLE dbo.fact_disruption (
            disruption_id INT PRIMARY KEY,
            source_id INT,
            affected_route NVARCHAR(MAX),
            affected_train_line_qty INT,
            cause NVARCHAR(50),
            cause_group NVARCHAR(50),
            d_date INT,
            d_time INT,
            duration_minutes INT
        );
    END;

    /* Store previous row count */
    DECLARE @old_rows INT;

    SELECT @old_rows = COUNT(*)
    FROM dbo.fact_disruption;

    /* Delete old records */
    DELETE FROM dbo.fact_disruption;

    /* Insert refreshed records */
    INSERT INTO dbo.fact_disruption (
        disruption_id,
        source_id,
        affected_route,
        affected_train_line_qty,
        cause,
        cause_group,
        d_date,
        d_time,
        duration_minutes
    )
    SELECT
        ROW_NUMBER() OVER (ORDER BY start_time, source_id) AS disruption_id,
        COALESCE(source_id, 9999999) AS source_id,
        COALESCE(lines_names, 'missing') AS affected_route,
        COALESCE(affected_lines, 0) AS affected_train_line_qty,
        COALESCE(cause_en, 'undefined') AS cause,
        COALESCE(cause_group, 'undefined') AS cause_group,
        CONVERT(INT, FORMAT(
            start_time AT TIME ZONE 'UTC'
                       AT TIME ZONE 'Central European Standard Time',
            'yyyyMMdd'
        )) AS d_date,
        DATEPART(HOUR,
            start_time AT TIME ZONE 'UTC'
                       AT TIME ZONE 'Central European Standard Time'
        ) AS d_time,
        duration_minutes
    FROM dbo.silver_disruption
    WHERE 
        lines_names LIKE '%Amsterdam Centraal%'
        AND start_time >= '2023-01-01';
END;
GO


/* ------------------------------------------------------------
   3. Validation
   ------------------------------------------------------------ */
SELECT 'fact_stop' AS tbl, COUNT(*) AS rows FROM dbo.fact_stop
UNION ALL SELECT 'fact_stop_weather', COUNT(*) FROM dbo.fact_stop_weather;
UNION ALL SELECT 'fact_disruption', COUNT(*) FROM dbo.fact_disruption;

-- weather join coverage (should be high if timezones line up)
SELECT
    COUNT(*) AS total_hours,
    SUM(CASE WHEN temperature_2m IS NOT NULL THEN 1 ELSE 0 END) AS matched_weather,
    CAST(SUM(CASE WHEN temperature_2m IS NOT NULL THEN 1 ELSE 0 END) AS FLOAT)
        / NULLIF(COUNT(*),0) AS match_rate
FROM dbo.fact_stop_weather;
