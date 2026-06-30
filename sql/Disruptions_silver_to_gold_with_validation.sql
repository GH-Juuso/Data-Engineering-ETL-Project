

/* Check if the table already exists and create it if it doesnt. */

IF OBJECT_ID('dbo.fact_disruption', 'U') IS NULL
	CREATE TABLE fact_disruption(
		disruption_id INT PRIMARY KEY, 
		source_id INT, 
		affected_route NVARCHAR(500), 
		affected_train_line_qty INT, 
		cause NVARCHAR(50), 
		cause_group NVARCHAR(50),
		d_date DATE,
		d_time TIME
	);


/* Store the previous row count for later validation. */

DECLARE @old_rows AS INT = (
    SELECT COUNT(*)
    FROM fact_disruption
);


/* Delete the previous records to avoid duplicates */

DELETE fact_disruption


/* Get the latest records from silver table. Add a rownumber as the primary key and identifier for disruption rows. 
Check the columns for nulls and replace them with default values. Filter the data so that we only get the weather related disruptions 
that departure from, arrive to or pass by Amsterdam Centraal and have happened after 2023 so that we can match it with train services */

INSERT INTO fact_disruption(disruption_id, source_id, affected_route, affected_train_line_qty, cause, cause_group, d_date, d_time)
	SELECT
		ROW_NUMBER() OVER (ORDER BY start_time, source_id) AS disruption_id,
		COALESCE(source_id, 9999999) AS source_id,
		COALESCE(lines_names, 'missing') AS affected_route,
		COALESCE(affected_lines, 0) AS affected_train_line_qty,
		COALESCE(cause_en, 'undefined') AS cause,
		COALESCE(cause_group,'undefined') AS cause_group,
		CAST(start_time AS date) AS d_date,
		CAST(start_time AS time) AS d_time
	FROM silver_disruption
	WHERE 
		lines_names LIKE '%Amsterdam Centraal%' AND
		YEAR(start_time) >= 2023 AND
		cause_group = 'weather';


/* Show null values */
-- Sum per null value in a cloumn

SELECT
    SUM(CASE WHEN source_id = 9999999 THEN 1 ELSE 0 END) AS default_source_id_count,
    SUM(CASE WHEN affected_route = 'missing' THEN 1 ELSE 0 END) AS default_route_count,
    SUM(CASE WHEN affected_train_line_qty <= 0 THEN 1 ELSE 0 END) AS default_line_qty_count,
    SUM(CASE WHEN cause = 'undefined' THEN 1 ELSE 0 END) AS default_cause_count,
    SUM(CASE WHEN cause_group = 'undefined' THEN 1 ELSE 0 END) AS default_cause_group_count,
    SUM(CASE WHEN d_date IS NULL THEN 1 ELSE 0 END) AS null_d_date,
    SUM(CASE WHEN d_time IS NULL THEN 1 ELSE 0 END) AS null_d_time
FROM fact_disruption;

-- Gather the rows with nulls into a CTE

WITH rows_with_default_values AS (
    SELECT *
    FROM fact_disruption
    WHERE source_id = 9999999
       OR affected_route = 'missing'
       OR affected_train_line_qty = 0
       OR cause = 'undefined'
       OR cause_group = 'undefined'
)
SELECT *
FROM rows_with_default_values;


/* Validate refresh result */

WITH expected AS (
    SELECT COUNT(*) AS expected_rows
    FROM silver_disruption
    WHERE 
        lines_names LIKE '%Amsterdam Centraal%' AND
        YEAR(start_time) >= 2023 AND
        cause_group = 'weather'
),
actual AS (
    SELECT COUNT(*) AS actual_rows
    FROM fact_disruption
)
SELECT
    @old_rows AS previous_row_count,
    expected.expected_rows,
    actual.actual_rows,
    actual.actual_rows - @old_rows AS row_count_change,
    CASE 
        WHEN actual.actual_rows = expected.expected_rows THEN 'PASS'
        ELSE 'FAIL'
    END AS row_count_validation
FROM expected
CROSS JOIN actual;