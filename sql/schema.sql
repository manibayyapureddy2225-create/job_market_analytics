CREATE TABLE IF NOT EXISTS jobs (
    job_id INTEGER PRIMARY KEY AUTOINCREMENT,

    external_job_id TEXT,

    job_title TEXT NOT NULL,

    role_category TEXT,

    company TEXT,

    location TEXT,

    country TEXT,

    remote_type TEXT,

    job_type TEXT,

    experience_required TEXT,

    salary_min REAL,

    salary_max REAL,

    salary_avg REAL,

    salary_currency TEXT,

    skills TEXT,

    job_description TEXT,

    source TEXT,

    job_url TEXT UNIQUE,

    posted_date TEXT,

    scraped_date TEXT,

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
-- ============================================================
-- JOB SKILLS
-- ============================================================

CREATE TABLE IF NOT EXISTS job_skills (
    skill_id INTEGER PRIMARY KEY AUTOINCREMENT,
    job_id INTEGER NOT NULL,
    skill TEXT NOT NULL,

    FOREIGN KEY (job_id)
        REFERENCES jobs(job_id),

    UNIQUE(job_id, skill)
);

CREATE INDEX IF NOT EXISTS idx_job_skills_skill
ON job_skills(skill);

CREATE INDEX IF NOT EXISTS idx_job_skills_job_id
ON job_skills(job_id);