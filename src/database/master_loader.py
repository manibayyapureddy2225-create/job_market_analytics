from pathlib import Path
import json
import pandas as pd
from sqlalchemy import text

from src.database.db import get_engine


BASE_DIR = Path(__file__).resolve().parents[2]

RAW_FILE = BASE_DIR / "data" / "raw" / "jobs_collected.json"
OUTPUT_FILE = BASE_DIR / "data" / "processed" / "jobs_cleaned.csv"


COLUMNS = [
    "external_job_id",
    "job_title",
    "role_category",
    "company",
    "location",
    "country",
    "remote_type",
    "job_type",
    "experience_required",
    "salary_min",
    "salary_max",
    "salary_avg",
    "salary_period",
    "salary_currency",
    "skills",
    "job_description",
    "source",
    "job_url",
    "posted_date",
    "scraped_date",
]


def load_raw_jobs():
    if not RAW_FILE.exists():
        raise FileNotFoundError(
            f"Raw dataset not found: {RAW_FILE}"
        )

    with open(RAW_FILE, "r", encoding="utf-8") as file:
        data = json.load(file)

    if isinstance(data, dict):
        data = data.get("jobs", [])

    if not isinstance(data, list):
        raise ValueError("Raw dataset must contain a list of jobs.")

    return data


def normalize_text(value):
    if value is None:
        return None

    value = str(value).strip()

    return value if value else None


def calculate_salary_avg(row):
    salary_min = row.get("salary_min")
    salary_max = row.get("salary_max")

    if salary_min is not None and salary_max is not None:
        try:
            return (float(salary_min) + float(salary_max)) / 2
        except (ValueError, TypeError):
            pass

    return None


def normalize_job(job):
    normalized = {}

    for column in COLUMNS:
        normalized[column] = job.get(column)

    # Text fields
    text_fields = [
        "external_job_id",
        "job_title",
        "role_category",
        "company",
        "location",
        "country",
        "remote_type",
        "job_type",
        "experience_required",
        "salary_period",
        "salary_currency",
        "skills",
        "job_description",
        "source",
        "job_url",
        "posted_date",
        "scraped_date",
    ]

    for field in text_fields:
        normalized[field] = normalize_text(normalized[field])

    # Numeric salary fields
    for field in ["salary_min", "salary_max", "salary_avg"]:
        try:
            if normalized[field] is not None:
                normalized[field] = float(normalized[field])
        except (ValueError, TypeError):
            normalized[field] = None

    # Calculate average if missing
    if normalized["salary_avg"] is None:
        normalized["salary_avg"] = calculate_salary_avg(normalized)

    return normalized


def clean_dataframe(jobs):
    normalized_jobs = [
        normalize_job(job)
        for job in jobs
    ]

    df = pd.DataFrame(normalized_jobs, columns=COLUMNS)

    if df.empty:
        return df

    # Remove jobs without essential fields
    df = df.dropna(
        subset=["job_title", "company", "job_url"]
    )

    # Remove duplicate URLs
    df = df.drop_duplicates(
        subset=["job_url"],
        keep="first"
    )

    # Remove duplicate external IDs where available
    df["external_job_id"] = df["external_job_id"].fillna("")

    with_external_id = df[
        df["external_job_id"] != ""
    ]

    without_external_id = df[
        df["external_job_id"] == ""
    ]

    with_external_id = with_external_id.drop_duplicates(
        subset=["external_job_id"],
        keep="first"
    )

    df = pd.concat(
        [with_external_id, without_external_id],
        ignore_index=True
    )

    # Ensure salary average is correct
    missing_avg = df["salary_avg"].isna()

    df.loc[missing_avg, "salary_avg"] = (
        df.loc[missing_avg, ["salary_min", "salary_max"]]
        .mean(axis=1)
    )

    return df


def save_csv(df):
    OUTPUT_FILE.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    df.to_csv(
        OUTPUT_FILE,
        index=False,
        encoding="utf-8"
    )

    print(f"Clean dataset saved: {OUTPUT_FILE}")


def load_into_database(df):
    if df.empty:
        print("No records to load into database.")
        return

    engine = get_engine()
    inserted = 0
    updated = 0

    columns = list(COLUMNS)
    insert_columns = ", ".join(columns)
    placeholders = ", ".join(f":{column}" for column in columns)

    update_columns = [
        column for column in columns
        if column != "job_url"
    ]
    update_clause = ", ".join(
        f"{column} = :{column}"
        for column in update_columns
    )

    upsert_sql = text(f"""
        INSERT INTO jobs ({insert_columns})
        VALUES ({placeholders})
        ON CONFLICT(job_url) DO UPDATE SET
            {update_clause}
    """)

    with engine.begin() as connection:
        for _, row in df.iterrows():
            values = {
                column: (
                    None if pd.isna(row[column]) else row[column]
                )
                for column in columns
            }

            exists = connection.execute(
                text("SELECT 1 FROM jobs WHERE job_url = :url"),
                {"url": values["job_url"]}
            ).fetchone()

            connection.execute(upsert_sql, values)

            if exists:
                updated += 1
            else:
                inserted += 1

    print(f"New jobs inserted: {inserted}")
    print(f"Existing jobs updated: {updated}")


def main():
    print("=" * 60)
    print("JOB MARKET ANALYTICS - MASTER DATA LOADER")
    print("=" * 60)

    print("\nLoading raw dataset...")

    jobs = load_raw_jobs()

    print(f"Raw records: {len(jobs)}")

    print("\nNormalizing and cleaning...")

    df = clean_dataframe(jobs)

    print(f"Clean records: {len(df)}")

    if df.empty:
        print("No valid jobs available.")
        return

    print("\nSaving processed dataset...")

    save_csv(df)

    print("\nLoading into SQLite...")

    load_into_database(df)

    print("\n" + "=" * 60)
    print("MASTER LOAD COMPLETE")
    print("=" * 60)

    print("\nDataset summary:")
    print(f"Jobs       : {len(df)}")
    print(
        f"Companies  : {df['company'].nunique()}"
    )
    print(
        f"Locations  : {df['location'].nunique()}"
    )
    print(
        f"Sources    : {df['source'].nunique()}"
    )


if __name__ == "__main__":
    main()