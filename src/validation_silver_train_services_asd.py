# VALIDATION SCRIPT FOR THE DISRUPTION_SILVER DATASET

import pandas as pd
from pathlib import Path
from sqlalchemy import create_engine
from sqlalchemy import engine
from urllib.parse import quote_plus

#%%
# ----- SETUP DIRECTORIES AND CONNECT TO DATABASE -----

ROOT_DIR = Path("../") # One step down..
CREDENTIALS_FILE = ROOT_DIR / "private/credentials.csv"

try:
    credentials = pd.read_csv(CREDENTIALS_FILE)
except FileNotFoundError:
    print("Failed to load credentials: credentials.csv not found")
except:
    print("Failed to load credentials: Unknown reason")

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

#%%
# ----- FETCH DATA FROM DATABASE -----
silver_train_services_asd = pd.read_sql("SELECT * FROM silver_train_services_asd", engine)

#%%

validation_table = silver_train_services_asd #dont do a deep copy, a reference copy is good enough!
validation_result_dict = {}
validation_resuls_table_name = 'silver_train_services_asd_validation'
# %%
# ----- NUMBER OF ROWS
rows_total = len(validation_table)
validation_result_dict['rows_total'] = str(rows_total)

validation_result_dict.update({f"{k}_is_null": v for k, v in validation_table.isna().sum().to_dict().items()})

# %%
# ----- WRITING silver_disruption_validation TO DATABASE
validation_df = pd.DataFrame(list(validation_result_dict.items()), columns=['check_description', 'check_result'])

validation_df
with engine.connect() as conn:
    validation_df.to_sql(validation_resuls_table_name, engine, if_exists="replace", index=False)
# %%
