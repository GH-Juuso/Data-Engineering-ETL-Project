# Data Dictionary — Rijden de Treinen Train Services Archive

## Source overview

| Property | Value |
|---|---|
| **Dataset** | Train services in the Netherlands (train archive) |
| **Publisher** | Rijden de Treinen |
| **Source page** | https://www.rijdendetreinen.nl/en/open-data/train-archive |
| **Coverage** | All passenger train services in the Netherlands since 2019 |
| **Format** | CSV compressed with Gzip (`.csv.gz`) |
| **Granularity** | One row per **stop at a station** (each service contributes ≥2 rows: at least one departure and one arrival) |
| **File cadence** | Full-year files (e.g. `services-2019.csv.gz`) and per-month files from 2023 onward (e.g. `services-2025-01.csv.gz`); monthly files ~27–33 MiB, yearly files ~360–378 MiB |
| **License** | Creative Commons Attribution 4.0 (CC BY 4.0) — free for any purpose with attribution to Rijden de Treinen |

## Grain

Each row represents a **single stop of a single train service on a single date**. A service appears multiple times across rows because it stops at multiple stations. The `Service:RDT-ID` repeats across rows of the same service; `Stop:RDT-ID` is unique per row.

## Columns

### Service-level columns (repeat across all stops of the same service)

| Column | Meaning | Type | Notes |
|---|---|---|---|
| `Service:RDT-ID` | Unique identifier for the service | ID | Internal RDT ID, no meaning beyond uniquely identifying one service on one date. **Repeats** across rows for the same service. |
| `Service:Date` | Scheduled service date | Date | Schedule date, not necessarily the actual calendar date. A service departing 23:59 on 31 Jul and arriving 02:00 on 1 Aug has service date 31 Jul. Delays do not change the service date. |
| `Service:Type` | Service type | Text | E.g. Intercity, Sprinter, ICE International. |
| `Service:Company` | Operator | Text | Operating company, e.g. NS or Arriva. |
| `Service:Train number` | Train (service) number | Text/Int | Sometimes communicated to passengers (esp. international). A single service may have multiple train numbers (e.g. split trains or number changes at a major station). |
| `Service:Completely cancelled` | Whole service cancelled | Boolean | `true` when all stops of the service are cancelled (train does not run at all). |
| `Service:Partly cancelled` | Part of service cancelled | Boolean | `true` when one or more stops are cancelled (train does not run on part of the route). |
| `Service:Maximum delay` | Highest delay across the service | Integer (min) | Maximum delay in minutes across all stops of the service. |

### Stop-level columns (specific to each row)

| Column | Meaning | Type | Notes |
|---|---|---|---|
| `Stop:RDT-ID` | Unique identifier for the stop | ID | Unique per row. No further meaning. |
| `Stop:Station code` | Station code (abbreviation) | Text | Join key to the [stations dataset](https://www.rijdendetreinen.nl/en/open-data/stations). |
| `Stop:Station name` | Station name | Text | Human-readable station name. |
| `Stop:Arrival time` | Scheduled arrival time | DateTime (RFC 3339) | Empty when no arrival was scheduled (e.g. origin station). Timezone-aware. |
| `Stop:Arrival delay` | Arrival delay | Integer (min) | Empty when no arrival was scheduled. |
| `Stop:Arrival cancelled` | Arrival cancelled | Boolean | `true` if the arrival was cancelled; empty when no arrival was scheduled. |
| `Stop:Departure time` | Scheduled departure time | DateTime (RFC 3339) | Empty when no departure was scheduled (e.g. final station). Timezone-aware. |
| `Stop:Departure delay` | Departure delay | Integer (min) | Empty when no departure was scheduled. |
| `Stop:Departure cancelled` | Departure cancelled | Boolean | `true` if the departure was cancelled; empty when no departure was scheduled. |
| `Stop:Platform change` | Platform changed | Boolean | `true` when the actual platform differs from the planned one. |
| `Stop:Planned platform` | Scheduled platform | Text | Originally scheduled platform. |
| `Stop:Actual platform` | Actual platform | Text | Platform actually used. |

## Candidate keys

| Key | Use |
|---|---|
| `Stop:RDT-ID` | Primary key — unique per row (per stop). |
| `Service:RDT-ID` | Groups all stops belonging to one service on one date. |
| `Stop:Station code` | Foreign/join key to the stations lookup dataset (and to weather data via station lat/long). |

## Join notes (for Medallion pipeline use)

- **To weather data (Open-Meteo):** join on `Stop:Station code` → station lat/long (via stations lookup) and on the hour bucket derived from `Stop:Arrival time` / `Stop:Departure time`.
- **Time handling:** arrival/departure times are RFC 3339 (timezone-aware) — parse into proper timestamps in Silver; truncate to the hour for weather joins.
- **Delays:** in minutes; empty values are not zero — they mean *no scheduled arrival/departure at that stop*, so do not coalesce blindly to 0.
- **Booleans:** `true`/blank — standardize to real booleans in Silver.

## Limitations

- Service date ≠ actual calendar date around midnight crossings.
- One service may carry multiple train numbers (splits, mid-route renumbering).
- A row's empty arrival or departure fields indicate origin/terminus stops, not missing data.
- Source is NS real-time data; reflects observed operations rather than a corrected ground truth.
- Updated yearly, so the public archive is not real-time.

## Attribution

Source: Rijden de Treinen — https://www.rijdendetreinen.nl — licensed under CC BY 4.0.