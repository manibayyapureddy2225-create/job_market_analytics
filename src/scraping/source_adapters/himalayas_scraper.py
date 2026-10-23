import json
import re
import time
from pathlib import Path
from datetime import datetime, timezone

import requests
from bs4 import BeautifulSoup

from src.scraping.base_scraper import BaseJobScraper


BASE_DIR = Path(__file__).resolve().parents[3]
RAW_DIR = BASE_DIR / "data" / "raw"

API_URL = "https://himalayas.app/jobs/api"


class HimalayasScraper(BaseJobScraper):

    def __init__(self):
        super().__init__("Himalayas")

    def clean_html(self, html):
        if not html:
            return ""

        soup = BeautifulSoup(html, "html.parser")

        return re.sub(
            r"\s+",
            " ",
            soup.get_text(" ", strip=True)
        ).strip()

    def classify_role(self, title, description):

        title = (title or "").lower().strip()
        description = (description or "").lower()

        role_patterns = {
            "Data Analyst": [
                "data analyst",
                "business analyst",
                "bi analyst",
                "business intelligence analyst",
                "analytics analyst",
            ],

            "Data Scientist": [
                "data scientist",
                "machine learning scientist",
                "ml scientist",
            ],

            "Data Engineer": [
                "data engineer",
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
                "web developer",
                "web engineer",
                "product engineer",
            ],
        }

        for role, patterns in role_patterns.items():
            for pattern in patterns:
                if pattern in title:
                    return role

        return None

    def parse_salary(self, job):

        salary_min = job.get("minSalary")
        salary_max = job.get("maxSalary")

        try:
            salary_min = float(salary_min) if salary_min is not None else None
        except (ValueError, TypeError):
            salary_min = None

        try:
            salary_max = float(salary_max) if salary_max is not None else None
        except (ValueError, TypeError):
            salary_max = None

        salary_avg = None

        if salary_min is not None and salary_max is not None:
            salary_avg = (salary_min + salary_max) / 2

        return salary_min, salary_max, salary_avg

    def fetch_jobs(self, query=None, location=None):

        all_jobs = []
        cursor = None
        page = 1

        print("=" * 60)
        print("HIMALAYAS JOB COLLECTOR")
        print("=" * 60)

        MAX_PAGES = 10

        while page <= MAX_PAGES:

            params = {
                "limit": 20
            }

            if cursor:
                params["cursor"] = cursor

            print(f"\nFetching page {page}...")

            response = requests.get(
                API_URL,
                params=params,
                timeout=30
            )

            response.raise_for_status()

            data = response.json()

            jobs = data.get("jobs", [])

            print(f"Jobs received: {len(jobs)}")

            for job in jobs:

                title = job.get("title", "")

                description = self.clean_html(
                    job.get("description", "")
                )

                role_category = self.classify_role(
                    title,
                    description
                )

                # Keep only jobs relevant to our project
                if not role_category:
                    continue

                salary_min, salary_max, salary_avg = (
                    self.parse_salary(job)
                )

                locations = job.get(
                    "locationRestrictions",
                    []
                )

                location_names = [
                    item.get("name")
                    for item in locations
                    if isinstance(item, dict)
                    and item.get("name")
                ]

                location_text = (
                    ", ".join(location_names)
                    if location_names
                    else "Worldwide"
                )

                seniority = job.get("seniority")

                if isinstance(seniority, list):
                    experience = ", ".join(
                        str(x) for x in seniority
                    )
                else:
                    experience = seniority

                pub_date = job.get("pubDate")

                if isinstance(pub_date, (int, float)):

                    try:
                        posted_date = datetime.fromtimestamp(
                            pub_date / 1000,
                            tz=timezone.utc
                        ).isoformat()
                    except (ValueError, OSError):
                        posted_date = None

                else:
                    posted_date = pub_date

                normalized_job = {
                    "external_job_id": job.get("guid"),

                    "job_title": title,

                    "role_category": role_category,

                    "company": job.get(
                        "companyName"
                    ),

                    "location": location_text,

                    "country": (
                        location_names[0]
                        if location_names
                        else None
                    ),

                    "remote_type": "Remote",

                    "job_type": job.get(
                        "employmentType"
                    ),

                    "experience_required": experience,

                    "salary_min": salary_min,

                    "salary_max": salary_max,

                    "salary_avg": salary_avg,

                    "salary_currency": job.get(
                        "currency"
                    ),

                    "skills": None,

                    "job_description": description,

                    "source": "Himalayas",

                    "job_url": job.get(
                        "applicationLink"
                    ),

                    "posted_date": posted_date,

                    "scraped_date": datetime.now(
                        timezone.utc
                    ).isoformat(),

                    "role_confidence": (
                        0.95
                        if role_category
                        else 0.0
                    ),
                }

                all_jobs.append(normalized_job)

            cursor = data.get("nextCursor")

            if not cursor:
                break

            page += 1

            # Avoid aggressive requests
            time.sleep(1)
            if page > MAX_PAGES:
              print(
                f"\nReached maximum collection limit: "
                f"{MAX_PAGES} pages"
            )

        # Deduplicate
        unique_jobs = {}

        for job in all_jobs:

            url = job.get("job_url")

            if not url:
                continue

            if url not in unique_jobs:
                unique_jobs[url] = job

        final_jobs = list(
            unique_jobs.values()
        )

        print("\n" + "-" * 60)
        print("HIMALAYAS COLLECTION SUMMARY")
        print("-" * 60)

        print(
            f"Relevant jobs: {len(final_jobs)}"
        )

        return final_jobs

    def save_jobs(self, jobs):

        RAW_DIR.mkdir(
            parents=True,
            exist_ok=True
        )

        output_file = (
            RAW_DIR / "himalayas_jobs.json"
        )

        with open(
            output_file,
            "w",
            encoding="utf-8"
        ) as file:

            json.dump(
                jobs,
                file,
                indent=2,
                ensure_ascii=False
            )

        print(
            f"\nSaved Himalayas data:"
            f"\n{output_file}"
        )


def main():

    scraper = HimalayasScraper()

    jobs = scraper.fetch_jobs()

    scraper.save_jobs(jobs)

    print("\n" + "=" * 60)
    print("HIMALAYAS COLLECTION COMPLETE")
    print("=" * 60)


if __name__ == "__main__":
    main()