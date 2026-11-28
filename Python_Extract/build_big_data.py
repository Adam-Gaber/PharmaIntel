import io
import json
import sys
import time
import zipfile
from pathlib import Path

import pandas as pd
import requests

YEAR = "2013"
OUT_DIR = Path("data/big")
INDEX_URL = "https://api.fda.gov/download.json"

EVENT_COLS = ["safetyreportid", "receivedate", "reporter_country", "patient_sex",
              "serious_flag", "death_flag", "patient_age_years", "age_group"]
DRUG_COLS = ["safetyreportid", "drug_name", "generic_name", "characterization",
             "indication", "standard_drug_name", "is_suspect"]
REACTION_COLS = ["safetyreportid", "reaction", "outcome"]


def download(url, tries=3):
    for attempt in range(1, tries + 1):
        try:
            r = requests.get(url, timeout=600)
            r.raise_for_status()
            return r.content
        except Exception as e:
            print("  download failed (try %d): %s" % (attempt, e))
            time.sleep(5)
    raise SystemExit("Could not download: " + url)


def clean_records(records):
    events, drugs, reactions = [], [], []
    for record in records:
        rid = record.get("safetyreportid")
        patient = record.get("patient") or {}
        source = record.get("primarysource") or {}
        events.append({
            "safetyreportid": rid,
            "receivedate": record.get("receivedate"),
            "serious": record.get("serious"),
            "seriousnessdeath": record.get("seriousnessdeath"),
            "reporter_country": source.get("reportercountry"),
            "patient_sex": patient.get("patientsex"),
            "patient_age": patient.get("patientonsetage"),
            "patient_age_unit": patient.get("patientonsetageunit"),
        })
        for drug in patient.get("drug") or []:
            openfda = drug.get("openfda") or {}
            generic_names = openfda.get("generic_name") or []
            drugs.append({
                "safetyreportid": rid,
                "drug_name": drug.get("medicinalproduct"),
                "generic_name": generic_names[0] if generic_names else None,
                "characterization": drug.get("drugcharacterization"),
                "indication": drug.get("drugindication"),
            })
        for reaction in patient.get("reaction") or []:
            reactions.append({
                "safetyreportid": rid,
                "reaction": reaction.get("reactionmeddrapt"),
                "outcome": reaction.get("reactionoutcome"),
            })

    # ---- events ----
    ev = pd.DataFrame(events)
    ev["receivedate"] = pd.to_datetime(ev["receivedate"], format="%Y%m%d", errors="coerce").dt.strftime("%Y-%m-%d")
    ev["serious_flag"] = ev["serious"].map({"1": 1, "2": 0})
    ev["death_flag"] = ev["seriousnessdeath"].map({"1": 1}).fillna(0).astype(int)
    ev["reporter_country"] = ev["reporter_country"].fillna("Unknown").replace("COUNTRY NOT SPECIFIED", "Unknown")
    ev["patient_sex"] = ev["patient_sex"].map({"1": "Male", "2": "Female", "0": "Unknown"}).fillna("Unknown")

    age_factor = ev["patient_age_unit"].map({
        "800": 10, "801": 1, "802": 1 / 12, "803": 1 / 52, "804": 1 / 365, "805": 1 / 8760,
    })
    ev["patient_age_years"] = (pd.to_numeric(ev["patient_age"], errors="coerce") * age_factor).round(1)
    ev["patient_age_years"] = ev["patient_age_years"].where(ev["patient_age_years"].between(0, 120))
    ev["age_group"] = (
        pd.cut(ev["patient_age_years"], bins=[0, 18, 35, 50, 65, 121],
               labels=["0-17", "18-34", "35-49", "50-64", "65+"], right=False)
        .astype("object").fillna("Unknown")
    )
    ev = ev[EVENT_COLS]

    # ---- drugs ----
    dr = pd.DataFrame(drugs, columns=["safetyreportid", "drug_name", "generic_name", "characterization", "indication"])
    dr["drug_name"] = dr["drug_name"].str.upper().str.strip()
    dr["generic_name"] = dr["generic_name"].str.upper().str.strip()
    dr = dr.dropna(subset=["drug_name"])
    dr["standard_drug_name"] = dr["generic_name"].fillna(dr["drug_name"])
    dr["characterization"] = dr["characterization"].map(
        {"1": "Suspect", "2": "Concomitant", "3": "Interacting"}).fillna("Unknown")
    dr["is_suspect"] = (dr["characterization"] == "Suspect").astype(int)
    dr["indication"] = (dr["indication"].str.upper().str.strip()
                        .replace("PRODUCT USED FOR UNKNOWN INDICATION", "UNKNOWN").fillna("UNKNOWN"))
    dr["drug_name"] = dr["drug_name"].str[:400]
    dr["standard_drug_name"] = dr["standard_drug_name"].str[:400]
    dr["indication"] = dr["indication"].str[:500]
    dr = dr.drop_duplicates(subset=["safetyreportid", "drug_name"])
    dr = dr[DRUG_COLS]

    # ---- reactions ----
    rx = pd.DataFrame(reactions, columns=REACTION_COLS)
    rx["reaction"] = rx["reaction"].str.upper().str.strip()
    rx = rx.dropna(subset=["reaction"])
    rx["reaction"] = rx["reaction"].str[:300]
    rx["outcome"] = rx["outcome"].map({
        "1": "Recovered", "2": "Recovering", "3": "Not recovered",
        "4": "Recovered with sequelae", "5": "Fatal", "6": "Unknown",
    }).fillna("Unknown")
    rx = rx.drop_duplicates(subset=["safetyreportid", "reaction"])

    return ev, dr, rx


def main():
    limit = int(sys.argv[1]) if len(sys.argv) > 1 else None

    index = requests.get(INDEX_URL, timeout=60).json()
    parts = index["results"]["drug"]["event"]["partitions"]
    parts = [p for p in parts if p["display_name"].startswith(YEAR)]
    if limit:
        parts = parts[:limit]

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    for name in ("events.csv", "drugs.csv", "reactions.csv"):
        f = OUT_DIR / name
        if f.exists():
            f.unlink()

    seen = set()
    totals = [0, 0, 0]
    first = True

    for i, p in enumerate(parts, 1):
        print("[%d/%d] %s | %s MB | %s reports" % (i, len(parts), p["display_name"], p["size_mb"], p["records"]))
        raw = download(p["file"])
        with zipfile.ZipFile(io.BytesIO(raw)) as z:
            records = json.loads(z.read(z.namelist()[0]))["results"]

        fresh = []
        for rec in records:
            rid = rec.get("safetyreportid")
            if rid in seen:
                continue
            seen.add(rid)
            fresh.append(rec)

        ev, dr, rx = clean_records(fresh)
        ev.to_csv(OUT_DIR / "events.csv", mode="a", header=first, index=False, encoding="utf-8")
        dr.to_csv(OUT_DIR / "drugs.csv", mode="a", header=first, index=False, encoding="utf-8")
        rx.to_csv(OUT_DIR / "reactions.csv", mode="a", header=first, index=False, encoding="utf-8")
        first = False

        totals[0] += len(ev)
        totals[1] += len(dr)
        totals[2] += len(rx)
        print("  added: %d events, %d drugs, %d reactions (running total events: %d)" % (len(ev), len(dr), len(rx), totals[0]))

    print("DONE. events=%d drugs=%d reactions=%d" % tuple(totals))


if __name__ == "__main__":
    main()