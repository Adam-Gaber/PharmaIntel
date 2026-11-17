USE FDA_DW;

INSERT INTO dbo.dim_patient (sex, age_group)

SELECT s.sex, a.age_group
FROM (VALUES ('Male'), ('Female'), ('Unknown')) AS s(sex)
CROSS JOIN (VALUES ('0-17'), ('18-34'), ('35-49'), ('50-64'), ('65+'), ('Unknown')) AS a(age_group)
WHERE NOT EXISTS (
    SELECT 1
    FROM dbo.dim_patient p
    WHERE p.sex = s.sex AND p.age_group = a.age_group
);

USE FDA_DW;

SELECT TABLE_NAME, COLUMN_NAME, DATA_TYPE, CHARACTER_MAXIMUM_LENGTH, IS_NULLABLE
FROM INFORMATION_SCHEMA.COLUMNS
WHERE TABLE_NAME NOT IN ('dim_drug', 'dim_reaction', 'dim_patient')
ORDER BY TABLE_NAME, ORDINAL_POSITION;