from pathlib import Path
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup

PAGE_URL = "https://www.rijdendetreinen.nl/en/open-data/disruptions#downloads"

OUT_DIR = Path.home() / "Downloads" / "TrainDisruptions"
OUT_DIR.mkdir(exist_ok=True)  # Safe even if it already exists

print("Saving files to:", OUT_DIR)

headers = {
    "User-Agent": "csv-downloader/1.0"
}

# 1. Get page
html = requests.get(PAGE_URL, headers=headers, timeout=30)
html.raise_for_status()

# 2. Find CSV links
soup = BeautifulSoup(html.text, "html.parser")
csv_urls = sorted({
    urljoin(PAGE_URL, a["href"])
    for a in soup.find_all("a", href=True)
    if a["href"].endswith(".csv")
})

print(f"Found {len(csv_urls)} CSV files")

# 3. Download each CSV
for url in csv_urls:
    filename = url.split("/")[-1]
    output_path = OUT_DIR / filename

    print(f"Downloading {filename}...")
    with requests.get(url, headers=headers, stream=True, timeout=60) as r:
        r.raise_for_status()
        with open(output_path, "wb") as f:
            for chunk in r.iter_content(chunk_size=1024 * 1024):
                if chunk:
                    f.write(chunk)

print("Done.")


