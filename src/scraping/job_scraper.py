"""
Job Market Analytics
Day 1 - Job Data Collector

Collects job listings from a public JSON/API-style source
and stores the raw records for later cleaning and analysis.
"""

from datetime import datetime, timezone
from pathlib import Path
import json


# ---------------------------------------------------------
# PROJECT PATHS
# ---------------------------------------------------------

BASE_DIR = Path(__file__).resolve().parents[2]

RAW_DATA_DIR = BASE_DIR / "data" / "raw"

RAW_DATA_FILE = RAW_DATA_DIR / "jobs_raw.json"


# ---------------------------------------------------------
# SAMPLE DATA
# ---------------------------------------------------------
# We start with controlled sample records.
# Later, this function will be replaced/extended with
# a real permitted public job-data source.

def get_sample_jobs():
    """Return sample job records for pipeline development."""

    scraped_date = datetime.now(timezone.utc).isoformat()

    jobs = [
        {
            "job_title": "Data Analyst",
            "company": "Example Analytics Pvt Ltd",
            "location": "Hyderabad, India",
            "job_type": "Full-time",
            "experience_required": "0-2 years",
            "salary_min": 400000,
            "salary_max": 700000,
            "salary_currency": "INR",
            "skills": [
                "Python",
                "SQL",
                "Power BI",
                "Excel"
            ],
            "job_description": (
                "Analyze business data, create dashboards, "
                "write SQL queries and generate reports."
            ),
            "source": "Sample",
            "job_url": "https://example.com/jobs/data-analyst-001",
            "posted_date": "2026-10-01",
            "scraped_date": scraped_date
        },
        {
            "job_title": "Junior Python Developer",
            "company": "Example Technologies",
            "location": "Bangalore, India",
            "job_type": "Full-time",
            "experience_required": "0-2 years",
            "salary_min": 500000,
            "salary_max": 900000,
            "salary_currency": "INR",
            "skills": [
                "Python",
                "FastAPI",
                "SQL",
                "Git",
                "REST API"
            ],
            "job_description": (
                "Develop backend applications using Python, "
                "REST APIs and SQL databases."
            ),
            "source": "Sample",
            "job_url": "https://example.com/jobs/python-dev-001",
            "posted_date": "2026-10-02",
            "scraped_date": scraped_date
        },
        {
            "job_title": "Business Intelligence Analyst",
            "company": "Example Consulting",
            "location": "Pune, India",
            "job_type": "Full-time",
            "experience_required": "1-3 years",
            "salary_min": 600000,
            "salary_max": 1000000,
            "salary_currency": "INR",
            "skills": [
                "Power BI",
                "SQL",
                "Excel",
                "Data Visualization",
                "Python"
            ],
            "job_description": (
                "Build business intelligence dashboards, "
                "analyze trends and communicate insights."
            ),
            "source": "Sample",
            "job_url": "https://example.com/jobs/bi-analyst-001",
            "posted_date": "2026-10-03",
            "scraped_date": scraped_date
        }
    ]

    return jobs


# ---------------------------------------------------------
# SAVE RAW DATA
# ---------------------------------------------------------

def save_raw_jobs(jobs):
    """Save collected jobs as JSON."""

    RAW_DATA_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    with open(
        RAW_DATA_FILE,
        "w",
        encoding="utf-8"
    ) as file:

        json.dump(
            jobs,
            file,
            indent=4,
            ensure_ascii=False
        )

    print(f"Saved {len(jobs)} jobs.")
    print(f"File: {RAW_DATA_FILE}")


# ---------------------------------------------------------
# MAIN PIPELINE
# ---------------------------------------------------------

def main():

    print("=" * 60)
    print("JOB MARKET ANALYTICS - DATA COLLECTION")
    print("=" * 60)

    print("\nCollecting job records...")

    jobs = get_sample_jobs()

    print(f"Collected: {len(jobs)} jobs")

    save_raw_jobs(jobs)

    print("\nData collection completed successfully.")


if __name__ == "__main__":
    main()