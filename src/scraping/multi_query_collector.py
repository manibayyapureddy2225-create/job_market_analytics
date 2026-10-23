"""
Job Market Analytics
Step 8D - Job Classification Engine

Fetches public jobs and performs local role classification
instead of trusting the source search parameter.
"""

from pathlib import Path
from datetime import datetime
import json
import re
import time

from src.scraping.source_adapters.remotive_scraper import (
    RemotiveScraper
)


BASE_DIR = Path(__file__).resolve().parents[2]

OUTPUT_DIR = BASE_DIR / "data" / "raw"

OUTPUT_FILE = OUTPUT_DIR / "jobs_collected.json"


# ============================================================
# ROLE CLASSIFICATION
# ============================================================

ROLE_CATEGORIES = {

    "Data Analyst": [
        "data analyst",
        "data analytics",
        "data analysis",
        "analytics analyst"
    ],

    "Business Analyst": [
        "business analyst",
        "business analysis"
    ],

    "Business Intelligence": [
        "business intelligence",
        "bi analyst",
        "bi developer"
    ],

    "Data Scientist": [
        "data scientist",
        "data science"
    ],

    "Machine Learning": [
        "machine learning engineer",
        "machine learning",
        "ml engineer",
        "mlops"
    ],

    "Python Developer": [
        "python developer",
        "python engineer",
        "python backend",
        "python software"
    ],

    "Software Developer": [
        "software developer",
        "software engineer",
        "full stack developer",
        "full-stack developer",
        "backend developer",
        "back-end developer",
        "frontend developer",
        "front-end developer"
    ]
}


# ============================================================
# TEXT NORMALIZATION
# ============================================================

def normalize_text(value):

    if not value:
        return ""

    value = str(value).lower()

    value = re.sub(
        r"[^a-z0-9+#.\s-]",
        " ",
        value
    )

    value = re.sub(
        r"\s+",
        " ",
        value
    )

    return value.strip()


# ============================================================
# CLASSIFY JOB
# ============================================================

def classify_job(job):

    title = normalize_text(
        job.get("job_title")
    )

    description = normalize_text(
        job.get("job_description")
    )

    # Title gets much stronger weight
    title_matches = {}

    for category, keywords in ROLE_CATEGORIES.items():

        score = 0

        for keyword in keywords:

            keyword = normalize_text(
                keyword
            )

            if keyword in title:
                score += 10

        for keyword in keywords:

            keyword = normalize_text(
                keyword
            )

            if keyword in description:
                score += 1

        title_matches[category] = score

    best_category = max(
        title_matches,
        key=title_matches.get
    )

    best_score = title_matches[
        best_category
    ]

    if best_score < 10:
        return None, 0

    return best_category, best_score


# ============================================================
# DEDUPLICATION
# ============================================================

def deduplicate_jobs(jobs):

    unique_jobs = []

    seen_urls = set()

    seen_job_keys = set()

    for job in jobs:

        url = job.get("job_url")

        title = normalize_text(
            job.get("job_title")
        )

        company = normalize_text(
            job.get("company")
        )

        key = (
            title,
            company
        )

        if url and url in seen_urls:
            continue

        if key in seen_job_keys:
            continue

        if url:
            seen_urls.add(url)

        seen_job_keys.add(key)

        unique_jobs.append(job)

    return unique_jobs


# ============================================================
# SAVE DATASET
# ============================================================

def save_dataset(jobs):

    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    dataset = {

        "metadata": {
            "dataset_created": datetime.now().isoformat(),
            "source": "Remotive",
            "total_jobs": len(jobs)
        },

        "jobs": jobs
    }

    with open(
        OUTPUT_FILE,
        "w",
        encoding="utf-8"
    ) as file:

        json.dump(
            dataset,
            file,
            indent=4,
            ensure_ascii=False
        )

    return OUTPUT_FILE


# ============================================================
# MAIN
# ============================================================

def main():

    print("=" * 70)
    print("JOB MARKET ANALYTICS")
    print("STEP 8D - LOCAL JOB CLASSIFICATION")
    print("=" * 70)

    scraper = RemotiveScraper()

    # Fetch a broad dataset once.
    print("\nRequesting public job dataset...")

    raw_jobs = scraper.collect_and_normalize(
        query="",
        limit=100
    )

    print(
        f"Jobs received from source: {len(raw_jobs)}"
    )

    # --------------------------------------------------------
    # CLASSIFICATION
    # --------------------------------------------------------

    classified_jobs = []

    rejected = 0

    for job in raw_jobs:

        category, score = classify_job(
            job
        )

        if category is None:

            rejected += 1

            continue

        job["role_category"] = category

        job["classification_score"] = score

        classified_jobs.append(
            job
        )

    # --------------------------------------------------------
    # DEDUPLICATION
    # --------------------------------------------------------

    before_dedup = len(
        classified_jobs
    )

    classified_jobs = deduplicate_jobs(
        classified_jobs
    )

    duplicates = (
        before_dedup
        - len(classified_jobs)
    )

    # --------------------------------------------------------
    # SAVE
    # --------------------------------------------------------

    output_file = save_dataset(
        classified_jobs
    )

    # --------------------------------------------------------
    # SUMMARY
    # --------------------------------------------------------

    print("\n" + "=" * 70)
    print("CLASSIFICATION SUMMARY")
    print("=" * 70)

    print(
        f"Source jobs          : {len(raw_jobs)}"
    )

    print(
        f"Relevant jobs        : {before_dedup}"
    )

    print(
        f"Duplicates removed   : {duplicates}"
    )

    print(
        f"Irrelevant jobs      : {rejected}"
    )

    print(
        f"Final dataset        : {len(classified_jobs)}"
    )

    print(
        f"\nSaved to:\n{output_file}"
    )

    # --------------------------------------------------------
    # ROLE DISTRIBUTION
    # --------------------------------------------------------

    print("\n" + "=" * 70)
    print("ROLE DISTRIBUTION")
    print("=" * 70)

    role_counts = {}

    for job in classified_jobs:

        role = job["role_category"]

        role_counts[role] = (
            role_counts.get(role, 0) + 1
        )

    for role, count in sorted(
        role_counts.items(),
        key=lambda item: item[1],
        reverse=True
    ):

        print(
            f"{role:25} {count}"
        )

    # --------------------------------------------------------
    # SAMPLE
    # --------------------------------------------------------

    print("\n" + "=" * 70)
    print("SAMPLE CLASSIFIED JOBS")
    print("=" * 70)

    for job in classified_jobs[:15]:

        print(
            f"{job['role_category']:22} | "
            f"{job['job_title']} | "
            f"{job['company']}"
        )

    print("\n" + "=" * 70)
    print("LOCAL CLASSIFICATION COMPLETED")
    print("=" * 70)


if __name__ == "__main__":
    main()