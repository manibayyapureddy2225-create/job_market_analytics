import json
from pathlib import Path
from collections import Counter

BASE_DIR = Path(__file__).resolve().parents[2]

INPUT_FILE = BASE_DIR / "data" / "raw" / "jobs_collected.json"
OUTPUT_FILE = BASE_DIR / "data" / "raw" / "jobs_validated.json"
REPORT_FILE = BASE_DIR / "data" / "processed" / "data_quality_report.json"


ROLE_PATTERNS = {
    "Data Analyst": [
        "data analyst",
        "senior data analyst",
        "junior data analyst",
        "business analyst",
        "bi analyst",
        "business intelligence analyst",
        "analytics analyst",
    ],

    "Data Scientist": [
        "data scientist",
        "senior data scientist",
        "junior data scientist",
        "machine learning scientist",
        "ml scientist",
    ],

    "Data Engineer": [
        "data engineer",
        "senior data engineer",
        "junior data engineer",
        "analytics engineer",
        "big data engineer",
    ],

    
    "Software Developer": [
        "software engineer",
        "software developer",
        "software development engineer",
        "full stack developer",
        "full-stack developer",
        "full stack engineer",
        "full-stack engineer",
        "backend developer",
        "back-end developer",
        "backend engineer",
        "back-end engineer",
        "frontend developer",
        "front-end developer",
        "frontend engineer",
        "front-end engineer",
        "frontend web application developer",
        "web application developer",
        "web developer",
        "web engineer",
        "product engineer",
        "software development",
        "shopify developer",
        "ai engineer",
        "artificial intelligence engineer",
        "full stack rails engineer",
        "full-stack rails engineer",
    ],

}


def classify_role(title, description=""):
    """
    Title-first job classification.
    The title has priority because descriptions
    often mention unrelated technologies/roles.
    """

    title = (title or "").lower().strip()
    description = (description or "").lower()

    # Strong title match
    for role, patterns in ROLE_PATTERNS.items():
        for pattern in patterns:
            if pattern in title:
                return role, 0.95

    # Secondary description validation
    if "data analyst" in description:
        return "Data Analyst", 0.80

    if "data scientist" in description:
        return "Data Scientist", 0.80

    if "data engineer" in description:
        return "Data Engineer", 0.80

    return None, 0.0


def validate_job(job):
    title = job.get("job_title")
    description = job.get("job_description")

    role, confidence = classify_role(title, description)

    job["validated_role"] = role
    job["role_confidence"] = confidence

    # Basic required-field validation
    required_fields = [
        "job_title",
        "company",
        "job_url",
    ]

    missing_fields = [
        field
        for field in required_fields
        if not job.get(field)
    ]

    job["missing_required_fields"] = missing_fields

    # Quality checks
    has_description = bool(
        str(job.get("job_description") or "").strip()
    )

    has_location = bool(
        str(job.get("location") or "").strip()
    )

    has_salary = (
        job.get("salary_min") is not None
        or job.get("salary_max") is not None
        or job.get("salary_avg") is not None
    )

    job["has_description"] = has_description
    job["has_location"] = has_location
    job["has_salary"] = has_salary


    # Final validation decision
    job["is_valid"] = (
        role is not None
        and confidence >= 0.80
        and len(missing_fields) == 0
    )

    rejection_reasons = []

    if role is None:
        rejection_reasons.append("Role not matched")

    if len(missing_fields) > 0:
        rejection_reasons.append(
            "Missing required fields: " + ", ".join(missing_fields)
        )

    job["rejection_reason"] = (
        "; ".join(rejection_reasons) if rejection_reasons else None
    )

    return job



def main():
    print("=" * 60)
    print("JOB MARKET ANALYTICS - DATA QUALITY VALIDATOR")
    print("=" * 60)

    if not INPUT_FILE.exists():
        raise FileNotFoundError(
            f"Input dataset not found: {INPUT_FILE}"
        )

    with open(INPUT_FILE, "r", encoding="utf-8") as file:
        jobs = json.load(file)

    if not isinstance(jobs, list):
        raise ValueError("Input dataset must contain a list.")

    print(f"\nInput records: {len(jobs)}")

    validated_jobs = []

    for job in jobs:
        validated_jobs.append(validate_job(job))

    valid_jobs = [
        job
        for job in validated_jobs
        if job["is_valid"]
    ]

    rejected_jobs = [
        job
        for job in validated_jobs
        if not job["is_valid"]
    ]

    # Save only validated jobs
    OUTPUT_FILE.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    with open(OUTPUT_FILE, "w", encoding="utf-8") as file:
        json.dump(
            valid_jobs,
            file,
            indent=2,
            ensure_ascii=False
        )

    # Role distribution
    role_counts = Counter(
        job["validated_role"]
        for job in valid_jobs
    )

    source_counts = Counter(
        job.get("source", "Unknown")
        for job in valid_jobs
    )

    rejected_by_source = Counter(
        job.get("source", "Unknown")
        for job in rejected_jobs
    )

    salary_count = sum(
        1 for job in valid_jobs
        if job["has_salary"]
    )

    location_count = sum(
        1 for job in valid_jobs
        if job["has_location"]
    )

    description_count = sum(
        1 for job in valid_jobs
        if job["has_description"]
    )

    report = {
        "input_records": len(jobs),
        "valid_records": len(valid_jobs),
        "rejected_records": len(rejected_jobs),

        "validation_rate": round(
            len(valid_jobs) / len(jobs) * 100,
            2
        ) if jobs else 0,

        "role_distribution": dict(role_counts),

        "source_distribution": dict(source_counts),

        "rejected_by_source": dict(rejected_by_source),

        "data_completeness": {
            "salary_available": salary_count,
            "salary_percentage": round(
                salary_count / len(valid_jobs) * 100,
                2
            ) if valid_jobs else 0,

            "location_available": location_count,
            "location_percentage": round(
                location_count / len(valid_jobs) * 100,
                2
            ) if valid_jobs else 0,

            "description_available": description_count,
            "description_percentage": round(
                description_count / len(valid_jobs) * 100,
                2
            ) if valid_jobs else 0,
        },

        "rejected_jobs": [
            {
                "job_title": job.get("job_title"),
                "company": job.get("company"),
                "source": job.get("source"),
                "job_url": job.get("job_url"),
                "reason":job.get("rejection_reason"),
                
            }
            for job in rejected_jobs
        ],
    }

    with open(REPORT_FILE, "w", encoding="utf-8") as file:
        json.dump(
            report,
            file,
            indent=2,
            ensure_ascii=False
        )

    print("\nVALIDATION RESULTS")
    print("-" * 40)
    print(f"Input records       : {len(jobs)}")
    print(f"Valid records       : {len(valid_jobs)}")
    print(f"Rejected records    : {len(rejected_jobs)}")
    print(
        f"Validation rate     : "
        f"{report['validation_rate']}%"
    )

    print("\nROLE DISTRIBUTION")
    print("-" * 40)

    for role, count in role_counts.items():
        print(f"{role:<25}: {count}")

    print("\nSOURCE DISTRIBUTION")
    print("-" * 40)

    for source, count in source_counts.items():
        print(f"{source:<25}: {count}")

    print("\nREJECTED BY SOURCE")
    print("-" * 40)

    for source, count in rejected_by_source.items():
        print(f"{source:<25}: {count}")

    print("\nDATA COMPLETENESS")
    print("-" * 40)

    print(
        f"Salary available     : "
        f"{report['data_completeness']['salary_percentage']}%"
    )

    print(
        f"Location available   : "
        f"{report['data_completeness']['location_percentage']}%"
    )

    print(
        f"Description available: "
        f"{report['data_completeness']['description_percentage']}%"
    )

    print("\nValidated dataset:")
    print(OUTPUT_FILE)

    print("\nQuality report:")
    print(REPORT_FILE)

    print("\n" + "=" * 60)
    print("QUALITY VALIDATION COMPLETE")
    print("=" * 60)


if __name__ == "__main__":
    main()