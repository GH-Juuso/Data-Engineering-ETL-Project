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
IF OBJECT_ID('dbo.fact_stop', 'U') IS NOT NULL DROP TABLE dbo.fact_stop;

SELECT
    s.stop_id,
    s.service_id,
    st.service_type_key,
    ds.station_key,
    -- -- Amsterdam-local date key for joining to dim_date, plus local stop hour kept in fact table
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
    -- a stop counts as "delayed" if departure delay exceeds the threshold (3 min)
    CASE WHEN s.departure_delay > 3 THEN 1 ELSE 0 END AS is_delayed,
    s.source_year
INTO dbo.fact_stop
FROM dbo.silver_train_services_asd s
LEFT JOIN dbo.dim_station ds      ON ds.station_code = s.station_code
LEFT JOIN dbo.dim_service_type st ON st.service_type  = s.service_type;


/* ------------------------------------------------------------
   2. fact_stop_weather  -- one row per STATION-HOUR (the analysis grain)
      Aggregates fact_stop to the hour and pulls weather in directly
      as columns (no dim_weather -- see note above).
      This is the table the weather association analysis uses.
   ------------------------------------------------------------ */
IF OBJECT_ID('dbo.fact_stop_weather', 'U') IS NOT NULL DROP TABLE dbo.fact_stop_weather;

WITH hourly AS (
    SELECT
        f.station_key,
        f.date_key,
        f.stop_time_hour_local,
        COUNT(*) AS n_stops,
        AVG(CAST(f.departure_delay AS FLOAT)) AS mean_departure_delay,

        -- delay rate = share of running stops delayed > 3 min
        AVG(CASE WHEN f.is_cancelled = 0 THEN CAST(f.is_delayed AS FLOAT) END) AS delay_rate,

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
    
    -- weather columns, joined straight onto the fact (no dim_weather)
    w.temperature_2m,
    w.rain,
    w.snowfall,
    w.precipitation,
    w.wind_speed_10m,
    w.snow_depth
INTO dbo.fact_stop_weather
FROM hourly h
LEFT JOIN dbo.silver_weather w
       ON CONVERT(INT, CONVERT(CHAR(8), w.[time], 112)) = h.date_key
      AND DATEPART(HOUR, w.[time]) = h.stop_time_hour_local;


/* ------------------------------------------------------------
   3. Validation
   ------------------------------------------------------------ */
SELECT 'fact_stop' AS tbl, COUNT(*) AS rows FROM dbo.fact_stop
UNION ALL SELECT 'fact_stop_weather', COUNT(*) FROM dbo.fact_stop_weather;

-- weather join coverage (should be high if timezones line up)
SELECT
    COUNT(*) AS total_hours,
    SUM(CASE WHEN temperature_2m IS NOT NULL THEN 1 ELSE 0 END) AS matched_weather,
    CAST(SUM(CASE WHEN temperature_2m IS NOT NULL THEN 1 ELSE 0 END) AS FLOAT)
        / NULLIF(COUNT(*),0) AS match_rate
FROM dbo.fact_stop_weather;
