"""
Job Market Analytics
Day 1 - Step 4: Load cleaned data into SQLite
"""

from pathlib import Path

import pandas as pd
from sqlalchemy import text

from db import get_engine


# ---------------------------------------------------------
# PROJECT PATHS
# ---------------------------------------------------------

BASE_DIR = Path(__file__).resolve().parents[2]

PROCESSED_FILE = (
    BASE_DIR
    / "data"
    / "processed"
    / "jobs_cleaned.csv"
)


# ---------------------------------------------------------
# LOAD CSV
# ---------------------------------------------------------

def load_csv():
    """Load cleaned job data."""

    if not PROCESSED_FILE.exists():
        raise FileNotFoundError(
            f"Processed file not found: {PROCESSED_FILE}"
        )

    df = pd.read_csv(PROCESSED_FILE)

    print(f"CSV records loaded: {len(df)}")

    return df


# ---------------------------------------------------------
# PREPARE DATA
# ---------------------------------------------------------

def prepare_data(df):
    """Prepare data before inserting into SQL."""

    # Convert date columns to strings compatible with SQLite
    for column in ["posted_date", "scraped_date"]:
        if column in df.columns:
            df[column] = pd.to_datetime(
                df[column],
                errors="coerce"
            ).astype("string")

    # Ensure salary columns are numeric
    for column in [
        "salary_min",
        "salary_max",
        "salary_avg"
    ]:
        if column in df.columns:
            df[column] = pd.to_numeric(
                df[column],
                errors="coerce"
            )

    return df


# ---------------------------------------------------------
# INSERT INTO DATABASE
# ---------------------------------------------------------

def insert_data(df):
    """Insert cleaned records into SQL database."""

    engine = get_engine()

    # Remove previous records from this dataset
    # This keeps repeated test runs from creating duplicates.
    with engine.begin() as connection:
        connection.execute(
            text("DELETE FROM jobs")
        )

    # Match the database schema.
    columns = [
        "job_title",
        "company",
        "location",
        "job_type",
        "experience_required",
        "salary_min",
        "salary_max",
        "salary_avg",
        "salary_currency",
        "skills",
        "job_description",
        "source",
        "job_url",
        "posted_date",
        "scraped_date"
    ]

    data_to_insert = df[columns].copy()

    data_to_insert.to_sql(
        "jobs",
        engine,
        if_exists="append",
        index=False
    )

    print(f"Inserted {len(data_to_insert)} records into SQL.")


# ---------------------------------------------------------
# VALIDATE DATABASE
# ---------------------------------------------------------

def validate_database():
    """Run database validation checks."""

    engine = get_engine()

    with engine.connect() as connection:

        total_jobs = connection.execute(
            text("SELECT COUNT(*) FROM jobs")
        ).scalar()

        duplicate_urls = connection.execute(
            text("""
                SELECT COUNT(*)
                FROM (
                    SELECT job_url
                    FROM jobs
                    GROUP BY job_url
                    HAVING COUNT(*) > 1
                )
            """)
        ).scalar()

        missing_titles = connection.execute(
            text("""
                SELECT COUNT(*)
                FROM jobs
                WHERE job_title IS NULL
                   OR TRIM(job_title) = ''
            """)
        ).scalar()

        missing_companies = connection.execute(
            text("""
                SELECT COUNT(*)
                FROM jobs
                WHERE company IS NULL
                   OR TRIM(company) = ''
            """)
        ).scalar()

        print("\n" + "=" * 60)
        print("DATABASE VALIDATION")
        print("=" * 60)

        print(f"Total jobs in database : {total_jobs}")
        print(f"Duplicate URLs         : {duplicate_urls}")
        print(f"Missing job titles     : {missing_titles}")
        print(f"Missing companies      : {missing_companies}")

        if duplicate_urls == 0:
            print("URL validation         : PASS")

        if missing_titles == 0:
            print("Job title validation   : PASS")

        if missing_companies == 0:
            print("Company validation     : PASS")


# ---------------------------------------------------------
# SHOW SAMPLE RECORDS
# ---------------------------------------------------------

def show_sample_records():
    """Display a few records from SQL."""

    engine = get_engine()

    query = text("""
        SELECT
            job_id,
            job_title,
            company,
            location,
            salary_min,
            salary_max
        FROM jobs
        ORDER BY job_id
        LIMIT 5
    """)

    with engine.connect() as connection:

        result = connection.execute(query)

        print("\n" + "=" * 60)
        print("SAMPLE DATABASE RECORDS")
        print("=" * 60)

        for row in result:
            print(
                f"{row.job_id} | "
                f"{row.job_title} | "
                f"{row.company} | "
                f"{row.location} | "
                f"{row.salary_min} - {row.salary_max}"
            )


# ---------------------------------------------------------
# MAIN
# ---------------------------------------------------------

def main():

    print("=" * 60)
    print("JOB MARKET ANALYTICS - SQL DATA LOADER")
    print("=" * 60)

    # Load
    df = load_csv()

    # Prepare
    df = prepare_data(df)

    # Insert
    insert_data(df)

    # Validate
    validate_database()

    # Display
    show_sample_records()

    print("\n" + "=" * 60)
    print("SQL DATA LOADING COMPLETED SUCCESSFULLY")
    print("=" * 60)


if __name__ == "__main__":
    main()