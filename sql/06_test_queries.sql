USE FDA_DW;

-- 1) كل بلاغ بتفاصيله من الـ Dimensions
SELECT e.safetyreportid, d.full_date, c.country_name,
       p.sex, p.age_group, e.serious_flag, e.death_flag
FROM dbo.fact_adverse_event e
JOIN dbo.dim_date    d ON e.date_id    = d.date_id
JOIN dbo.dim_country c ON e.country_id = c.country_id
JOIN dbo.dim_patient p ON e.patient_id = p.patient_id
ORDER BY e.safetyreportid;

-- 2) أكتر الأدوية ظهورًا في بلاغات خطيرة
SELECT dr.standard_drug_name, COUNT(*) AS serious_reports
FROM dbo.fact_event_drug fd
JOIN dbo.fact_adverse_event e ON fd.safetyreportid = e.safetyreportid
JOIN dbo.dim_drug dr          ON fd.drug_id = dr.drug_id
WHERE e.serious_flag = 1//
GROUP BY dr.standard_drug_name
ORDER BY serious_reports DESC;

-- 3) الأعراض الأكتر مع كل دولة
SELECT c.country_name, r.reaction_name, COUNT(*) AS cnt
FROM dbo.fact_event_reaction fr
JOIN dbo.fact_adverse_event e ON fr.safetyreportid = e.safetyreportid
JOIN dbo.dim_country c        ON e.country_id = c.country_id
JOIN dbo.dim_reaction r       ON fr.reaction_id = r.reaction_id
GROUP BY c.country_name, r.reaction_name
ORDER BY cnt DESC;

-- 4) تفاصيل كل دوا جوه كل بلاغ
SELECT dr.drug_name, dr.standard_drug_name, fd.characterization, fd.indication
FROM dbo.fact_event_drug fd
JOIN dbo.dim_drug dr ON fd.drug_id = dr.drug_id;