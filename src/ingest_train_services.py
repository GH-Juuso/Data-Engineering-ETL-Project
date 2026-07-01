"""
Bronze ingestion: download Rijden de Treinen monthly service archives.
Source: https://www.rijdendetreinen.nl/en/open-data/train-archive (CC BY 4.0)
"""

#%%
import urllib.request
from pathlib import Path
from datetime import datetime, timezone

# 1. Months to download
# Generate all months from 2023-01 through 2025-12
MONTHS = [f"{year}-{month:02d}" for year in range(2023, 2026) for month in range(1, 13)]

# 2. Save the data in bronze
BRONZE_DIR = Path(__file__).resolve().parent.parent / "data" / "bronze" / "train_services"

BASE_URL = "https://opendata.rijdendetreinen.nl/public/services/services-{month}.csv.gz"

# %%
def download_month(month: str, verbose: bool = False) -> dict:
    """Download one month's gzipped CSV and return metadata for the run log."""
    url = BASE_URL.format(month=month)
    out_path = BRONZE_DIR / f"services-{month}.csv.gz"

    if out_path.exists():
        if verbose: print(f"[skip] {out_path} already exists")
    else:
        if verbose: print(f"[download] {url}")
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req) as response, open(out_path, "wb") as f:
            f.write(response.read())
        if verbose: print(f"[done] saved to {out_path}")

    return {
        "source_name": "rijden_de_treinen",
        "file_name": out_path.name,
        "source_url": url,
        "load_timestamp": datetime.now(timezone.utc).isoformat(),
        "size_bytes": out_path.stat().st_size,
    }

# %%
def main(verbose: bool = False):
    BRONZE_DIR.mkdir(parents=True, exist_ok=True)

    run_log = [download_month(m, verbose) for m in MONTHS]

    # Write a simple run-metadata file alongside the data (good Bronze practice)
    log_path = BRONZE_DIR / "_load_log.csv"
    import csv
    with open(log_path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=run_log[0].keys())
        writer.writeheader()
        writer.writerows(run_log)

    if verbose: print(f"\nRun log written to {log_path}")

# %%
if __name__ == "__main__":
    main()
