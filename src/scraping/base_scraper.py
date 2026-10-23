"""
Job Market Analytics
Step 8 - Base Scraper Architecture

Defines the common interface that all job-source
collectors should follow.
"""

from abc import ABC, abstractmethod
from typing import List, Dict


class BaseJobScraper(ABC):
    """
    Abstract base class for job-source collectors.
    """

    def __init__(self, source_name: str):
        self.source_name = source_name

    @abstractmethod
    def fetch_jobs(self, query: str, location: str) -> List[Dict]:
        """
        Fetch jobs from the source.
        """
        raise NotImplementedError

    def normalize_job(self, job: Dict) -> Dict:
        """
        Normalize a job record into the project's
        standard schema.
        """

        return {
            "job_title": job.get("job_title"),
            "company": job.get("company"),
            "location": job.get("location"),
            "job_type": job.get("job_type"),
            "experience_required": job.get(
                "experience_required"
            ),
            "salary_min": job.get("salary_min"),
            "salary_max": job.get("salary_max"),
            "salary_currency": job.get(
                "salary_currency"
            ),
            "skills": job.get("skills"),
            "job_description": job.get(
                "job_description"
            ),
            "source": self.source_name,
            "job_url": job.get("job_url"),
            "posted_date": job.get("posted_date"),
            "scraped_date": job.get("scraped_date")
        }

    def normalize_jobs(
        self,
        jobs: List[Dict]
    ) -> List[Dict]:
        """
        Normalize multiple job records.
        """

        return [
            self.normalize_job(job)
            for job in jobs
        ]