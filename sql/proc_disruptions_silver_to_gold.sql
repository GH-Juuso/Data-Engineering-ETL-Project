
CREATE OR ALTER PROCEDURE dbo.refresh_fact_disruption
AS
BEGIN
    SET NOCOUNT ON

    /* Create table if it does not exist */
    IF OBJECT_ID('dbo.fact_disruption', 'U') IS NULL
    BEGIN
        CREATE TABLE dbo.fact_disruption (
            disruption_id INT PRIMARY KEY,
            source_id INT,
            affected_route NVARCHAR(500),
            affected_train_line_qty INT,
            cause NVARCHAR(50),
            cause_group NVARCHAR(50),
            d_date DATE,
            d_time TIME
        );
    END;

    /* Store previous row count */
    DECLARE @old_rows INT;

    SELECT @old_rows = COUNT(*)
    FROM dbo.fact_disruption;

    /* Delete old records */
    DELETE FROM dbo.fact_disruption;

    /* Insert refreshed records */
    INSERT INTO dbo.fact_disruption (
        disruption_id,
        source_id,
        affected_route,
        affected_train_line_qty,
        cause,
        cause_group,
        d_date,
        d_time
    )
    SELECT
        ROW_NUMBER() OVER (ORDER BY start_time, source_id) AS disruption_id,
        COALESCE(source_id, 9999999) AS source_id,
        COALESCE(lines_names, 'missing') AS affected_route,
        COALESCE(affected_lines, 0) AS affected_train_line_qty,
        COALESCE(cause_en, 'undefined') AS cause,
        COALESCE(cause_group, 'undefined') AS cause_group,
        CAST(start_time AS DATE) AS d_date,
        CAST(start_time AS TIME) AS d_time
    FROM dbo.silver_disruption
    WHERE
        lines_names LIKE '%Amsterdam Centraal%'
        AND start_time >= '2023-01-01'
        AND cause_group = 'weather';
END;
