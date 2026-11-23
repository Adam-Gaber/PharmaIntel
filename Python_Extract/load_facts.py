import os
import pandas as pd
import pyodbc
from dotenv import load_dotenv

load_dotenv()

conn = pyodbc.connect(
    f"DRIVER={{{os.getenv('DB_DRIVER')}}};"
    f"SERVER={os.getenv('DB_SERVER')};"
    f"DATABASE={os.getenv('DB_NAME')};"
    f"UID={os.getenv('DB_USER')};"
    f"PWD={os.getenv('DB_PASSWORD')};"
    "TrustServerCertificate=yes;"
)
cur = conn.cursor()

def count(table):
    cur.execute(f"SELECT COUNT(*) FROM dbo.{table}")
    return cur.fetchone()[0]

# ===== 1. قراءة الـ CSVs =====
events = pd.read_csv("data/clean/events.csv")
drugs = pd.read_csv("data/clean/drugs.csv")
reactions = pd.read_csv("data/clean/reactions.csv")

# ===== 2. قواميس الـ Lookup (نص ← رقم) =====
cur.execute("SELECT country_name, country_id FROM dbo.dim_country")
country_map = {r[0]: r[1] for r in cur.fetchall()}

cur.execute("SELECT sex, age_group, patient_id FROM dbo.dim_patient")
patient_map = {(r[0], r[1]): r[2] for r in cur.fetchall()}

cur.execute("SELECT drug_name, standard_drug_name, drug_id FROM dbo.dim_drug")
drug_map = {(r[0], r[1]): r[2] for r in cur.fetchall()}

cur.execute("SELECT reaction_name, reaction_id FROM dbo.dim_reaction")
reaction_map = {r[0]: r[1] for r in cur.fetchall()}

# ===== 3. تجهيز events =====
# التاريخ -> date_id بنفس صيغة dim_date (20140306)
events["date_id"] = pd.to_datetime(events["receivedate"]).dt.strftime("%Y%m%d").astype(int)
events["country_id"] = events["reporter_country"].map(country_map)
events["patient_id"] = [
    patient_map.get((s, a)) for s, a in zip(events["patient_sex"], events["age_group"])
]

# لو أي Lookup فشل، نوقف قبل ما ندخل حاجة غلط
missing = events[events[["country_id", "patient_id"]].isna().any(axis=1)]
if not missing.empty:
    print("Lookup فشل للبلاغات دي:")
    print(missing[["safetyreportid", "reporter_country", "patient_sex", "age_group"]])
    raise SystemExit("وقفنا: في قيم مش موجودة في الـ Dimensions")

before = {t: count(t) for t in ["fact_adverse_event", "fact_event_drug", "fact_event_reaction"]}

def none_if_nan(v):
    return None if pd.isna(v) else v

# ===== 4. fact_adverse_event =====
for r in events.itertuples():
    cur.execute("""
        INSERT INTO dbo.fact_adverse_event
            (safetyreportid, date_id, country_id, patient_id,
             serious_flag, death_flag, patient_age_years)
        SELECT ?, ?, ?, ?, ?, ?, ?
        WHERE NOT EXISTS (SELECT 1 FROM dbo.fact_adverse_event WHERE safetyreportid = ?)
    """, str(r.safetyreportid), int(r.date_id), int(r.country_id), int(r.patient_id),
         none_if_nan(r.serious_flag), int(r.death_flag), none_if_nan(r.patient_age_years),
         str(r.safetyreportid))

# ===== 5. fact_event_drug =====
for r in drugs.itertuples():
    drug_id = drug_map.get((r.drug_name, r.standard_drug_name))
    if drug_id is None:
        print("دوا مش في dim_drug:", r.drug_name)
        continue
    cur.execute("""
        INSERT INTO dbo.fact_event_drug
            (safetyreportid, drug_id, characterization, is_suspect, indication)
        SELECT ?, ?, ?, ?, ?
        WHERE NOT EXISTS (SELECT 1 FROM dbo.fact_event_drug
                          WHERE safetyreportid = ? AND drug_id = ?)
    """, str(r.safetyreportid), drug_id, r.characterization, int(r.is_suspect), r.indication,
         str(r.safetyreportid), drug_id)

# ===== 6. fact_event_reaction =====
for r in reactions.itertuples():
    reaction_id = reaction_map.get(r.reaction)
    if reaction_id is None:
        print("عرض مش في dim_reaction:", r.reaction)
        continue
    cur.execute("""
        INSERT INTO dbo.fact_event_reaction (safetyreportid, reaction_id, outcome)
        SELECT ?, ?, ?
        WHERE NOT EXISTS (SELECT 1 FROM dbo.fact_event_reaction
                          WHERE safetyreportid = ? AND reaction_id = ?)
    """, str(r.safetyreportid), reaction_id, r.outcome,
         str(r.safetyreportid), reaction_id)

conn.commit()

# ===== 7. النتيجة =====
for t in before:
    print(f"{t}: {before[t]} -> {count(t)}")

conn.close()