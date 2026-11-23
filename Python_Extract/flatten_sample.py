import json

import pandas as pd

with open("data/sample_5.json", "r", encoding="utf-8") as f:
    records = json.load(f)

print("Records loaded:", len(records))

#fill each repoart
events = []
drugs = []
reactions = []

for record in records:
    report_id = record.get("safetyreportid")
    patient = record.get("patient") or {}
    source = record.get("primarysource") or {}

    events.append({
        "safetyreportid": report_id,
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
            "safetyreportid": report_id,
            "drug_name": drug.get("medicinalproduct"),
            "generic_name": generic_names[0] if generic_names else None,
            "characterization": drug.get("drugcharacterization"),
            "indication": drug.get("drugindication"),
        })

    for reaction in patient.get("reaction") or []:
        reactions.append({
            "safetyreportid": report_id,
            "reaction": reaction.get("reactionmeddrapt"),
            "outcome": reaction.get("reactionoutcome"),
        })
drugs_df = pd.DataFrame(drugs)
reactions_df = pd.DataFrame(reactions)
print(drugs_df["safetyreportid"].value_counts())
print(reactions_df["safetyreportid"].value_counts())

#Block 1: Cleaning the events table

events_df = pd.DataFrame(events)
events_df["receivedate"] = pd.to_datetime(
    events_df["receivedate"], format="%Y%m%d", errors="coerce"
)

events_df["serious_flag"] = events_df["serious"].map({"1": 1, "2": 0})

events_df["death_flag"] = events_df["seriousnessdeath"].map({"1": 1}).fillna(0).astype(int)

events_df = events_df.drop(columns=["serious", "seriousnessdeath"])

events_df["reporter_country"] = events_df["reporter_country"].fillna("Unknown")

events_df["patient_sex"] = events_df["patient_sex"].map({"1": "Male", "2": "Female", "0": "Unknown"}).fillna("Unknown")

#Block 2: Age

age_factor = events_df["patient_age_unit"].map({
    "800": 10,
    "801": 1,
    "802": 1 / 12,
    "803": 1 / 52,
    "804": 1 / 365,
    "805": 1 / 8760,
})

events_df["patient_age_years"] = (
    pd.to_numeric(events_df["patient_age"], errors="coerce") * age_factor
).round(1)

events_df = events_df.drop(columns=["patient_age", "patient_age_unit"])

events_df["patient_age_years"] = events_df["patient_age_years"].where(
    events_df["patient_age_years"].between(0, 120)
)

age_bins = [0, 18, 35, 50, 65, 121]
age_labels = ["0-17", "18-34", "35-49", "50-64", "65+"]

events_df["age_group"] = (
    pd.cut(
        events_df["patient_age_years"],
        bins=age_bins,
        labels=age_labels,
        right=False,
    )
    .astype("object")
    .fillna("Unknown")
)

print(events_df[["patient_age_years", "age_group"]])

#Block 3: Cleaning the drugs table

drugs_df["drug_name"] = drugs_df["drug_name"].str.upper().str.strip()
drugs_df["generic_name"] = drugs_df["generic_name"].str.upper().str.strip()

drugs_df = drugs_df.dropna(subset=["drug_name"])

drugs_df["standard_drug_name"] = drugs_df["generic_name"].fillna(drugs_df["drug_name"])

drugs_df["characterization"] = drugs_df["characterization"].map({"1": "Suspect", "2": "Concomitant", "3": "Interacting"}).fillna("Unknown")

drugs_df["is_suspect"] = (drugs_df["characterization"] == "Suspect").astype(int)

drugs_df["indication"] = (
    drugs_df["indication"]
    .str.upper()
    .str.strip()
    .replace("PRODUCT USED FOR UNKNOWN INDICATION", "UNKNOWN")
    .fillna("UNKNOWN")
)
drugs_df = drugs_df.drop_duplicates(subset=["safetyreportid", "drug_name"])

#Block 4: Cleaning the reactions table

reactions_df["reaction"] = reactions_df["reaction"].str.upper().str.strip()
reactions_df = reactions_df.dropna(subset=["reaction"])
print(reactions_df["outcome"].value_counts(dropna=False))

reactions_df["outcome"] = (
    reactions_df["outcome"]
    .map({
        "1": "Recovered",
        "2": "Recovering",
        "3": "Not recovered",
        "4": "Recovered with sequelae",
        "5": "Fatal",
        "6": "Unknown",
    })
    .fillna("Unknown")
)

reactions_df = reactions_df.drop_duplicates(subset=["safetyreportid", "reaction"])

#Block 5: we save 3 CSV files

from pathlib import Path

Path("data/clean").mkdir(parents=True, exist_ok=True)

events_df.to_csv("data/clean/events.csv", index=False, encoding="utf-8", date_format="%Y-%m-%d")
drugs_df.to_csv("data/clean/drugs.csv", index=False, encoding="utf-8")
reactions_df.to_csv("data/clean/reactions.csv", index=False, encoding="utf-8")

print(events_df)
print(drugs_df)
print(reactions_df)
