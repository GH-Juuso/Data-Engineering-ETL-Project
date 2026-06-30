# %%
# ----- SETUP -----
import sys
import pandas as pd
from pathlib import Path
from sqlalchemy import create_engine
from sqlalchemy import engine
from urllib.parse import quote_plus

ROOT_DIR = Path("../") # One step down..
CREDENTIALS_FILE = ROOT_DIR / "private/credentials.csv"
print(f"Project root set to: {ROOT_DIR.resolve()}")
print(CREDENTIALS_FILE.resolve())

# %%
# ----- LOAD ALL FILES INTO DATAFRAME -----
disruptions_bronze = pd.concat([
    pd.read_csv((ROOT_DIR / f"data/bronze/train_disruptions/disruptions-{year}.csv")).assign(source_file=f"disruptions-{year}.csv")
    for year in range(2011, 2026)
]).copy()

# %%
# ----- BRONZE -> CLEAN -> SILVER -----
disruptions_clean = disruptions_bronze.copy()

# %%
# ----- CREATING CLEANED COLUMNS -----
disruptions_clean["start_time_clean"] = pd.to_datetime(disruptions_clean["start_time"], errors="coerce")
disruptions_clean["end_time_clean"] = pd.to_datetime(disruptions_clean["end_time"], errors="coerce")
disruptions_clean["duration_minutes_clean"] = pd.to_numeric(disruptions_clean["duration_minutes"], errors="coerce")

disruptions_clean["cause_en_clean"] = disruptions_clean["cause_en"].str.strip().str.lower()
disruptions_clean["statistical_cause_en_clean"] = disruptions_clean["statistical_cause_en"].str.strip().str.lower()
disruptions_clean["cause_group_clean"] = disruptions_clean["cause_group"].str.strip().str.lower()

# %%
# ----- CREATING CALCULATED COLUMNS -----
disruptions_clean["affected_lines"] = disruptions_clean["rdt_lines_id"].str.split(",").str.len()
disruptions_clean["affected_stations"] = disruptions_clean["rdt_station_codes"].str.split(",").str.len()

# %%
# ----- CHERRY PICKING COLUMNS FOR THE SILVER DATAFRAME -----
disruption_silver = disruptions_clean[["source_file",
                                        "rdt_id",
                                        "rdt_lines",
                                        "affected_lines",
                                        "rdt_lines_id",
                                        "affected_stations",
                                        "rdt_station_names",
                                        "rdt_station_codes",
                                        "cause_en_clean",
                                        "statistical_cause_en_clean",
                                        "cause_group_clean",
                                        "start_time_clean",
                                        "end_time_clean",
                                        "duration_minutes"]].copy()

# %%
# ----- RENAMING COLUMNS -----
disruption_silver.rename(columns={"rdt_id" : "source_id",
                                    "rdt_lines": "lines_names",
                                    "rdt_lines_id": "lines_id",
                                    "rdt_station_names" : "station_names",
                                    "rdt_station_codes" : "station_codes",
                                    "cause_en_clean" : "cause_en",
                                    "statistical_cause_en_clean" : "statistical_cause_en",
                                    "cause_group_clean" : "cause_group",
                                    "start_time_clean" : "start_time",
                                    "end_time_clean" : "end_time"},
                                    inplace=True)

# %%
print((CREDENTIALS_FILE).resolve())

# %%
# ----- FETCHING CREDENTIALS -----
try:
    credentials = pd.read_csv(CREDENTIALS_FILE)
except FileNotFoundError:
    print("Failed to load credentials: credentials.csv not found")
except:
    print("Failed to load credentials: Unknown reason")


# %%
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

# %%
# ----- WRITING SILVER DATAFRAME TO DATABASE -----
import time
start = time.time()

table_name = "silver_disruption"

with engine.connect() as conn:
    disruption_silver.to_sql(table_name, engine, if_exists="replace", index=False)

print(f"Writing dbo.{table_name} to {credentials.loc[0, "server_name"]} - {credentials.loc[0, "database_name"]} took {time.time() - start:.2f}s")
