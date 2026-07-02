# Import and set up directories
# Import necessary libraries
import sys
import pandas as pd
from pathlib import Path
from sqlalchemy import create_engine
from sqlalchemy import engine
from urllib.parse import quote_plus


def main(verbose:bool = False):
    # Project root and data directories
    PROJECT_ROOT = Path(__file__).resolve().parents[1]
    CREDENTIALS_FILE = PROJECT_ROOT / "private/credentials.csv"
    if verbose: print(f"Project root set to: {PROJECT_ROOT.resolve()}")

    if not CREDENTIALS_FILE.exists():
        print(f"Could not find credentials at: {CREDENTIALS_FILE}")
        print("Aborting dim_date.py...")
        sys.exit(1)


    # Create a date range from the minimum to maximum date
    start = "2023-01-01"
    end = "2025-12-31"

    date_range = pd.date_range(start=start, end=end, freq="D")


    # Create a DataFrame for the date dimension
    dim_date = pd.DataFrame({
        "date": date_range
    })

    dim_date["date_key"] = dim_date["date"].dt.strftime("%Y%m%d").astype(int)
    dim_date["year"] = dim_date["date"].dt.year
    dim_date["month"] = dim_date["date"].dt.month
    dim_date["day"] = dim_date["date"].dt.day
    dim_date["week_of_year"] = dim_date["date"].dt.isocalendar().week.astype(int)
    dim_date["day_name"] = dim_date["date"].dt.day_name()
    dim_date["is_weekend"] = dim_date["date"].dt.weekday >= 5

    def get_season(month):
        if month in [12, 1, 2]:
            return "Winter"
        elif month in [3, 4, 5]:
            return "Spring"
        elif month in [6, 7, 8]:
            return "Summer"
        else:
            return "Autumn"

    dim_date["season"] = dim_date["month"].apply(get_season)


    #
    # ----- FETCHING CREDENTIALS -----
    try:
        credentials = pd.read_csv(CREDENTIALS_FILE)
    except FileNotFoundError:
        print("Failed to load credentials: credentials.csv not found")
    except:
        print("Failed to load credentials: Unknown reason")


    #
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


    #
    # ----- WRITING SILVER DATAFRAME TO DATABASE -----
    import time
    start = time.time()

    table_name = "dim_date"

    with engine.connect() as conn:
        dim_date.to_sql(table_name, engine, if_exists="replace", index=False)

    if verbose: print(f"Writing dbo.{table_name} to {credentials.loc[0, 'server_name']} - {credentials.loc[0, 'database_name']} took {time.time() - start:.2f}s")

if __name__ == "__main__":
    main()
