import time
import sys
from pathlib import Path
import pandas as pd
from sqlalchemy import create_engine, text
from sqlalchemy.dialects.mssql import DATETIME2
import urllib.parse
from urllib.parse import quote_plus

import disruptions_bronze_to_silver
import clean_weather
import silver_train_services
import dim_date

def main(verbose:bool = False):

    total_time = time.time()

    ## b2s
    b2s_time = time.time()
    print("███████████████████████████████████████████████████████████████")
    print("██ Processing: Bronze to Silver...             (~15 minutes) ██")
    print("███████████████████████████████████████████████████████████████")

    start = time.time()
    print("██ Processing disruptions dataset...", end=" ")
    disruptions_bronze_to_silver.main(verbose)
    print(f"OK! ({time.time() - start:.2f}s)")

    start = time.time()
    print("██ Processing train_services_asd dataset...", end=" ")
    silver_train_services.main(verbose)
    print(f"OK! ({time.time() - start:.2f}s)")

    start = time.time()
    print("██ Processing weather_hourly dataset...", end=" ")
    clean_weather.main(verbose)
    print(f"OK! ({time.time() - start:.2f}s)")

    print("██▄▀▄▀▄▀▄▀▄▀▄▀▄▀▄▀▄▀▄▀▄▀▄▀▄▀▄▀▄▀▄▀▄▀▄▀▄▀▄▀▄▀▄▀▄▀▄▀██ ..Done! ██")
    print(f"██ Bronze to Silver - Total Time {time.time() - b2s_time:.2f}s")
    print(f"██                    Total Time {(time.time() - b2s_time)/60:.2f}min")
    print("███████████████████████████████████████████████████████████████")

    print() #4 lines

    ROOT_DIR = Path(__file__).parent.parent
    SQL_DIR = ROOT_DIR / "sql"
    CREDS_FILE = ROOT_DIR / "private/credentials.csv"

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

    connection_ok = False
    with engine.connect() as conn:
        if verbose:
            if conn.execute(text("SELECT 1")).scalar():
                print("██ Connection OK!")
                connection_ok = True
            else:
                print("██ Connection Failed!")

    ## s2g
    s2g_time = time.time()

    print("███████████████████████████████████████████████████████████████")
    print("██ Processing: Silver to Gold...        (Less then a minute) ██")
    print("███████████████████████████████████████████████████████████████")

    with engine.connect() as conn:
        if conn.execute(text("SELECT 1")).scalar():
            print(f"██ Server   : {credentials.loc[0, "server_name"]}")
            print(f"██ Database : {credentials.loc[0, "database_name"]}")
            print("██ Connection OK!")
            print("██ ------------------------------------------------------------")
        else:
            print("██ Connection Failed!")
            print("██")
            print("██ Aborting...")
            print("███████████████████████████████████████████████████████████████")
            sys.exit(1)


    ### DIMS ####################################
    start = time.time()
    print("██ ■■■■ Generating Dim-tables...")

    with engine.connect() as conn:
        print("██ ►► Running SQL 'gold_dimensions.sql'...", end=" ")
        sql = (SQL_DIR / "gold_dimensions.sql").read_text()
        conn.execute(text(sql))
        conn.commit()
    dim_date.main(verbose)
    print(f"OK! ({time.time() - start:.2f}s)")
    #######################################

    #######################################
    start = time.time()
    print("██ ■■■■ Generating Fact-tables...")

    with engine.connect() as conn:
        print("██ ►► Running SQL 'proc_disruptions_silver_to_gold.sql'...", end=" ")
        sql = (SQL_DIR / "proc_disruptions_silver_to_gold.sql").read_text()
        conn.execute(text(sql))
        conn.commit()
        print(f"OK!")

        print("██ ►► Execute USP 'refresh_fact_disruption'...", end=" ")
        conn.execute(text("EXEC refresh_fact_disruption"))
        conn.commit()
        print(f"OK!")
    #######################################

    #######################################
    print("██ ►► Running SQL 'gold_facts.sql'...", end=" ")
    with engine.connect() as conn:
        sql = (SQL_DIR / "gold_facts.sql").read_text()
        conn.execute(text(sql))
        conn.commit()
        print(f"OK!")

    print(f"██    ■ Fact-tables ({time.time() - start:.2f}s)")
    #######################################


    print("██▄▀▄▀▄▀▄▀▄▀▄▀▄▀▄▀▄▀▄▀▄▀▄▀▄▀▄▀▄▀▄▀▄▀▄▀▄▀▄▀▄▀▄▀▄▀▄▀██ ..Done! ██")
    print(f"██ Silver to Gold - Total Time {time.time() - s2g_time:.2f}s")
    print(f"██                  Total Time {(time.time() - s2g_time)/60:.2f}min")
    print("███████████████████████████████████████████████████████████████")

    print()

    import validation_silver_disruptions
    import validation_silver_train_services_asd
    import validation_silver_weather

    validation_start = time.time()
    print("███████████████████████████████████████████████████████████████")
    print("██ Validating tables...                 (Less then a minute) ██")
    print("███████████████████████████████████████████████████████████████")

    print("██ Running validation_silver_disruptions...", end=" ")
    start = time.time()
    validation_silver_disruptions.main()
    print(f"OK! ({time.time() - start:.2f}s)")

    print("██ Running validation_silver_train_services_asd...", end=" ")
    start = time.time()
    validation_silver_train_services_asd.main()
    print(f"OK! ({time.time() - start:.2f}s)")

    print("██ Running validation_silver_weather...", end=" ")
    start = time.time()
    validation_silver_weather.main()
    print(f"OK! ({time.time() - start:.2f}s)")

    print("██ Running SQL 'fact_table_validations'...", end=" ")
    start = time.time()
    with engine.connect() as conn:
        sql = (SQL_DIR / "fact_table_validations.sql").read_text()
        conn.execute(text(sql))
        conn.commit()
        conn.execute(text("EXEC check_fact_table_nulls"))
        conn.commit()
    print(f"OK! ({time.time() - start:.2f}s)")

    print("██▄▀▄▀▄▀▄▀▄▀▄▀▄▀▄▀▄▀▄▀▄▀▄▀▄▀▄▀▄▀▄▀▄▀▄▀▄▀▄▀▄▀▄▀▄▀▄▀██ ..Done! ██")
    print(f"██ Validations - Total Time {time.time() - validation_start:.2f}s")
    print(f"██               Total Time {(time.time() - validation_start)/60:.2f}min")
    print("███████████████████████████████████████████████████████████████")

    print()

    print("███████████████████████████████████████████████████████████████")
    print("██▄▀▄▀▄▀▄▀▄▀▄▀▄▀▄▀▄▀▄▀▄▀▄▀▄▀▄▀▄▀▄▀▄▀▄▀▄▀▄▀▄▀▄▀▄▀▄▀▄▀▄▀▄▀▄▀▄▀▄██")
    print(f"██ D-ETL Chain - Total Time {time.time() - total_time:.2f}s")
    print(f"██               Total Time {(time.time() - total_time)/60:.2f}min")
    print("██▄▀▄▀▄▀▄▀▄▀▄▀▄▀▄▀▄▀▄▀▄▀▄▀▄▀▄▀▄▀▄▀▄▀▄▀▄▀▄▀▄▀▄▀▄▀▄▀▄▀▄▀▄▀▄▀▄▀▄██")
    print("███████████████████████████████████████████████████████████████")

if __name__ == "__main__":
    main()
