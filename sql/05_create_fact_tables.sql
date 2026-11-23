USE FDA_DW;

--create fact_adverse_event
IF OBJECT_ID('dbo.fact_adverse_event', 'U') IS NULL
CREATE TABLE dbo.fact_adverse_event (
    safetyreportid    VARCHAR(50)  NOT NULL PRIMARY KEY,
    date_id          INT          NOT NULL,
    country_id        INT          NOT NULL,
    patient_id        INT          NOT NULL,
    serious_flag      TINYINT      NULL,
    death_flag        TINYINT      NOT NULL,
    patient_age_years DECIMAL(4,1) NULL,
    CONSTRAINT CK_fae_serious CHECK (serious_flag IN (0, 1)),
    CONSTRAINT CK_fae_death   CHECK (death_flag IN (0, 1)),
    CONSTRAINT FK_fae_date    FOREIGN KEY (date_id)   REFERENCES dbo.dim_date (date_id),
    CONSTRAINT FK_fae_country FOREIGN KEY (country_id) REFERENCES dbo.dim_country (country_id),
    CONSTRAINT FK_fae_patient FOREIGN KEY (patient_id) REFERENCES dbo.dim_patient (patient_id)
);

--create fact_event_drug

IF OBJECT_ID('dbo.fact_event_drug', 'U') IS NULL
CREATE TABLE dbo.fact_event_drug (
    event_drug_id    INT IDENTITY(1,1) PRIMARY KEY,
    safetyreportid   VARCHAR(50)  NOT NULL,
    drug_id          INT          NOT NULL,
    characterization VARCHAR(20)  NOT NULL,
    is_suspect       TINYINT      NOT NULL,
    indication       VARCHAR(500) NOT NULL,
    CONSTRAINT CK_fed_suspect CHECK (is_suspect IN (0, 1)),
    CONSTRAINT FK_fed_event   FOREIGN KEY (safetyreportid) REFERENCES dbo.fact_adverse_event (safetyreportid),
    CONSTRAINT FK_fed_drug    FOREIGN KEY (drug_id)        REFERENCES dbo.dim_drug (drug_id)
);

--create fact_event_reaction

IF OBJECT_ID('dbo.fact_event_reaction', 'U') IS NULL
CREATE TABLE dbo.fact_event_reaction (
    event_reaction_id INT IDENTITY(1,1) PRIMARY KEY,
    safetyreportid    VARCHAR(50) NOT NULL,
    reaction_id       INT         NOT NULL,
    outcome           VARCHAR(30) NOT NULL,
    CONSTRAINT FK_fer_event    FOREIGN KEY (safetyreportid) REFERENCES dbo.fact_adverse_event (safetyreportid),
    CONSTRAINT FK_fer_reaction FOREIGN KEY (reaction_id)    REFERENCES dbo.dim_reaction (reaction_id)
);