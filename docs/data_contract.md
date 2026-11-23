# Data Contract: Python to Talend

This page tells you three things:

1. What files you will receive.
2. What you must do with them.
3. How to check that your work is correct.

## The idea in 3 lines

- You receive **3 clean CSV files** (drug adverse event reports from the FDA).
- SQL Server already has **the tables** (empty or almost empty).
- Your job: **move the data from the CSVs into the tables using Talend**, following the order and rules below.

## 1) The files you receive

They are placed in the folder `data/clean/`. This folder is NOT on GitHub. You get it directly from Adam.

### events.csv (one row per report)

| Column | Example | Notes |
|---|---|---|
| safetyreportid | 10003300 | Report number, text, never repeated |
| receivedate | 2014-03-06 | Format YYYY-MM-DD |
| reporter_country | US | Country name |
| patient_sex | Female | Male, Female, or Unknown |
| serious_flag | 1 | 1 = serious, 0 = not serious. Can be EMPTY |
| death_flag | 0 | Always 1 or 0 |
| patient_age_years | 77.0 | Can be EMPTY |
| age_group | 65+ | 0-17, 18-34, 35-49, 50-64, 65+, or Unknown |

### drugs.csv (one row per drug inside a report)

| Column | Example | Notes |
|---|---|---|
| safetyreportid | 10003304 | |
| drug_name | OXYCONTIN | |
| generic_name | OXYCODONE HYDROCHLORIDE | Can be empty. Do NOT use it |
| characterization | Suspect | |
| indication | UNKNOWN | |
| standard_drug_name | OXYCODONE HYDROCHLORIDE | |
| is_suspect | 1 | 1 or 0 |

### reactions.csv (one row per reaction inside a report)

| Column | Example |
|---|---|
| safetyreportid | 10003300 |
| reaction | VOMITING |
| outcome | Unknown |

## 2) Where each file goes

| File | Target table | How |
|---|---|---|
| drugs.csv | `dim_drug` | UNIQUE pairs of (drug_name, standard_drug_name) |
| reactions.csv | `dim_reaction` | UNIQUE values of reaction |
| events.csv | `dim_country` | UNIQUE values of reporter_country |
| events.csv | `fact_adverse_event` | One row per report (with lookups, see section 4) |
| drugs.csv | `fact_event_drug` | One row per CSV row (with lookup) |
| reactions.csv | `fact_event_reaction` | One row per CSV row (with lookup) |

You do NOT load these from Talend (they are filled by SQL scripts): `dim_patient` (18 rows) and `dim_date` (all dates from 2000 to 2026).

## 3) Loading order (very important)

The tables point to each other (foreign keys). If you change the order you will get an error.

1. Run the SQL scripts in the `sql/` folder in order (01 to 05). This builds the tables and fills `dim_patient` and `dim_date`.
2. Load `dim_drug`, `dim_reaction`, `dim_country` (order between them does not matter).
3. Load `fact_adverse_event`.
4. Load `fact_event_drug` and `fact_event_reaction` (only after step 3).

## 4) Lookups: turning text into a number

The fact tables store numbers, not names. So before inserting a row, you must find the number in the dimension table.

### fact_adverse_event (from events.csv)

| Table column | How to get it |
|---|---|
| safetyreportid | As is |
| date_id | Convert receivedate to a number: 2014-03-06 becomes 20140306 |
| country_id | Look up reporter_country in `dim_country.country_name`, return `country_id` |
| patient_id | Look up (patient_sex + age_group) in `dim_patient.(sex, age_group)`, return `patient_id` |
| serious_flag | As is (if empty, keep NULL) |
| death_flag | As is |
| patient_age_years | As is (if empty, keep NULL) |

### fact_event_drug (from drugs.csv)

| Table column | How to get it |
|---|---|
| safetyreportid | As is |
| drug_id | Look up (drug_name + standard_drug_name) in `dim_drug`, return `drug_id` |
| characterization | As is |
| is_suspect | As is |
| indication | As is |

`event_drug_id` is automatic. Do not send it.

### fact_event_reaction (from reactions.csv)

| Table column | How to get it |
|---|---|
| safetyreportid | As is |
| reaction_id | Look up reaction in `dim_reaction.reaction_name`, return `reaction_id` |
| outcome | As is |

`event_reaction_id` is automatic. Do not send it.

## 5) Rules you must follow

1. **No duplicates.** The job must be safe to run twice in a row. Row counts must NOT grow on the second run.
2. **Empty values** in `serious_flag` and `patient_age_years` must become NULL (not 0, not an empty text).
3. **If a lookup finds nothing** (unknown country or group), do not insert the row silently. Send it to a reject file and tell Adam.
4. **Spelling is exact:** `Male`, not `male`. `18-34`, not `18 - 34`.
5. **Do not edit the CSVs or the column names.** If something looks wrong, tell Adam.

## 6) How to check your work (reference numbers)

After running the job on the SAMPLE (5 reports), run this in DBeaver:

```sql
USE FDA_DW;
SELECT 'dim_patient' AS tbl, COUNT(*) AS cnt FROM dbo.dim_patient
UNION ALL SELECT 'dim_date', COUNT(*) FROM dbo.dim_date
UNION ALL SELECT 'dim_country', COUNT(*) FROM dbo.dim_country
UNION ALL SELECT 'dim_drug', COUNT(*) FROM dbo.dim_drug
UNION ALL SELECT 'dim_reaction', COUNT(*) FROM dbo.dim_reaction
UNION ALL SELECT 'fact_adverse_event', COUNT(*) FROM dbo.fact_adverse_event
UNION ALL SELECT 'fact_event_drug', COUNT(*) FROM dbo.fact_event_drug
UNION ALL SELECT 'fact_event_reaction', COUNT(*) FROM dbo.fact_event_reaction;
```

The result must be exactly:

| Table | Count |
|---|---|
| dim_patient | 18 |
| dim_date | 9862 |
| dim_country | 2 |
| dim_drug | 13 |
| dim_reaction | 10 |
| fact_adverse_event | 5 |
| fact_event_drug | 13 |
| fact_event_reaction | 10 |

Run the job **twice**. The numbers must stay the same. If they change, something is wrong in the job: re-check sections 4 and 5.

## 7) What you hand back to Adam

1. The exported Talend job (`.bat`, and `.sh` if possible) in the folder `Talend_Jobs/`.
2. A screenshot of the section 6 query result (after the first run and after the second run).
3. Any problems you faced (they go into the README under "Challenges").

## 8) Connection details

| | |
|---|---|
| Server | `localhost,1433` |
| Database | `FDA_DW` |
| User | `sa` |
| Password | Adam will send it on WhatsApp (never on GitHub) |

## 9) Later: the big data

After the job works on the sample, you will receive files with the same names and the same columns, but with about 600,000 reports. The job should work by only changing the file path. If it is too slow, tell Adam.
