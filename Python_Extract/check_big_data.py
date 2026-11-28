import pandas as pd

ev = pd.read_csv("data/big/events.csv", dtype={"safetyreportid": str}, keep_default_na=False, na_values=[""])
dr = pd.read_csv("data/big/drugs.csv", dtype={"safetyreportid": str}, keep_default_na=False, na_values=[""])
rx = pd.read_csv("data/big/reactions.csv", dtype={"safetyreportid": str}, keep_default_na=False, na_values=[""])

print("events rows:", len(ev), "| unique ids:", ev["safetyreportid"].nunique())
print("drugs rows:", len(dr), "| reactions rows:", len(rx))
print("--- expected dimension sizes ---")
print("dim_country:", ev["reporter_country"].nunique())
print("dim_drug pairs:", len(dr[["drug_name", "standard_drug_name"]].drop_duplicates()))
print("dim_reaction:", rx["reaction"].nunique())
print("--- problems (all should be 0) ---")
print("empty dates:", ev["receivedate"].isna().sum())
print("empty country:", ev["reporter_country"].isna().sum())
print("drugs without a report:", (~dr["safetyreportid"].isin(ev["safetyreportid"])).sum())
print("reactions without a report:", (~rx["safetyreportid"].isin(ev["safetyreportid"])).sum())
print("--- info ---")
print("date range:", ev["receivedate"].min(), "to", ev["receivedate"].max())
print("serious_flag empty:", ev["serious_flag"].isna().sum())
print("age empty:", ev["patient_age_years"].isna().sum())
print("deaths:", ev["death_flag"].sum())
print("max lengths:", dr["drug_name"].str.len().max(), dr["standard_drug_name"].str.len().max(),
      dr["indication"].str.len().max(), rx["reaction"].str.len().max())