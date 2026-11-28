import io
import json
import zipfile
from pathlib import Path

import requests

data = requests.get("https://api.fda.gov/download.json", timeout=60).json()
parts = data["results"]["drug"]["event"]["partitions"]
parts_2013 = [p for p in parts if p["display_name"].startswith("2013")]

print("Number of 2013 parts:", len(parts_2013))
print("Total reports:", sum(int(p["records"]) for p in parts_2013))

# pick the smallest part for a quick test
p = min(parts_2013, key=lambda x: float(x["size_mb"]))
print("Downloading:", p["display_name"], "|", p["size_mb"], "MB |", p["records"], "reports")

Path("data/raw").mkdir(parents=True, exist_ok=True)
r = requests.get(p["file"], timeout=300)
with zipfile.ZipFile(io.BytesIO(r.content)) as z:
    name = z.namelist()[0]
    z.extract(name, "data/raw")
print("Saved in data/raw:", name)

with open(f"data/raw/{name}", encoding="utf-8") as f:
    d = json.load(f)
print("Keys:", list(d.keys()))
print("Reports in file:", len(d["results"]))
print("First report id:", d["results"][0]["safetyreportid"])