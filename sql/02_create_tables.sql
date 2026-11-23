USE FDA_DW;

IF OBJECT_ID('dbo.dim_country', 'U') IS NULL
CREATE TABLE dbo.dim_country(
	
	country_id INT IDENTITY(1,1) PRIMARY KEY,
	country_name VARCHAR(100) NOT NULL UNIQUE

);

IF OBJECT_ID('dbo.dim_reaction', 'U') IS NULL
CREATE TABLE dbo.dim_reaction (

    reaction_id   INT IDENTITY(1,1) PRIMARY KEY,
    reaction_name VARCHAR(300) NOT NULL UNIQUE
);


IF OBJECT_ID('dbo.dim_drug', 'U') IS NULL
CREATE TABLE dbo.dim_drug (

	drug_id INT IDENTITY(1,1) PRIMARY KEY,
	drug_name VARCHAR(400) NOT NULL,
	standard_drug_name VARCHAR(400) NOT NULL,
	
    CONSTRAINT UQ_dim_drug UNIQUE (drug_name, standard_drug_name)
);

IF OBJECT_ID('dbo.dim_patient', 'U') IS NULL
CREATE TABLE dbo.dim_patient (

    patient_id INT IDENTITY(1,1) PRIMARY KEY,
    sex        VARCHAR(10) NOT NULL,
    age_group  VARCHAR(20) NOT NULL,
    
    CONSTRAINT UQ_dim_patient UNIQUE (sex, age_group)
);

IF OBJECT_ID('dbo.dim_patient', 'U') IS NULL
CREATE TABLE dbo.dim_patient (

    patient_id INT IDENTITY(1,1) PRIMARY KEY,
    sex        VARCHAR(10) NOT NULL,
    age_group  VARCHAR(20) NOT NULL,
    CONSTRAINT UQ_dim_patient UNIQUE (sex, age_group)
    
);
