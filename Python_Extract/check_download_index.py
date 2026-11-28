import requests
from collections import defaultdict

URL = "https://api.fda.gov/download.json"

data = requests.get(URL, timeout=60).json()
parts = data["results"]["drug"]["event"]["partitions"]

print("Number of parts:", len(parts))
print("Total Records:", data["results"]["drug"]["event"]["total_records"])

per_year = defaultdict(lambda: [0, 0.0])  # [records, size_mb]
for p in parts:
    year = p["display_name"].split()[0]
    per_year[year][0] += int(p["records"])
    per_year[year][1] += float(p["size_mb"])

print("\nYear | Number of Reports | Size in MB (zip)")
for year in sorted(per_year):
    rec, mb = per_year[year]
    print(f"{year} | {rec:>10,} | {mb:>8,.0f}")