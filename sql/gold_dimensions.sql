/* ============================================================
   GOLD LAYER -- DIMENSIONS ONLY
   Rail x Weather (Amsterdam Centraal)
   Runs in Azure SQL Database. Run BEFORE gold_facts.sql.

   Source (Silver, already loaded):
     dbo.silver_train_services (one row per stop)

   Re-runnable: each table is dropped and recreated.
   ============================================================ */


/* ------------------------------------------------------------
   1. dim_station  -- one row per station (lat/long for weather join)

   Scope note: currently a single row (ASD). Kept as a dimension
   rather than a fact column so a future multi-station enrichment
   is a data change, not a schema change.
   ------------------------------------------------------------ */
IF OBJECT_ID('dbo.dim_station', 'U') IS NOT NULL DROP TABLE dbo.dim_station;

CREATE TABLE dbo.dim_station (
    station_key    INT IDENTITY(1,1) PRIMARY KEY,
    station_code   VARCHAR(10)  NOT NULL UNIQUE,
    station_name   VARCHAR(100) NOT NULL,
    latitude       FLOAT NULL,    -- fill for the weather location
    longitude      FLOAT NULL     -- fill for the weather location
);

INSERT INTO dbo.dim_station (station_code, station_name, latitude, longitude)
SELECT DISTINCT
    station_code,
    MAX(station_name) AS station_name,
    CASE WHEN station_code = 'ASD' THEN 52.37916 ELSE NULL END,  -- Amsterdam Centraal (ASD)
    CASE WHEN station_code = 'ASD' THEN 4.9001612 ELSE NULL END
FROM dbo.silver_train_services
GROUP BY station_code;


/* ------------------------------------------------------------
   2. dim_service_type  -- currently only Sprinter, Stoptrein

   Scope note: kept so adding Intercity (Option 2 enrichment) is a filter widening, not a rebuild.
   ------------------------------------------------------------ */
IF OBJECT_ID('dbo.dim_service_type', 'U') IS NOT NULL DROP TABLE dbo.dim_service_type;

CREATE TABLE dbo.dim_service_type (
    service_type_key  INT IDENTITY(1,1) PRIMARY KEY,
    service_type      VARCHAR(50) NOT NULL UNIQUE
);

INSERT INTO dbo.dim_service_type (service_type)
SELECT DISTINCT service_type
FROM dbo.silver_train_services
WHERE service_type IS NOT NULL;

/* ------------------------------------------------------------
   3. Validation
   ------------------------------------------------------------ */
SELECT 'dim_station'       AS tbl, COUNT(*) AS rows FROM dbo.dim_station
UNION ALL SELECT 'dim_service_type', COUNT(*) FROM dbo.dim_service_type
UNION ALL SELECT 'dim_date',         COUNT(*) FROM dbo.dim_date;
