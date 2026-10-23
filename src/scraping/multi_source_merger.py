import json
from pathlib import Path
from datetime import datetime, timezone


BASE_DIR = Path(__file__).resolve().parents[2]

RAW_DIR = BASE_DIR / "data" / "raw"

REMOTIVE_FILE = RAW_DIR / "remotive_data_analyst.json"
JOBICY_FILE = RAW_DIR / "jobicy_jobs.json"
HIMALAYAS_FILE = RAW_DIR / "himalayas_jobs.json"
OUTPUT_FILE = RAW_DIR / "jobs_collected.json"


def load_json(file_path):
    if not file_path.exists():
        print(f"WARNING: File not found: {file_path}")
        return []

    with open(
        file_path,
        "r",
        encoding="utf-8"
    ) as file:

        data = json.load(file)

    if isinstance(data, dict):
        return data.get("jobs", [])

    return data


def normalize_job(job, source):
    """
    Make sure every source follows the same schema.
    """

    return {
        "external_job_id": job.get(
            "external_job_id"
        ),

        "job_title": job.get(
            "job_title"
        ),

        "role_category": job.get(
            "role_category"
        ),

        "company": job.get(
            "company"
        ),

        "location": job.get(
            "location"
        ),

        "country": job.get(
            "country"
        ),

        "remote_type": job.get(
            "remote_type"
        ),

        "job_type": job.get(
            "job_type"
        ),

        "experience_required": job.get(
            "experience_required"
        ),

        "salary_min": job.get(
            "salary_min"
        ),

        "salary_max": job.get(
            "salary_max"
        ),

        "salary_avg": job.get(
            "salary_avg"
        ),
        
        "salary_period": job.get(
            "salary_period",
            "unknown"
        ),


        "salary_currency": job.get(
            "salary_currency"
        ),

        "skills": job.get(
            "skills"
        ),

        "job_description": job.get(
            "job_description"
        ),

        "source": source,

        "job_url": job.get(
            "job_url"
        ),

        "posted_date": job.get(
            "posted_date"
        ),

        "scraped_date": job.get(
            "scraped_date"
        )
        or datetime.now(
            timezone.utc
        ).isoformat(),
    }


def merge_jobs():

    print("=" * 60)
    print("MULTI-SOURCE JOB MERGER")
    print("=" * 60)

    print("\nLoading sources...")

    remotive_jobs = load_json(
        REMOTIVE_FILE
    )

    jobicy_jobs = load_json(
        JOBICY_FILE
    )
    himalayas_jobs = load_json(HIMALAYAS_FILE)

    print(
        f"Remotive records : "
        f"{len(remotive_jobs)}"
    )

    print(
        f"Jobicy records   : "
        f"{len(jobicy_jobs)}"
    )
    print(f"Himalayas records : {len(himalayas_jobs)}")



    all_jobs = []

    for job in remotive_jobs:

        normalized = normalize_job(
            job,
            "Remotive"
        )

        if normalized["job_url"]:
            all_jobs.append(normalized)

    for job in jobicy_jobs:

        normalized = normalize_job(
            job,
            "Jobicy"
        )

        if normalized["job_url"]:
            all_jobs.append(normalized)
    for job in himalayas_jobs:
         normalized = normalize_job(job, "Himalayas")
         if normalized["job_url"]:
          all_jobs.append(normalized)


    print(
        f"\nCombined records: "
        f"{len(all_jobs)}"
    )

    # --------------------------------------------------
    # Deduplicate using job URL
    # --------------------------------------------------

    unique_jobs = {}

    duplicates = 0

    for job in all_jobs:

        url = job["job_url"]

        if url in unique_jobs:
            duplicates += 1
            continue

        unique_jobs[url] = job

    final_jobs = list(
        unique_jobs.values()
    )

    print(
        f"Duplicates removed: "
        f"{duplicates}"
    )

    print(
        f"Final unique jobs: "
        f"{len(final_jobs)}"
    )

    # --------------------------------------------------
    # Save master raw dataset
    # --------------------------------------------------

    with open(
        OUTPUT_FILE,
        "w",
        encoding="utf-8"
    ) as file:

        json.dump(
            final_jobs,
            file,
            indent=2,
            ensure_ascii=False
        )

    print(
        f"\nMaster dataset saved:"
        f"\n{OUTPUT_FILE}"
    )

    # --------------------------------------------------
    # Source distribution
    # --------------------------------------------------

    source_counts = {}

    for job in final_jobs:

        source = job["source"]

        source_counts[source] = (
            source_counts.get(source, 0) + 1
        )

    print("\nSOURCE DISTRIBUTION")

    for source, count in source_counts.items():

        print(
            f"{source}: {count}"
        )

    print("\n" + "=" * 60)
    print("MERGE COMPLETE")
    print("=" * 60)


if __name__ == "__main__":
    merge_jobs()