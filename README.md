# Rail × Weather: a Medallion data pipeline

How does weather affect the punctuality of Dutch passenger trains — and how much
of that effect can we actually attribute to weather rather than just observe as a
correlation? This project ingests open train-stop data, open hourly weather data,
and open disruption-cause data, cleans and validates all three with Python,
models them into a Gold star schema, and reports the result in Power BI — all
organised as a Bronze / Silver / Gold Medallion architecture.

## Business questions

The Gold layer and the Power BI report answer:

1. Are delays and cancellations **associated** with rain, snow, wind, or
   temperature extremes? (service × weather)
2. Of the major disruptions NS reported, what share were **attributed** to
   weather, and do those line up with the hours we measured as adverse?
   (disruptions × weather)
3. How often do the two lenses **agree** — i.e. does a weather-flagged
   disruption coincide with both bad measured weather and elevated delays?
4. Which stations, operators, times of day and conditions are most
   weather-sensitive?

> **Important framing:** this is observational open data. Service × weather gives
> us *association*, not proof of cause. Disruption data gives us a stated cause
> but only for *reported major* events. The project's contribution is the honest
> **triangulation** of these two imperfect lenses, and a clear statement of where
> each one's limits lie. See `docs/analysis_scope_and_limitations.md`.

## Data sources

| Source | Provider | Type | Grain | Role | License |
|--------|----------|------|-------|------|---------|
| Train services | Rijden de Treinen | CSV.gz download | one row per train stop | main fact | CC BY 4.0 |
| Historical weather | Open-Meteo | REST API (JSON) | one row per station-hour | join to fact | open / free |
| Disruptions + causes | Rijden de Treinen | CSV download | one row per reported disruption | cause enrichment | CC BY 4.0 |
| Stations (lookup) | Rijden de Treinen | CSV | one row per station | coordinate bridge | CC BY 4.0 |

See `docs/source_description.md` for full schema, keys, limitations and the
fallback plan.

## Architecture

```
Sources ─► Bronze (raw + metadata) ─► Silver (clean, typed, validated) ─► Gold (star schema) ─► Power BI
```

See `docs/architecture.md` for what changes between each layer.

## Stack

- Python + Pandas — ingestion, profiling, cleaning, validation
- DuckDB — SQL staging, Gold model build, validation queries
- Parquet — Bronze and Silver storage
- Power BI — reporting from Gold only

## Repository layout

```
rail-weather/
├── README.md
├── config.py                     # central config: months, paths, thresholds, URLs
├── requirements.txt
├── docs/
│   └── source_description.md              # datasets, schema, keys, limitations
├── src/
│   ├── pipeline/                 # run-in-order scripts (one per ingest/clean/build step)
│   │   ├── ingest_weather.py        
│   │   ├── clean_weather.py             
│   │   ├── tbd.             
│   │   └── build_gold.py or tbd.            
│   └── utils/                    # shared helpers or tbd. if needed
├── notebooks/                    # exploration per cleaning
├── sql/
│   ├── gold/                     
│   └── validation/              
├── data/
│   ├── bronze/                   # raw ingested parquet (git-ignored)
│   ├── silver/                   # cleaned parquet + rejected/ (git-ignored)
│   └── gold/                     # star-schema tables + duckdb file (git-ignored)
└── powerbi/                      # .pbix, README, screenshots/
```

## Quick start

In short: create a virtual environment, install requirements, run the ingestion scripts to build Bronze, run the cleaning to build Silver, run the Gold build, then point Power BI at `data/gold/`.

## Team

Four members; every member owns Python cleaning or validation work. 

## Attribution

Train + disruption data © Rijden de Treinen (CC BY 4.0). Weather data © Open-Meteo.
