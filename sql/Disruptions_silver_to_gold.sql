

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
		ROW_NUMBER() OVER (ORDER BY (SELECT 1)) AS disruption_id,
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


/* Check the number of affected rows*/

WITH validation_view AS(
	SELECT
		@old_rows AS previous_row_count,
		count(*) AS new_row_count,
		(count(*) - @old_rows) AS added_rows
	FROM fact_disruption
	)

SELECT *
FROM validation_view;