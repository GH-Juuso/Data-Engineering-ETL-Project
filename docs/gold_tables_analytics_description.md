# Fact Tables — Column Definitions and Business Questions

Reference document for Power BI report building and presentation.
All tables live in `dbo` schema in the Azure SQL Database.

---

## fact_stop
**Grain:** one row per train stop (a Sprinter calling at Amsterdam Centraal).
**Source:** `dbo.silver_train_services`
**Answers:** Business Question 1 — "Are ASD Sprinters punctual?"

| Column | Type | Description |
|---|---|---|
| `stop_id` | INT | Unique identifier for the stop. Natural key from the source (`Stop:RDT-ID`). One row per stop. |
| `service_id` | INT | The train run this stop belongs to (`Service:RDT-ID`). Multiple stops share one service. |
| `station_key` | INT (FK) | Foreign key to `dim_station`. Currently always `1` (Amsterdam Centraal). |
| `service_type_key` | INT (FK) | Foreign key to `dim_service_type`. Currently always `Sprinter`. |
| `date_key` | INT (FK) | Foreign key to `dim_date` (format `YYYYMMDD`). Represents the **calendar day** of the stop. |
| `stop_time_hour_local` | INT | Hour of day the stop occurred (0–23), in Amsterdam local time. **Not a FK** — used directly as a filter/axis in Power BI. Derive `is_peak` from this: hour IN (7,8,9,16,17,18). |
| `stop_ts_local` | DATETIME2 | Full timestamp of the stop in Amsterdam local time (minute precision). Use for traceability; the hourly analysis uses `stop_time_hour_local` instead. |
| `arrival_delay` | FLOAT | Arrival delay in minutes. NULL for origin stops (no arrival — train starts here). |
| `departure_delay` | FLOAT | Departure delay in minutes. NULL for terminus stops (no departure — train ends here). |
| `is_cancelled` | BIT | `1` if this stop was cancelled (arrival or departure). Not an error — a real disruption signal. |
| `is_delayed` | BIT | `1` if `departure_delay > 3` minutes. The 3-minute threshold matches NS's own punctuality standard. NULL if stop is cancelled (no delay to measure). |
| `source_year` | VARCHAR | The source year file this row came from (`2023`, `2024`, or `2025`). |

**Key notes for Power BI:**
- Filter to `is_cancelled = 0` for pure delay analysis; include `is_cancelled = 1` for disruption analysis.
- `arrival_delay` NULLs (~168k rows) are terminus stops — expected, not data errors.
- `departure_delay` NULLs are origin stops — same reason.
- Lead with `is_delayed` (rate-based) not raw delay values — the distribution is zero-dominated (median = 0), so averages are misleading.

---

## fact_stop_weather
**Grain:** one row per station-hour (Amsterdam Centraal, one hour).
**Source:** aggregated from `fact_stop` + joined from `dbo.weather_silver`
**Answers:** Business Question 2 — "Does weather relate to delay or cancellation rates?"

| Column | Type | Description |
|---|---|---|
| `station_key` | INT (FK) | Foreign key to `dim_station`. Currently always `1` (Amsterdam Centraal). |
| `date_key` | INT (FK) | Foreign key to `dim_date` (format `YYYYMMDD`). Represents the calendar day. |
| `stop_time_hour_local` | INT | Hour of day (0–23), Amsterdam local time. Same as in `fact_stop`. Use this as the shared grain key between `fact_stop` and `fact_stop_weather`. Derive `is_peak` here too: hour IN (7,8,9,16,17,18). |
| `n_stops` | INT | Number of Sprinter stops at ASD in this hour. Varies by hour (rush hour has more stops than midnight). Use as a weight when interpreting rates. |
| `mean_departure_delay` | FLOAT | Average departure delay in minutes across all stops that hour. **Treat with caution** — NULL when all stops that hour are terminus arrivals (no departure); misleading when the distribution is zero-dominated. Prefer `delay_rate`. |
| `delay_rate` | FLOAT | Share of *running* (not cancelled) stops that hour with departure delay > 3 min. Range 0.0–1.0 (e.g. `0.167` = 16.7% of trains delayed). The primary punctuality metric. |
| `cancel_rate` | FLOAT | Share of all stops that hour that were cancelled. Range 0.0–1.0. The primary disruption metric. |
| `temperature_2m` | FLOAT | Air temperature in °C measured at 2 metres above ground. Hourly, Amsterdam. |
| `rain` | FLOAT | Rainfall in mm that hour. |
| `snowfall` | FLOAT | New snowfall in cm that hour. |
| `precipitation` | FLOAT | Total precipitation that hour (rain + snow combined) in mm. Use this as the umbrella weather variable; don't sum it with `rain` or `snowfall` separately or you will double-count. |
| `wind_speed_10m` | FLOAT | Wind speed in km/h at 10 metres above ground. Hourly maximum. |
| `snow_depth` | FLOAT | Accumulated snow depth on the ground in cm. Better proxy for icy conditions than `snowfall` — even after snow stops falling, accumulated depth means ice/slipperiness persists. |

**Key notes for Power BI:**
- Hours with zero Sprinter stops at ASD are absent from this table (no row). This is correct — do not interpret gaps as missing data.
- `mean_departure_delay` is NULL for hours where all stops were terminus arrivals. Avoid this column as a headline metric; use `delay_rate` instead.
- `rain` and `precipitation` overlap — do not put both on the same chart axis. Use `precipitation` for the umbrella view; `rain`/`snowfall` only to distinguish precipitation type.
- `snow_depth` is often 0 in 2025 data (Amsterdam had minimal snowfall). If all values are 0 in your selected period, drop it from that chart.
- This table joins to `fact_disruption` via `date_key` + `stop_time_hour_local` for the cross-check page.

---

## fact_disruption
**Grain:** one row per ASD hour (hours that had at least one active disruption touching Amsterdam Centraal).
**Source:** `dbo.disruption_silver`, filtered and reshaped to hourly flags
**Answers:** Business Question 3 — "Do NS disruption labels agree with the weather finding?"

| Column | Type | Description |
|---|---|---|
| `date_key` | INT (FK) | Foreign key to `dim_date` (format `YYYYMMDD`). The calendar day of the hour. |
| `hour_ts` | DATETIME2 | The Amsterdam-local hour timestamp (e.g. `2025-01-15 08:00:00`). Use for joining to `fact_stop_weather` on date + hour. |
| `n_disruptions` | INT | Number of disruption events active at ASD during this hour (one event can span multiple hours). |
| `is_disrupted` | BIT | `1` if any disruption was active at ASD that hour, regardless of cause. |
| `is_weather_disrupted` | BIT | `1` if any active disruption that hour was labelled `cause_group = 'weather'` by NS. **This is 0 for all ASD hours in 2025** — the core triangulation finding. |

**Key notes for Power BI:**
- This table only contains hours where a disruption was active. Hours with no disruption have no row — use a LEFT JOIN from `fact_stop_weather` so non-disrupted hours show as `is_disrupted = 0`.
- `is_weather_disrupted = 0` for all ASD rows in 2025 is the finding, not a data error. It triangulates with the weather-delay null result from `fact_stop_weather`.
- The ASD filter uses exact-token matching on `rdt_station_codes` — Amsterdam Zuid (`ASDZ`) is excluded. Only true Amsterdam Centraal disruptions are here.

---

## dim_date
**Grain:** one row per calendar day.
**Built by:** teammate. Used as-is — not rebuilt in this pipeline.
**Joins to:** `fact_stop`, `fact_stop_weather`, `fact_disruption` via `date_key` (format `YYYYMMDD`).

| Column | Type | Description |
|---|---|---|
| `date_key` | INT (PK) | Surrogate key in `YYYYMMDD` format (e.g. `20230101`). Join target for all facts. |
| `date` | DATETIME2 | Full date timestamp (midnight). |
| `year` | INT | Calendar year. |
| `month` | INT | Month number (1–12). |
| `day` | INT | Day of month (1–31). |
| `week_of_year` | INT | ISO week number. |
| `day_name` | VARCHAR | Day of week name (e.g. `Monday`). |
| `is_weekend` | BIT | `1` for Saturday or Sunday. |
| `season` | VARCHAR | Season label (`Winter`, `Summer`, etc.). |

**Key note:** `dim_date` is at **daily** grain, not hourly. The hour-of-day lives as `stop_time_hour_local` (INT, 0–23) directly on each fact table — not in a separate dimension. Derive `is_peak` in Power BI as a calculated column or measure: `stop_time_hour_local IN (7, 8, 9, 16, 17, 18)`.

---

## dim_station
**Grain:** one row per station.
**Joins to:** `fact_stop`, `fact_stop_weather` via `station_key`.

| Column | Type | Description |
|---|---|---|
| `station_key` | INT (PK) | Surrogate key. |
| `station_code` | VARCHAR | NS station abbreviation code (e.g. `ASD` = Amsterdam Centraal). |
| `station_name` | VARCHAR | Full station name (e.g. `Amsterdam Centraal`). |
| `latitude` | FLOAT | Latitude used for the weather data join (52.37916 for ASD). |
| `longitude` | FLOAT | Longitude used for the weather data join (4.9001612 for ASD). |

**Scope note:** currently one row (ASD). Kept as a dimension for future multi-station enrichment.

---

## dim_service_type
**Grain:** one row per service type.
**Joins to:** `fact_stop` via `service_type_key`.

| Column | Type | Description |
|---|---|---|
| `service_type_key` | INT (PK) | Surrogate key. |
| `service_type` | VARCHAR | Service type name (e.g. `Sprinter`, `Stoptrein`). |

**Scope note:** currently two rows. Kept as a dimension so adding Intercity (Option 2 enrichment) is a filter widening, not a schema change.

---

## Derived measures (not stored columns — compute in Power BI)

These are not columns in any table but are used in the report:

| Measure | Formula | Used on |
|---|---|---|
| `is_peak` | `stop_time_hour_local IN (7,8,9,16,17,18)` | Both facts |
| `delay_rate_pct` | `delay_rate * 100` | Display as percentage |
| `cancel_rate_pct` | `cancel_rate * 100` | Display as percentage |
| `on_time_rate` | `1 - delay_rate` | Punctuality positive framing |
