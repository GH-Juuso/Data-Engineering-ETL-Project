"""
Bronze ingestion: download Rijden de Treinen monthly service archives.
Source: https://www.rijdendetreinen.nl/en/open-data/train-archive (CC BY 4.0)
"""

import csv
import urllib.request
from pathlib import Path
from datetime import datetime, timezone


# 2. Save the data in bronze
BRONZE_DIR = Path(__file__).resolve().parent.parent / "data" / "bronze" / "train_services"
BRONZE_DIR.mkdir(parents=True, exist_ok=True)

BASE_URL = "https://opendata.rijdendetreinen.nl/public/services/services-{year}.csv.gz"

YEARS = ["2023", "2024", "2025"]


def download_year(year: str, verbose:bool = False) -> dict:
    url = BASE_URL.format(year=year)
    out_path = BRONZE_DIR / f"services_{year}.csv.gz"

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


def main(verbose: bool = False):
    run_log = [download_year(m, verbose) for m in YEARS]

    # Write a simple run-metadata file alongside the data (good Bronze practice)
    log_path = BRONZE_DIR / "_load_log.csv"
    with open(log_path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=run_log[0].keys())
        writer.writeheader()
        writer.writerows(run_log)

    total_mb = sum(r["size_bytes"] for r in run_log) / 1_000_000
    if verbose: print(f"\nRun log written to {log_path}")
    if verbose: print(f"Total downloaded: {total_mb:.1f} MB")

if __name__ == "__main__":
    main()
