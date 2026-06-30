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
silver_disruptions = pd.read_sql("SELECT * FROM silver_disruption", engine)

#%%

silver_disruptions_validation_dict = {}

# %%
# ----- NUMBER OF ROWS
rows_total = len(silver_disruptions)
silver_disruptions_validation_dict['rows_total'] = str(rows_total)

# %%
# ----- NUMBER OF ROWS WITH NULL VALUES IN COLUMN lines_names
lines_names_is_null = silver_disruptions['lines_names'].isna().sum()
silver_disruptions_validation_dict['lines_names_is_null'] = str(lines_names_is_null)

# %%
# ----- NUMBER OF ROWS WITH NULL VALUES IN COLUMN affected_lines
affected_lines_is_null = silver_disruptions['affected_lines'].isna().sum()
silver_disruptions_validation_dict['affected_lines_is_null'] = str(affected_lines_is_null)

# %%
# ----- NUMBER OF ROWS WITH NULL VALUES IN COLUMN lines_id
lines_id_is_null = silver_disruptions['lines_id'].isna().sum()
silver_disruptions_validation_dict['lines_id_is_null'] = str(lines_id_is_null)

# %%
# ----- NUMBER OF ROWS WITH NULL VALUES IN COLUMN affected_stations
affected_stations_is_null = silver_disruptions['affected_stations'].isna().sum()
silver_disruptions_validation_dict['affected_stations_is_null'] = str(affected_stations_is_null)

# %%
# ----- NUMBER OF ROWS WITH NULL VALUES IN COLUMN station_names
station_names_is_null = silver_disruptions['station_names'].isna().sum()
silver_disruptions_validation_dict['station_names_is_null'] = str(station_names_is_null)

# %%
# ----- NUMBER OF ROWS WITH NULL VALUES IN COLUMN station_codes
station_codes_is_null = silver_disruptions['station_codes'].isna().sum()
silver_disruptions_validation_dict['station_codes_is_null'] = str(station_codes_is_null)

# %%
# ----- NUMBER OF ROWS WITH NULL VALUES IN COLUMN cause_en
cause_en_is_null = silver_disruptions['cause_en'].isna().sum()
silver_disruptions_validation_dict['cause_en_is_null'] = str(cause_en_is_null)

# %%
# ----- NUMBER OF ROWS WITH NULL VALUES IN COLUMN statistical_cause_en
statistical_cause_en_is_null = silver_disruptions['statistical_cause_en'].isna().sum()
silver_disruptions_validation_dict['statistical_cause_en_is_null'] = str(statistical_cause_en_is_null)

# %%
# ----- NUMBER OF ROWS WITH NULL VALUES IN COLUMN cause_group
cause_group_is_null = silver_disruptions['cause_group'].isna().sum()
silver_disruptions_validation_dict['cause_group_is_null'] = str(cause_group_is_null)

# %%
# ----- NUMBER OF ROWS WITH NULL VALUES IN COLUMN start_time
start_time_is_null = silver_disruptions['start_time'].isna().sum()
silver_disruptions_validation_dict['start_time_is_null'] = str(start_time_is_null)

# %%
# ----- NUMBER OF ROWS WITH NULL VALUES IN COLUMN end_time
end_time_is_null = silver_disruptions['end_time'].isna().sum()
silver_disruptions_validation_dict['end_time_is_null'] = str(end_time_is_null)

# %%
# ----- NUMBER OF ROWS WITH NULL VALUES IN COLUMN duration_minutes
duration_minutes_is_null = silver_disruptions['duration_minutes'].isna().sum()
silver_disruptions_validation_dict['duration_minutes_is_null'] = str(duration_minutes_is_null)


# %%
# ----- NUMBER OF ROWS WITHOUT AFFECTED LINES
rows_without_affected_lines = len(silver_disruptions[(silver_disruptions['affected_lines'].isna())])
silver_disruptions_validation_dict['rows_without_affected_lines'] = str(rows_without_affected_lines)

# %%
# ----- NUMBER OF ROWS WITHOUT STATIONS
rows_without_affected_stations = len(silver_disruptions[(silver_disruptions['affected_stations'].isna())])
silver_disruptions_validation_dict['rows_without_affected_stations'] = str(rows_without_affected_stations)

# %%
# ----- NUMBER OF ROWS WITHOUT AFFECTED LINES OR STATIONS
rows_without_affected_lines_or_stations = len(silver_disruptions[(silver_disruptions['affected_lines'].isna()) & (silver_disruptions['affected_stations'].isna())])
silver_disruptions_validation_dict['rows_without_affected_lines_or_stations'] = str(rows_without_affected_lines_or_stations)

# %%
# ----- ROWS AFFECTING ASD
rows_affecting_asd = silver_disruptions['station_codes'].str.split(',').apply(lambda x: 'ASD' in x if isinstance(x, list) else False).sum()
silver_disruptions_validation_dict['rows_affecting_asd'] = str(rows_affecting_asd)

# %%
# ----- ROWS AFFECTING ASD DUE TO WEATHER
rows_affecting_asd_due_to_weather = len(silver_disruptions[(silver_disruptions['station_codes'].str.split(',').apply(lambda x: 'ASD' in x if isinstance(x, list) else False)) & (silver_disruptions['cause_group'] == 'weather')])
silver_disruptions_validation_dict['rows_affecting_asd_due_to_weather'] = str(rows_affecting_asd_due_to_weather)

# %%
# ----- ROWS AFFECTING ASD DUE TO WEATHER 2023 AND FORWARD
# select * from silver_disruption where cause_group like 'weather' and lines_names like '%Amsterdam Centraal%' and DATEPART(year, start_time) >= 2023
rows_affecting_asd_due_to_weather_2023_and_forward = len(silver_disruptions[(silver_disruptions['lines_names'].str.contains('Amsterdam Centraal')) & (silver_disruptions['cause_group'] == 'weather') & (silver_disruptions['start_time'].dt.year >= 2023)])
silver_disruptions_validation_dict['rows_affecting_asd_due_to_weather_2023_and_forward'] = str(rows_affecting_asd_due_to_weather_2023_and_forward)

# %%
# ----- WRITING silver_disruption_validation TO DATABASE
silver_disruptions_validation_df = pd.DataFrame(list(silver_disruptions_validation_dict.items()), columns=['check_description', 'check_result'])

table_name = 'silver_disruption_validation'

with engine.connect() as conn:
    silver_disruptions_validation_df.to_sql(table_name, engine, if_exists="replace", index=False)
# %%
