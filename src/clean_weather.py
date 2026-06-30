# %% Import and set up directories

# Import necessary libraries
import sys
import pandas as pd
from pathlib import Path
from sqlalchemy import create_engine
from sqlalchemy import engine
from urllib.parse import quote_plus

# Project root and data directories
PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = PROJECT_ROOT / "data"
SILVER_DIR = DATA_DIR / "silver"
SILVER_DIR.mkdir(parents=True, exist_ok=True)
BRONZE_DIR = DATA_DIR / "bronze"
CREDENTIALS_FILE = PROJECT_ROOT / "private/credentials.csv"
print(f"Project root set to: {PROJECT_ROOT.resolve()}")

if not CREDENTIALS_FILE.exists():
    print(f"Could not find credentials at: {CREDENTIALS_FILE}")
    print("Aborting disruptions_bronze_to_silver.py...")
    sys.exit(1)

# Input and output files
input_file = BRONZE_DIR / "weather_data_hourly.csv"
output_file = SILVER_DIR / "cleaned_weather_data_hourly.csv"


# %% Read, clean and sort the DataFrame

# Read the raw weather data
hourly_df = pd.read_csv(input_file)

# Convert the "time" column to datetime format
hourly_df["time"] = pd.to_datetime(
    hourly_df["time"],
    errors="coerce"
)

# Convert the relevant columns to numeric, coercing errors to NaN
cols = [
    "temperature_2m",
    "rain",
    "snowfall",
    "snow_depth",
    "precipitation",
    "wind_speed_10m",
]
hourly_df[cols] = hourly_df[cols].apply(
    pd.to_numeric,
    errors="coerce"
)

# Remove duplicates based on the "time" column, keeping the first occurrence
silver_times = ( 
    hourly_df 
    .sort_values("time",ascending=True
    ) 
    .drop_duplicates(subset=["time"], keep="first") 
    .reset_index(drop=True)
)


# %% Run data quality checks
# Check for null values in the DataFrame
if silver_times.isnull().any().any():
    print("Warning: Null values found.")
else:
    print("No null values found.")

# Check for duplicate dates in the "time" column
duplicates = silver_times["time"].duplicated().sum()
print(f"Duplicate dates: {duplicates}")


# %% Save the cleaned DataFrame to CSV
silver_times.to_csv(output_file, index=False)


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
    f"SERVER={credentials.loc[0, 'server_name']};"
    f"DATABASE={credentials.loc[0, 'database_name']};"
    f"UID={credentials.loc[0, 'username']};"
    f"PWD={credentials.loc[0, 'password']};"
    "TrustServerCertificate=yes;"
)
connection_url = "mssql+pyodbc:///?odbc_connect=" + quote_plus(connection_string)
engine = create_engine(connection_url, fast_executemany=True)


# %%
# ----- WRITING SILVER DATAFRAME TO DATABASE -----
import time
start = time.time()

table_name = "silver_weather"

with engine.connect() as conn:
    silver_times.to_sql(table_name, engine, if_exists="replace", index=False)

print(f"Writing dbo.{table_name} to {credentials.loc[0, 'server_name']} - {credentials.loc[0, 'database_name']} took {time.time() - start:.2f}s")

