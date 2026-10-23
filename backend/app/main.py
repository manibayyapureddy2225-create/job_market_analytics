from fastapi import FastAPI, HTTPException, Query
from sqlalchemy import text
from src.database.db import get_engine
from datetime import date, datetime
from typing import Literal
from pydantic import BaseModel, Field

app = FastAPI(
    title="Job Market Analytics API",
    description="Search and explore jobs from the existing SQLite database.",
    version="1.0.0",
)


@app.get("/")
def home():
    return {
        "message": "Job Market Analytics API is running!",
        "docs": "/docs",
    }


@app.get("/api/health")
def health():
    try:
        with get_engine().connect() as connection:
            total = connection.execute(
                text("SELECT COUNT(*) FROM jobs")
            ).scalar_one()

        return {
            "status": "healthy",
            "database": "connected",
            "total_jobs": total,
        }
    except Exception as exc:
        raise HTTPException(
            status_code=503,
            detail="Database connection failed.",
        ) from exc


@app.get("/api/jobs")
def list_jobs(
    search: str | None = Query(default=None, max_length=100),
    location: str | None = Query(default=None, max_length=100),
    remote_type: str | None = Query(default=None, max_length=50),
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
):
    conditions = []
    params = {"limit": limit, "offset": offset}

    if search and search.strip():
        conditions.append(
            """
            (
                job_title LIKE :search
                OR company LIKE :search
                OR skills LIKE :search
                OR job_description LIKE :search
            )
            """
        )
        params["search"] = f"%{search.strip()}%"

    if location and location.strip():
        conditions.append("location LIKE :location")
        params["location"] = f"%{location.strip()}%"

    if remote_type and remote_type.strip():
        conditions.append("remote_type LIKE :remote_type")
        params["remote_type"] = f"%{remote_type.strip()}%"

    where_clause = (
        "WHERE " + " AND ".join(conditions)
        if conditions
        else ""
    )

    query = text(f"""
        SELECT
            job_id, job_title, company, location, country,
            remote_type, job_type, experience_required,
            salary_min, salary_max, salary_avg, salary_currency,
            salary_period, skills, source, job_url, posted_date
        FROM jobs
        {where_clause}
        ORDER BY job_id DESC
        LIMIT :limit OFFSET :offset
    """)

    count_query = text(
        f"SELECT COUNT(*) FROM jobs {where_clause}"
    )

    try:
        with get_engine().connect() as connection:
            total = connection.execute(
                count_query, params
            ).scalar_one()

            rows = connection.execute(
                query, params
            ).mappings().all()

        return {
            "total": total,
            "limit": limit,
            "offset": offset,
            "jobs": [dict(row) for row in rows],
        }

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail="Unable to retrieve jobs.",
        ) from exc


class ApplicationUpdate(BaseModel):
    status: Literal["Saved", "Applied", "Interview", "Rejected", "Offer"] = "Saved"
    notes: str = Field(default="", max_length=5000)
    application_date: date | None = None


def get_tracker_connection():
    return get_engine().raw_connection()


@app.get("/api/applications")
def list_applications():
    connection = get_tracker_connection()

    try:
        cursor = connection.cursor()
        cursor.execute("""
            SELECT
                a.id,
                a.job_id,
                a.status,
                a.notes,
                a.application_date,
                a.created_at,
                a.updated_at,
                j.job_title,
                j.company,
                j.location,
                j.job_url
            FROM job_applications a
            JOIN jobs j ON j.job_id = a.job_id
            ORDER BY a.updated_at DESC
        """)

        columns = [column[0] for column in cursor.description]
        return [dict(zip(columns, row)) for row in cursor.fetchall()]
    finally:
        connection.close()


@app.post("/api/applications/{job_id}")
def save_application(job_id: int, payload: ApplicationUpdate):
    connection = get_tracker_connection()

    try:
        cursor = connection.cursor()
        # Changed %s to ? for SQLite compatibility
        cursor.execute(
            "SELECT job_id FROM jobs WHERE job_id = ?",
            (job_id,),
        )

        if cursor.fetchone() is None:
            raise HTTPException(status_code=404, detail="Job not found")

        cursor.execute("""
            INSERT INTO job_applications
                (job_id, status, notes, application_date)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(job_id) DO UPDATE SET
                status = excluded.status,
                notes = excluded.notes,
                application_date = excluded.application_date,
                updated_at = CURRENT_TIMESTAMP
        """, (
            job_id,
            payload.status,
            payload.notes,
            payload.application_date.isoformat()
                if payload.application_date else None,
        ))

        connection.commit()
        return {"message": "Application saved", "job_id": job_id}
    finally:
        connection.close()


@app.delete("/api/applications/{job_id}")
def remove_application(job_id: int):
    connection = get_tracker_connection()

    try:
        cursor = connection.cursor()
        # Changed %s to ? for SQLite compatibility
        cursor.execute(
            "DELETE FROM job_applications WHERE job_id = ?",
            (job_id,),
        )
        connection.commit()

        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail="Saved application not found")

        return {"message": "Application removed", "job_id": job_id}
    finally:
        connection.close()