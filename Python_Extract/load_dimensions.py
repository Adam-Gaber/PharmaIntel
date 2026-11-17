import os
import pandas as pd
import pyodbc
from dotenv import load_dotenv

# بيقرا ملف .env ويحط قيمه كمتغيرات بيئة
load_dotenv()

# ===== 1. الاتصال بـ SQL Server =====
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


# ===== 2. تجهيز القيم الفريدة =====
drugs = pd.read_csv("data/clean/drugs.csv")
reactions = pd.read_csv("data/clean/reactions.csv")
events = pd.read_csv("data/clean/events.csv")

dim_drug = (drugs[["drug_name", "standard_drug_name"]]
            .dropna().drop_duplicates())
dim_reaction = (reactions[["reaction"]]
                .dropna().drop_duplicates())
dim_country = (events[["reporter_country"]]
               .dropna().drop_duplicates())

# ===== 3. التحميل مع حماية التكرار =====
before = {t: count(t) for t in ["dim_drug", "dim_reaction", "dim_country"]}

for _, r in dim_drug.iterrows():
    cur.execute("""
        INSERT INTO dbo.dim_drug (drug_name, standard_drug_name)
        SELECT ?, ?
        WHERE NOT EXISTS (SELECT 1 FROM dbo.dim_drug
                          WHERE drug_name = ? AND standard_drug_name = ?)
    """, r.drug_name, r.standard_drug_name, r.drug_name, r.standard_drug_name)

for _, r in dim_reaction.iterrows():
    cur.execute("""
        INSERT INTO dbo.dim_reaction (reaction_name)
        SELECT ?
        WHERE NOT EXISTS (SELECT 1 FROM dbo.dim_reaction WHERE reaction_name = ?)
    """, r.reaction, r.reaction)

for _, r in dim_country.iterrows():
    cur.execute("""
        INSERT INTO dbo.dim_country (country_name)
        SELECT ?
        WHERE NOT EXISTS (SELECT 1 FROM dbo.dim_country WHERE country_name = ?)
    """, r.reporter_country, r.reporter_country)

conn.commit()

# ===== 4. النتيجة =====
for t in before:
    print(f"{t}: {before[t]} -> {count(t)}")

conn.close()