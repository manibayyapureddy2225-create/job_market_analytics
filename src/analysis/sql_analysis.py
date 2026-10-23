"""
Job Market Analytics
Day 1 - Step 5: SQL Analytics Runner
"""

from pathlib import Path

import pandas as pd

from src.database.db import get_engine


# ---------------------------------------------------------
# PROJECT PATH
# ---------------------------------------------------------

BASE_DIR = Path(__file__).resolve().parents[2]

OUTPUT_DIR = BASE_DIR / "data" / "processed"


# ---------------------------------------------------------
# ANALYTICS QUERIES
# ---------------------------------------------------------

QUERIES = {

    "job_demand": """
        SELECT
            job_title,
            COUNT(*) AS job_count
        FROM jobs
        GROUP BY job_title
        ORDER BY job_count DESC
    """,

    "location_demand": """
        SELECT
            location,
            COUNT(*) AS job_count
        FROM jobs
        GROUP BY location
        ORDER BY job_count DESC
    """,

    "salary_by_role": """
        SELECT
            job_title,
            ROUND(AVG(salary_avg), 2) AS average_salary
        FROM jobs
        WHERE salary_avg IS NOT NULL
        GROUP BY job_title
        ORDER BY average_salary DESC
    """,

    "salary_by_location": """
        SELECT
            location,
            ROUND(AVG(salary_avg), 2) AS average_salary
        FROM jobs
        WHERE salary_avg IS NOT NULL
        GROUP BY location
        ORDER BY average_salary DESC
    """,

    "experience_demand": """
        SELECT
            experience_required,
            COUNT(*) AS job_count
        FROM jobs
        GROUP BY experience_required
        ORDER BY job_count DESC
    """,

    "company_demand": """
        SELECT
            company,
            COUNT(*) AS job_count
        FROM jobs
        GROUP BY company
        ORDER BY job_count DESC
    """
}


# ---------------------------------------------------------
# RUN ANALYTICS
# ---------------------------------------------------------

def run_analysis():

    engine = get_engine()

    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    print("=" * 60)
    print("JOB MARKET ANALYTICS")
    print("=" * 60)

    for analysis_name, query in QUERIES.items():

        print(f"\nRunning: {analysis_name}")

        df = pd.read_sql(
            query,
            engine
        )

        output_file = (
            OUTPUT_DIR
            / f"{analysis_name}.csv"
        )

        df.to_csv(
            output_file,
            index=False
        )

        print(df.to_string(index=False))
        print(f"Saved: {output_file}")


# ---------------------------------------------------------
# MAIN
# ---------------------------------------------------------

if __name__ == "__main__":
    run_analysis()