import json
from pathlib import Path
import requests

# request data from the API
URL = "https://api.fda.gov/drug/event.json"
params = {'limit': 5}
response = requests.get(URL, params=params, timeout=60)
print("Status code:", response.status_code)

# open response and see it
data = response.json()
print("Keys in response:", list(data.keys()))
print("Total reports available:", data["meta"]["results"]["total"])

records = data["results"]
print("Number of records we got:", len(records))

first_record = records[0]
print("Keys inside one record:", list(first_record.keys()))

Path("Data").mkdir(exist_ok=True)

with open("Data/sample_5.json", "w", encoding="utf-8") as f:
    json.dump(records, f, indent=2)

print("Saved to Data/sample_5.json")