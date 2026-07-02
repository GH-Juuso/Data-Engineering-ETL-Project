# ----- SETUP -----

import pandas as pd
from pathlib import Path
from sqlalchemy import create_engine, text
from sqlalchemy.dialects.mssql import DATETIME2
import urllib.parse
from urllib.parse import quote_plus

def main(verbose:bool = False):

    ROOT_DIR = Path(__file__).parent.parent
    BRONZE_DIR = ROOT_DIR / "data/bronze/train_services"

    CREDS_FILE = ROOT_DIR / "private/credentials.csv"
    SILVER_REJECTED_DIR = ROOT_DIR / "data/silver/rejected"
    SILVER_REJECTED_DIR.mkdir(parents=True, exist_ok=True)

    if verbose: print("BRONZE_DIR:", BRONZE_DIR.resolve())
    if verbose: print("CREDS_FILE:", CREDS_FILE.resolve())

    YEARS = ["2023", "2024", "2025"]

    # --- scope ---
    STATION_CODES = ["ASD"]
    ALLOWED_SERVICE_TYPES = ["sprinter", "stoptrein"]

    KEEP = [
        "Stop:RDT-ID", "Service:RDT-ID", "Service:Type",
        "Stop:Station code", "Stop:Station name",
        "Stop:Arrival time", "Stop:Arrival delay",
        "Stop:Departure time", "Stop:Departure delay",
        "Stop:Departure cancelled", "Stop:Arrival cancelled",
    ]

    # --- target table ---
    SILVER_SCHEMA = "dbo"
    SILVER_TABLE = "silver_train_services_asd"

    # Check the files exist
    for y in YEARS:
        f = BRONZE_DIR / f"services-{y}.csv.gz"
        if verbose: print(f"{f.name}: exists={f.exists()}")

    # ----- BULD CONNECTION -----
    #creds = pd.read_csv(CREDS_FILE).set_index("key")["value"].to_dict()

    #server   = creds["AZURE_SQL_SERVER"]
    #database = creds["AZURE_SQL_DATABASE"]
    #username = creds["AZURE_SQL_USER"]
    #password = creds["AZURE_SQL_PASSWORD"]

    #odbc_str = (
    #    "DRIVER={ODBC Driver 18 for SQL Server};"
    #    f"SERVER={server};"
    #    f"DATABASE={database};"
    #    f"UID={username};"
    #    f"PWD={password};"
    #    "Encrypt=yes;TrustServerCertificate=no;Connection Timeout=30;"
    #)
    #engine = create_engine(
    #    "mssql+pyodbc:///?odbc_connect=" + urllib.parse.quote_plus(odbc_str)
    #)

    try:
        credentials = pd.read_csv(CREDS_FILE)
    except FileNotFoundError:
        if verbose: print("Failed to load credentials: credentials.csv not found")
    except:
        if verbose: print("Failed to load credentials: Unknown reason")


    # ----- BUILDING CONNECTION STRING -----
    connection_string = (
        "DRIVER={ODBC Driver 18 for SQL Server};"
        f"SERVER={credentials.loc[0, "server_name"]};"
        f"DATABASE={credentials.loc[0, "database_name"]};"
        f"UID={credentials.loc[0, "username"]};"
        f"PWD={credentials.loc[0, "password"]};"
        "TrustServerCertificate=yes;"
    )
    connection_url = "mssql+pyodbc:///?odbc_connect=" + quote_plus(connection_string)
    engine = create_engine(connection_url, fast_executemany=True)

    # Connection test
    with engine.connect() as conn:
        if verbose: print("Connection OK, SELECT 1 =>", conn.execute(text("SELECT 1")).scalar())


    # ----- CLEANING FUNCTION -----
    def clean_one_year(path, chunksize=200_000):
        # read + filter (chunked, so the whole year never sits in memory) ---
        parts = []
        for chunk in pd.read_csv(path, compression="gzip", usecols=KEEP, chunksize=chunksize):
            type_lower = chunk["Service:Type"].str.strip().str.lower()
            mask = (
                chunk["Stop:Station code"].isin(STATION_CODES)
                & type_lower.isin(ALLOWED_SERVICE_TYPES)
            )
            parts.append(chunk[mask])

        df = pd.concat(parts, ignore_index=True)

        # --- type ---
        for col in ["Stop:Arrival time", "Stop:Departure time"]:
            df[col] = pd.to_datetime(df[col], errors="coerce", utc=True)
        for col in ["Stop:Arrival delay", "Stop:Departure delay"]:
            df[col] = pd.to_numeric(df[col], errors="coerce")

        # --- cancellation flag ---
        df["is_cancelled"] = (
            df["Stop:Departure cancelled"].fillna(False).astype(bool)
            | df["Stop:Arrival cancelled"].fillna(False).astype(bool)
        )

        # --- separate malformed rows ---
        no_time = df["Stop:Arrival time"].isna() & df["Stop:Departure time"].isna()
        malformed = no_time & ~df["is_cancelled"]
        return df[~malformed].copy(), df[malformed].copy()


    # ----- CLEANING STEPS FOR 3 YEARS 2023-2025 -----

    clean_parts, rejected_parts = [], []

    for y in YEARS:
        path = BRONZE_DIR / f"services_{y}.csv.gz"
        clean, rejected = clean_one_year(path)
        clean["source_year"] = y       # keep track of which file each row came from
        clean_parts.append(clean)
        rejected_parts.append(rejected)
        if verbose: print(f"{y}: clean={len(clean):>7}  rejected={len(rejected)}")

    silver_clean = pd.concat(clean_parts, ignore_index=True)
    rejected_all = pd.concat(rejected_parts, ignore_index=True)
    if verbose: print("\nTOTAL clean rows:", len(silver_clean))


    # ----- VALIDATION CHECK ON THE COMBINED DATA -----
    checks = {}
    checks["total_rows"] = len(silver_clean)
    checks["null_stop_ids"] = silver_clean["Stop:RDT-ID"].isna().sum()
    checks["duplicate_stop_ids"] = silver_clean["Stop:RDT-ID"].duplicated().sum()
    checks["negative_dep_delays"] = (silver_clean["Stop:Departure delay"] < 0).sum()

    running = silver_clean[~silver_clean["is_cancelled"]]
    missing_dep = running[running["Stop:Departure delay"].isna()]

    # Split "missing departure delay" into expected (terminus) vs genuinely suspect
    checks["terminus_stops_no_departure"] = missing_dep["Stop:Arrival delay"].notna().sum()
    checks["suspect_missing_both_delays"] = missing_dep["Stop:Arrival delay"].isna().sum()

    if verbose: pd.Series(checks)




    """
    **Reading the checks:**
    - `duplicate_stop_ids = 0` → `Stop:RDT-ID` is globally unique across all years,
    so `stop_id` alone is a valid key (no need for year+id).
    - `negative_dep_delays = 0` → delays are floored at 0 (a negative would be suspect).
    - `terminus_stops_no_departure` → stops with no departure delay but a valid arrival
    delay. These are **terminus arrivals** (train ends at ASD) — expected, not errors.
    The hourly join falls back to arrival time for these, so they're not lost.
    - `suspect_missing_both_delays` → rows missing *both* delays. Should be ~0; if not,
    those are the genuinely questionable rows worth investigating.
    """


    # ----- RENAME COLUMNS FOR SQL  -----
    rename_map = {
        "Stop:RDT-ID": "stop_id",
        "Service:RDT-ID": "service_id",
        "Service:Type": "service_type",
        "Stop:Station code": "station_code",
        "Stop:Station name": "station_name",
        "Stop:Arrival time": "arrival_time",
        "Stop:Arrival delay": "arrival_delay",
        "Stop:Departure time": "departure_time",
        "Stop:Departure delay": "departure_delay",
        "Stop:Departure cancelled": "departure_cancelled",
        "Stop:Arrival cancelled": "arrival_cancelled",
        "is_cancelled": "is_cancelled",
        "source_year": "source_year",
    }
    silver_sql = silver_clean.rename(columns=rename_map)[list(rename_map.values())]

    # Add a naive UTC load timestamp (SQL Server DATETIME2 stores no tz)
    silver_sql["loaded_at"] = pd.Timestamp.now(tz="UTC").tz_localize(None)

    # Strip timezone from the datetime columns (values stay UTC, just lose the tz label)
    for col in ["arrival_time", "departure_time"]:
        if silver_sql[col].dt.tz is not None:
            silver_sql[col] = silver_sql[col].dt.tz_localize(None)

    if verbose: display(silver_sql.info())
    if verbose: silver_sql.head()


    # ----- WRITE TO AZURE  -----

    # Force datetime columns to DATETIME2 (not SQL Server's special TIMESTAMP type)
    sql_dtypes = {
        "arrival_time": DATETIME2(),
        "departure_time": DATETIME2(),
        "loaded_at": DATETIME2(),
    }

    with engine.begin() as conn:
        silver_sql.to_sql(
            SILVER_TABLE, con=conn,
            schema=SILVER_SCHEMA,
            if_exists="replace",
            index=False,
            chunksize=100,
            method="multi",
            dtype=sql_dtypes,
        )
    if verbose: print(f"Wrote {len(silver_sql)} rows to {SILVER_SCHEMA}.{SILVER_TABLE}")


    # ----- VERIFY AND READ  -----

    with engine.connect() as conn:
        n = conn.execute(text(f"SELECT COUNT(*) FROM {SILVER_SCHEMA}.{SILVER_TABLE}")).scalar()
    if verbose: print(f"Rows in {SILVER_SCHEMA}.{SILVER_TABLE}: {n}")

    # Row count per year, read back from the DB
    pd.read_sql(
        f"SELECT source_year, COUNT(*) AS n FROM {SILVER_SCHEMA}.{SILVER_TABLE} "
        f"GROUP BY source_year ORDER BY source_year", engine
    )

    # ----- WRITE REJECTED ROWS  -----

    if len(rejected_all):
        # add a naive UTC load timestamp (consistent with the DB write)
        rejected_out = rejected_all.copy()
        rejected_out["loaded_at"] = pd.Timestamp.now(tz="UTC").tz_localize(None)

        # WRITE TO CSV
        rejected_out.to_csv(SILVER_REJECTED_DIR / "train_services_rejected.csv", index=False)

        if verbose: print(f"Wrote {len(rejected_out)} rejected rows to {SILVER_REJECTED_DIR}")
    else:
        if verbose: print("No rejected rows to write")

if __name__ == "__main__":
    main()
