"""
Job Market Analytics
Step 8B - Remotive Job Source Adapter

Collects public remote job listings from Remotive
and converts them into our standard job schema.
"""

from pathlib import Path
from datetime import datetime
import json
import re

import requests
from bs4 import BeautifulSoup

from src.scraping.base_scraper import BaseJobScraper


class RemotiveScraper(BaseJobScraper):

    API_URL = "https://remotive.com/api/remote-jobs"

    def __init__(self):
        super().__init__("Remotive")

    def fetch_jobs(
        self,
        query: str = "data analyst",
        limit: int = 50
    ):

        params = {
            "search": query,
            "limit": limit
        }

        headers = {
            "Accept": "application/json",
            "User-Agent": "JobMarketAnalytics/1.0"
        }

        response = requests.get(
            self.API_URL,
            params=params,
            headers=headers,
            timeout=30
        )

        response.raise_for_status()

        data = response.json()

        return data.get("jobs", [])

    @staticmethod
    def clean_html(html):

        if not html:
            return ""

        soup = BeautifulSoup(
            html,
            "html.parser"
        )

        text = soup.get_text(
            separator=" ",
            strip=True
        )

        text = re.sub(
            r"\s+",
            " ",
            text
        )

        return text.strip()


    @staticmethod
    def parse_salary(salary_text):
        """Parse an explicit numeric range, preserving decimals."""
        if not salary_text:
            return None, None

        text = str(salary_text).replace(",", "").strip()

        pattern = (
            r"(?<![\d.])\$?\s*(\d+(?:\.\d+)?)"
            r"\s*(?:/\s*(?:hr|hour|year|yr|month|mo))?"
            r"\s*(?:-|–|—|\bto\b)\s*"
            r"\$?\s*(\d+(?:\.\d+)?)"
        )

        match = re.search(pattern, text, re.IGNORECASE)

        if not match:
            return None, None

        minimum = float(match.group(1))
        maximum = float(match.group(2))

        if minimum < 0 or maximum < minimum:
            return None, None

        return minimum, maximum

    
    @staticmethod
    def detect_salary_period(salary_text, description=""):
        """Return a pay period only when the wording supports it."""
        text = f"{salary_text or ''} {description or ''}".lower()

        if re.search(r"\bper[- ]word\b|\bper word\b", text):
            return "per_word"

        if re.search(r"/\s*(?:hr|hour)\b|\bper hour\b|\bhourly\b", text):
            return "hourly"

        if re.search(r"/\s*(?:yr|year)\b|\bper year\b|\bannually\b|\bannual salary\b", text):
            return "annual"

        if re.search(r"/\s*(?:mo|month)\b|\bper month\b|\bmonthly\b", text):
            return "monthly"

        return "unknown"

    @staticmethod
    def detect_skills(text):

        skills = [
            "Python",
            "SQL",
            "Excel",
            "Power BI",
            "Tableau",
            "Java",
            "JavaScript",
            "TypeScript",
            "React",
            "Vue.js",
            "Node.js",
            "AWS",
            "Azure",
            "GCP",
            "Docker",
            "Kubernetes",
            "Git",
            "FastAPI",
            "Flask",
            "Django",
            "Pandas",
            "NumPy",
            "Machine Learning",
            "Data Analysis",
            "Data Visualization",
            "Statistics"
        ]

        text_lower = text.lower()

        detected = []

        for skill in skills:

            if skill.lower() in text_lower:

                detected.append(skill)

        return detected

    def normalize_job(self, job):

        description = self.clean_html(
            job.get("description", "")
        )

        salary_text = job.get(
            "salary",
            ""
        )

        salary_min, salary_max = self.parse_salary(
            salary_text
        )

        salary_avg = None

        if (
            salary_min is not None
            and salary_max is not None
        ):
            salary_avg = (
                salary_min + salary_max
            ) / 2

        salary_period = self.detect_salary_period(
            salary_text,
            description
        )

        searchable_text = (
            job.get("title", "")
            + " "
            + description
            + " "
            + " ".join(
                job.get("tags", [])
            )
        )

        skills = self.detect_skills(
            searchable_text
        )

        return {
            "job_title": job.get(
                "title",
                ""
            ).strip(),

            "company": job.get(
                "company_name",
                ""
            ).strip(),

            "location": job.get(
                "candidate_required_location",
                "Remote"
            ),

            "job_type": job.get(
                "job_type"
            ),

            "experience_required": None,

            "salary_min": salary_min,

            "salary_max": salary_max,

            "salary_avg": salary_avg,

            "salary_period": salary_period,

            "salary_currency": "USD",

            "skills": ", ".join(skills),

            "job_description": description,

            "source": self.source_name,

            "job_url": job.get(
                "url"
            ),

            "posted_date": job.get(
                "publication_date"
            ),

            "scraped_date": datetime.now().isoformat(),

            "external_job_id": str(
                job.get("id", "")
            )
        }

    def collect_and_normalize(
        self,
        query="data analyst",
        limit=50
    ):

        raw_jobs = self.fetch_jobs(
            query=query,
            limit=limit
        )

        normalized_jobs = []

        seen_urls = set()

        for job in raw_jobs:

            normalized = self.normalize_job(
                job
            )

            url = normalized.get(
                "job_url"
            )

            if not url:
                continue

            if url in seen_urls:
                continue

            seen_urls.add(url)

            normalized_jobs.append(
                normalized
            )

        return normalized_jobs


def save_raw_jobs(
    jobs,
    query
):

    base_dir = Path(
        __file__
    ).resolve().parents[3]

    output_dir = (
        base_dir
        / "data"
        / "raw"
    )

    output_dir.mkdir(
        parents=True,
        exist_ok=True
    )

    output_file = (
        output_dir
        / f"remotive_{query.replace(' ', '_')}.json"
    )

    with open(
        output_file,
        "w",
        encoding="utf-8"
    ) as file:

        json.dump(
            jobs,
            file,
            indent=4,
            ensure_ascii=False
        )

    return output_file


def main():

    print("=" * 60)
    print("REMOTIVE JOB COLLECTOR")
    print("=" * 60)

    scraper = RemotiveScraper()

    query = "data analyst"

    print(f"\nSearch query: {query}")
    print("Requesting public Remotive API...")

    jobs = scraper.collect_and_normalize(
        query=query,
        limit=50
    )

    print(
        f"\nJobs collected: {len(jobs)}"
    )

    if not jobs:

        print(
            "No jobs returned."
        )

        return

    output_file = save_raw_jobs(
        jobs,
        query
    )

    print(
        f"\nRaw dataset saved:"
    )

    print(output_file)

    print("\nSample records:")
    print("-" * 60)

    for job in jobs[:5]:

        print(
            f"{job['job_title']} | "
            f"{job['company']} | "
            f"{job['location']}"
        )

    print("\n" + "=" * 60)
    print("REMOTIVE COLLECTION COMPLETED")
    print("=" * 60)


if __name__ == "__main__":
    main()