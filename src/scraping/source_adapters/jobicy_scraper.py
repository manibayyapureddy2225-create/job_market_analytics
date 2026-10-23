import json
import re
from pathlib import Path
from datetime import datetime, timezone

import requests
from bs4 import BeautifulSoup

from src.scraping.base_scraper import BaseJobScraper


BASE_DIR = Path(__file__).resolve().parents[3]
RAW_DIR = BASE_DIR / "data" / "raw"

API_URL = "https://jobicy.com/api/v2/remote-jobs"


class JobicyScraper(BaseJobScraper):

    def __init__(self):
        super().__init__("Jobicy")

    def clean_html(self, html):
        if not html:
            return ""

        soup = BeautifulSoup(html, "html.parser")

        return soup.get_text(
            separator=" ",
            strip=True
        )

    def extract_skills(self, text):
        if not text:
            return ""

        skill_patterns = [
            "Python",
            "Java",
            "JavaScript",
            "TypeScript",
            "C++",
            "C#",
            "SQL",
            "Pandas",
            "NumPy",
            "Excel",
            "Power BI",
            "Tableau",
            "Machine Learning",
            "Deep Learning",
            "NLP",
            "FastAPI",
            "Flask",
            "Django",
            "REST API",
            "React",
            "Vue.js",
            "Node.js",
            "Spring Boot",
            "AWS",
            "Azure",
            "GCP",
            "Docker",
            "Kubernetes",
            "Git",
            "MySQL",
            "PostgreSQL",
            "MongoDB",
            "Data Visualization",
            "Statistics",
            "Jupyter",
        ]

        found = []

        text_lower = text.lower()

        for skill in skill_patterns:
            if skill.lower() in text_lower:
                found.append(skill)

        return ", ".join(sorted(set(found)))

    def classify_role(self, title, description):
        """
        Classify jobs using title-first scoring.

        The job title receives much more weight than the
        description to reduce false positives.
        """
        title = (title or "").lower().strip()
        description = (description or "").lower()

        role_patterns = {
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
                "web developer",
                "web engineer",
                "product engineer",
            ],
        }

        # --------------------------------------------------
        # 1. Strong title match
        # --------------------------------------------------
        for role, patterns in role_patterns.items():
            for pattern in patterns:
                if pattern in title:
                    return role

        # --------------------------------------------------
        # 2. Limited description fallback
        # --------------------------------------------------
        data_terms = [
            "data",
            "analytics",
            "machine learning",
            "artificial intelligence",
            "software",
            "engineering",
        ]

        title_has_data_context = any(
            term in title for term in data_terms
        )

        if title_has_data_context:
            if (
                "data engineering" in description
                or "data engineer" in description
            ):
                return "Data Engineer"

            if (
                "data scientist" in description
                or "machine learning scientist" in description
            ):
                return "Data Scientist"

            if (
                "data analyst" in description
                or "business intelligence analyst" in description
            ):
                return "Data Analyst"

        return None

    def normalize_jobicy_job(self, job):
        title = job.get("jobTitle", "")
        company = job.get("companyName", "")
        location = job.get("jobGeo", "")

        description = self.clean_html(
            job.get("jobDescription", "")
        )

        excerpt = self.clean_html(
            job.get("jobExcerpt", "")
        )

        combined_description = (
            f"{excerpt} {description}".strip()
        )

        role_category = self.classify_role(
            title,
            combined_description
        )

        role_confidence = 0.95 if role_category else 0.0

        job_types = job.get("jobType", [])

        if isinstance(job_types, list):
            job_type = ", ".join(job_types)
        else:
            job_type = str(job_types)

        salary_min = job.get("salaryMin")
        salary_max = job.get("salaryMax")

        salary_avg = None

        if salary_min is not None and salary_max is not None:
            try:
                salary_avg = (
                    float(salary_min) +
                    float(salary_max)
                ) / 2
            except (ValueError, TypeError):
                pass

        posted_date = job.get("pubDate")

        return {
            "external_job_id": str(job.get("id", "")),

            "job_title": title,

            "role_category": role_category,

            "role_confidence": role_confidence,

            "company": company,

            "location": location,

            "country": location,

            "remote_type": "Remote",

            "job_type": job_type,

            "experience_required": job.get(
                "jobLevel"
            ),

            "salary_min": salary_min,

            "salary_max": salary_max,

            "salary_avg": salary_avg,

            "salary_currency": job.get(
                "salaryCurrency"
            ),

            "skills": self.extract_skills(
                combined_description
            ),

            "job_description": combined_description,

            "source": "Jobicy",

            "job_url": job.get("url"),

            "posted_date": posted_date,

            "scraped_date": datetime.now(
                timezone.utc
            ).isoformat(),
        }

    def fetch_jobs(
        self,
        query="",
        location="",
        count=100,
        max_pages=5
    ):
        jobs = []

        params = {
            "count": count
        }

        if query:
            params["tag"] = query

        if location:
            params["geo"] = location

        for page in range(max_pages):

            response = requests.get(
                API_URL,
                params=params,
                headers={
                    "Accept": "application/json"
                },
                timeout=30
            )

            response.raise_for_status()

            data = response.json()

            if data.get("success") is False:
                raise RuntimeError(
                    data.get(
                        "error",
                        "Jobicy API request failed"
                    )
                )

            page_jobs = data.get(
                "jobs",
                []
            )

            print(
                f"Page {page + 1}: "
                f"{len(page_jobs)} jobs"
            )

            for job in page_jobs:
                normalized = (
                    self.normalize_jobicy_job(job)
                )

                if normalized["role_category"]:
                    jobs.append(normalized)

            next_cursor = data.get(
                "nextCursor"
            )

            if not next_cursor:
                break

            params["cursor"] = next_cursor

        unique_jobs = {}

        for job in jobs:
            url = job.get("job_url")

            if url:
                unique_jobs[url] = job

        return list(unique_jobs.values())

    def save_raw(self, jobs):
        RAW_DIR.mkdir(
            parents=True,
            exist_ok=True
        )

        output_file = (
            RAW_DIR / "jobicy_jobs.json"
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
            f"\nSaved {len(jobs)} jobs to:"
            f"\n{output_file}"
        )


if __name__ == "__main__":

    scraper = JobicyScraper()

    print("=" * 60)
    print("JOBICY JOB COLLECTOR")
    print("=" * 60)

    jobs = scraper.fetch_jobs(
        query="data",
        count=100,
        max_pages=3
    )

    scraper.save_raw(jobs)

    print("\nRelevant jobs:", len(jobs))

    print("\nSample:")

    for job in jobs[:10]:
        print(
            f"{job['role_category']} | "
            f"{job['job_title']} | "
            f"{job['company']}"
        )