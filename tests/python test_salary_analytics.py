
import sqlite3

db_path = "data/job_market.db"

query = """
SELECT
    COALESCE(NULLIF(TRIM(salary_currency), ''), 'unknown')
        AS salary_currency,
    COALESCE(NULLIF(LOWER(TRIM(salary_period)), ''), 'unknown')
        AS salary_period,
    COUNT(*) AS jobs_with_salary,
    ROUND(MIN(salary_avg), 2) AS minimum_recorded_value,
    ROUND(AVG(salary_avg), 2) AS average_recorded_value,
    ROUND(MAX(salary_avg), 2) AS maximum_recorded_value
FROM jobs
WHERE salary_avg IS NOT NULL
GROUP BY
    COALESCE(NULLIF(TRIM(salary_currency), ''), 'unknown'),
    COALESCE(NULLIF(LOWER(TRIM(salary_period)), ''), 'unknown')
ORDER BY jobs_with_salary DESC;
"""

try:
    with sqlite3.connect(db_path) as conn:
        cursor = conn.execute(query)

        print("SQL TEST: PASSED")
        print(" | ".join(column[0] for column in cursor.description))

        for row in cursor.fetchall():
            print(row)

except sqlite3.Error as error:
    print("SQL TEST: FAILED")
    print(error)
