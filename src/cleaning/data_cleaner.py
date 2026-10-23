"""
Job Market Analytics
Day 1 - Step 3: Data Cleaning

Cleans raw job data and creates a processed CSV dataset.
"""

from pathlib import Path
import json
import re
import pandas as pd


# ---------------------------------------------------------
# PROJECT PATHS
# ---------------------------------------------------------

BASE_DIR = Path(__file__).resolve().parents[2]

RAW_FILE = BASE_DIR / "data" / "raw" / "jobs_collected.json"
PROCESSED_DIR = BASE_DIR / "data" / "processed"

PROCESSED_FILE = PROCESSED_DIR / "jobs_cleaned.csv"


# ---------------------------------------------------------
# LOAD RAW DATA
# ---------------------------------------------------------

def load_raw_data():
    """Load raw job records from JSON."""

    with open(RAW_FILE, "r", encoding="utf-8") as file:
        jobs = json.load(file)

    print(f"Loaded {len(jobs)} raw jobs.")

    return jobs


# ---------------------------------------------------------
# CREATE DATAFRAME
# ---------------------------------------------------------

def create_dataframe(jobs):
    """Convert JSON records into a Pandas DataFrame."""

    df = pd.DataFrame(jobs)

    print(f"Initial rows: {len(df)}")
    print(f"Initial columns: {len(df.columns)}")

    return df


# ---------------------------------------------------------
# CLEAN TEXT
# ---------------------------------------------------------

def clean_text(value):
    """Remove unnecessary whitespace from text."""

    if pd.isna(value):
        return None

    value = str(value)

    value = re.sub(r"\s+", " ", value)

    return value.strip()


# ---------------------------------------------------------
# CLEAN JOB TITLES
# ---------------------------------------------------------

def clean_job_titles(df):
    """Standardize job title formatting."""

    df["job_title"] = (
        df["job_title"]
        .apply(clean_text)
        .str.title()
    )

    return df


# ---------------------------------------------------------
# CLEAN COMPANY
# ---------------------------------------------------------

def clean_companies(df):
    """Clean company names."""

    df["company"] = df["company"].apply(clean_text)

    return df


# ---------------------------------------------------------
# CLEAN LOCATIONS
# ---------------------------------------------------------

def clean_locations(df):
    """Standardize location text."""

    df["location"] = (
        df["location"]
        .apply(clean_text)
        .str.title()
    )

    return df


# ---------------------------------------------------------
# CLEAN JOB TYPE
# ---------------------------------------------------------

def clean_job_type(df):
    """Standardize job type."""

    df["job_type"] = (
        df["job_type"]
        .apply(clean_text)
        .str.title()
    )

    return df


# ---------------------------------------------------------
# CLEAN EXPERIENCE
# ---------------------------------------------------------

def clean_experience(df):
    """Clean experience requirement."""

    df["experience_required"] = (
        df["experience_required"]
        .apply(clean_text)
    )

    return df


# ---------------------------------------------------------
# NORMALIZE SKILLS
# ---------------------------------------------------------

def normalize_skills(skills):
    """
    Convert skill lists into a standardized comma-separated string.
    """

    if not isinstance(skills, list):
        return ""

    cleaned_skills = []

    for skill in skills:

        skill = clean_text(skill)

        if skill:
            cleaned_skills.append(skill)

    # Remove duplicates while preserving order
    cleaned_skills = list(dict.fromkeys(cleaned_skills))

    return ", ".join(cleaned_skills)


def clean_skills(df):
    """Normalize skills column."""

    df["skills"] = df["skills"].apply(normalize_skills)

    return df


# ---------------------------------------------------------
# CLEAN DESCRIPTION
# ---------------------------------------------------------

def clean_descriptions(df):
    """Clean job descriptions."""

    df["job_description"] = (
        df["job_description"]
        .apply(clean_text)
    )

    return df


# ---------------------------------------------------------
# SALARY NORMALIZATION
# ---------------------------------------------------------


def normalize_salary(df):
    """
    Convert salary values to numeric and reject invalid ranges.
    Do not infer missing salaries or pay periods.
    """
    df = df.copy()

    df["salary_min"] = pd.to_numeric(
        df["salary_min"], errors="coerce"
    )

    df["salary_max"] = pd.to_numeric(
        df["salary_max"], errors="coerce"
    )

    # Reject negative values and reversed ranges.
    invalid_range = (
        (df["salary_min"] < 0)
        | (df["salary_max"] < 0)
        | (
            df["salary_min"].notna()
            & df["salary_max"].notna()
            & (df["salary_min"] > df["salary_max"])
        )
    )

    df.loc[invalid_range, ["salary_min", "salary_max"]] = float("nan")

    # Calculate averages only when both endpoints are available.
    valid_range = (
        df["salary_min"].notna()
        & df["salary_max"].notna()
    )

    df["salary_avg"] = float("nan")

    df.loc[valid_range, "salary_avg"] = (
        df.loc[valid_range, "salary_min"]
        + df.loc[valid_range, "salary_max"]
    ) / 2

    return df



# ---------------------------------------------------------
# DATE VALIDATION
# ---------------------------------------------------------

def clean_dates(df):
    """Convert date columns into standard datetime format."""

    df["posted_date"] = pd.to_datetime(
        df["posted_date"],
        errors="coerce"
    )

    df["scraped_date"] = pd.to_datetime(
        df["scraped_date"],
        errors="coerce",
        utc=True
    )

    return df


# ---------------------------------------------------------
# REMOVE DUPLICATES
# ---------------------------------------------------------

def remove_duplicates(df):
    """Remove duplicate job listings."""

    before = len(df)

    # Prefer job URL as unique identifier
    if "job_url" in df.columns:
        df = df.drop_duplicates(
            subset=["job_url"],
            keep="first"
        )

    after = len(df)

    print(f"Duplicates removed: {before - after}")

    return df


# ---------------------------------------------------------
# MISSING VALUE HANDLING
# ---------------------------------------------------------

def handle_missing_values(df):
    """Handle missing values in important columns."""

    text_columns = [
        "company",
        "location",
        "job_type",
        "experience_required",
        "skills",
        "job_description"
    ]

    for column in text_columns:

        if column in df.columns:
            df[column] = df[column].fillna("Unknown")

    return df


# ---------------------------------------------------------
# DATA QUALITY REPORT
# ---------------------------------------------------------

def generate_quality_report(df):
    """Generate basic data quality statistics."""

    print("\n" + "=" * 60)
    print("DATA QUALITY REPORT")
    print("=" * 60)

    print(f"Total records       : {len(df)}")
    print(f"Total columns       : {len(df.columns)}")

    print("\nMissing values:")

    missing = df.isnull().sum()

    for column, count in missing.items():

        if count > 0:
            print(f"  {column}: {count}")

    print("\nDuplicate records   :", df.duplicated().sum())

    print("\nColumns:")

    for column in df.columns:
        print(f"  - {column}")


# ---------------------------------------------------------
# SAVE PROCESSED DATA
# ---------------------------------------------------------

def save_processed_data(df):
    """Save cleaned dataset as CSV."""

    PROCESSED_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    df.to_csv(
        PROCESSED_FILE,
        index=False,
        encoding="utf-8"
    )

    print("\nProcessed dataset saved:")
    print(PROCESSED_FILE)


# ---------------------------------------------------------
# MAIN CLEANING PIPELINE
# ---------------------------------------------------------

def main():

    print("=" * 60)
    print("JOB MARKET ANALYTICS - DATA CLEANING")
    print("=" * 60)

    # Load
    jobs = load_raw_data()

    # DataFrame
    df = create_dataframe(jobs)

    # Cleaning pipeline
    df = clean_job_titles(df)
    df = clean_companies(df)
    df = clean_locations(df)
    df = clean_job_type(df)
    df = clean_experience(df)
    df = clean_skills(df)
    df = clean_descriptions(df)

    # Salary
    df = normalize_salary(df)

    # Dates
    df = clean_dates(df)

    # Missing values
    df = handle_missing_values(df)

    # Duplicate removal
    df = remove_duplicates(df)

    # Quality report
    generate_quality_report(df)

    # Save
    save_processed_data(df)

    print("\n" + "=" * 60)
    print("DATA CLEANING COMPLETED SUCCESSFULLY")
    print("=" * 60)


if __name__ == "__main__":
    main()