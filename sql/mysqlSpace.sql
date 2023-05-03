SELECT
	table_schema AS "Schema",
	table_name AS "Table",
	ROUND((data_length/1048576),2) AS "Data Size (MB)",
	ROUND((index_length/1048576),2) AS "Index Size (MB)",
	ROUND(((data_length+index_length)/1048576),2) AS "Total Size (MB)",
	ROUND((data_free/1048576),2) AS "Size Free (MB)"
FROM
	information_schema.tables
ORDER BY
	(data_length+index_length) DESC;
