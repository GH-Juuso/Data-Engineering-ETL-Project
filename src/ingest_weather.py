import requests
import pandas as pd
import urllib.parse
from pathlib import Path

# Project root
PROJECT_ROOT = Path(__file__).resolve().parents[2]

# Data layers
DATA_DIR = PROJECT_ROOT / "data"
BRONZE_DIR = DATA_DIR / "bronze"

BRONZE_DIR.mkdir(parents=True, exist_ok=True)

# Output file
output_file = BRONZE_DIR / "weather_data.csv"

# API setup
BASE_URL = "https://archive-api.open-meteo.com/v1/archive"

params = {
    "latitude": 52.37916,
    "longitude": 4.9001612,
    "start_date": "2023-01-01",
    "end_date": "2025-12-31",
    "daily": "temperature_2m_mean,temperature_2m_max,temperature_2m_min,precipitation_sum,rain_sum,snowfall_sum,wind_speed_10m_max",
    "timezone": "Europe/Amsterdam",
}

url = BASE_URL + "?" + urllib.parse.urlencode(params)

# Request
response = requests.get(url, timeout=30)

print(response.status_code)

if response.status_code == 200:
    data = response.json()
    print(data.keys())
    weather_df = pd.DataFrame(data["daily"])
    weather_df.to_csv(output_file, index=False)
    print(f"Saved to: {output_file}")

else:
    print(response.text[:500])