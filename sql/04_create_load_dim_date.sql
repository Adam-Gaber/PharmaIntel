USE FDA_DW;

-- 1. إنشاء جدول التواريخ
IF OBJECT_ID('dbo.dim_date', 'U') IS NULL
BEGIN
    CREATE TABLE dbo.dim_date (
        date_id     INT         NOT NULL PRIMARY KEY,   -- بصيغة 20000101
        full_date   DATE        NOT NULL UNIQUE,
        year        INT         NOT NULL,
        quarter     INT         NOT NULL,
        month       INT         NOT NULL,
        month_name  VARCHAR(10) NOT NULL,
        day         INT         NOT NULL,
        day_name    VARCHAR(10) NOT NULL
    );
END;

-- 2. إدخال البيانات بملء التواريخ يوم بيوم
DECLARE @d DATE = '2000-01-01';
DECLARE @end DATE = '2026-12-31';

WHILE @d <= @end
BEGIN
    IF NOT EXISTS (SELECT 1 FROM dbo.dim_date WHERE full_date = @d)
        INSERT INTO dbo.dim_date
        VALUES (
            (YEAR(@d) * 10000) + (MONTH(@d) * 100) + DAY(@d), -- تم تعديل الأقواس لضمان دقة الحساب
            @d, 
            YEAR(@d), 
            DATEPART(QUARTER, @d), 
            MONTH(@d),
            DATENAME(MONTH, @d), 
            DAY(@d), 
            DATENAME(WEEKDAY, @d)
        );
    
    SET @d = DATEADD(DAY, 1, @d);
END;

-- 3. التحقق من العدد النهائي
SELECT COUNT(*) AS total_days FROM dbo.dim_date;