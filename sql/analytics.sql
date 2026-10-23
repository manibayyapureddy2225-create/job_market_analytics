-- ============================================================
-- JOB MARKET ANALYTICS
-- Premium SQL Analytics Layer
-- ============================================================


-- ============================================================
-- 1. OVERALL MARKET SUMMARY
-- ============================================================

SELECT
    COUNT(*) AS total_jobs,
    COUNT(DISTINCT company) AS unique_companies,
    COUNT(DISTINCT location) AS unique_locations,
    COUNT(DISTINCT source) AS job_sources,
    ROUND(AVG(salary_avg), 2) AS average_salary
FROM jobs;


-- ============================================================
-- 2. JOB DEMAND BY ROLE
-- ============================================================

SELECT
    role_category,
    COUNT(*) AS job_count,
    ROUND(
        COUNT(*) * 100.0 /
        (SELECT COUNT(*) FROM jobs),
        2
    ) AS demand_percentage
FROM jobs
GROUP BY role_category
ORDER BY job_count DESC;


-- ============================================================
-- 3. JOB DEMAND BY LOCATION
-- ============================================================

SELECT
    location,
    COUNT(*) AS job_count,
    ROUND(
        COUNT(*) * 100.0 /
        (SELECT COUNT(*) FROM jobs),
        2
    ) AS demand_percentage
FROM jobs
WHERE location IS NOT NULL
  AND TRIM(location) <> ''
GROUP BY location
ORDER BY job_count DESC;


-- ============================================================
-- 4. TOP HIRING COMPANIES
-- ============================================================

SELECT
    company,
    COUNT(*) AS job_count
FROM jobs
WHERE company IS NOT NULL
  AND TRIM(company) <> ''
GROUP BY company
ORDER BY job_count DESC
LIMIT 15;


-- ============================================================
-- 5. EXPERIENCE LEVEL DEMAND
-- ============================================================

SELECT
    experience_required,
    COUNT(*) AS job_count,
    ROUND(
        COUNT(*) * 100.0 /
        (SELECT COUNT(*) FROM jobs),
        2
    ) AS demand_percentage
FROM jobs
WHERE experience_required IS NOT NULL
  AND TRIM(experience_required) <> ''
GROUP BY experience_required
ORDER BY job_count DESC;


-- ============================================================
-- 6. SALARY BY ROLE
-- ============================================================

SELECT
    role_category,
    COUNT(*) AS jobs_with_salary,
    ROUND(MIN(salary_avg), 2) AS minimum_salary,
    ROUND(AVG(salary_avg), 2) AS average_salary,
    ROUND(MAX(salary_avg), 2) AS maximum_salary
FROM jobs
WHERE salary_avg IS NOT NULL
GROUP BY role_category
ORDER BY average_salary DESC;


-- ============================================================
-- 7. SALARY BY LOCATION
-- ============================================================

SELECT
    location,
    COUNT(*) AS jobs_with_salary,
    ROUND(AVG(salary_avg), 2) AS average_salary,
    ROUND(MAX(salary_avg), 2) AS maximum_salary
FROM jobs
WHERE location IS NOT NULL
  AND salary_avg IS NOT NULL
GROUP BY location
HAVING COUNT(*) >= 2
ORDER BY average_salary DESC;


-- ============================================================
-- 8. SALARY DISTRIBUTION
-- ============================================================

SELECT
    CASE
        WHEN salary_avg < 50000 THEN '< 50K'
        WHEN salary_avg < 100000 THEN '50K - 100K'
        WHEN salary_avg < 150000 THEN '100K - 150K'
        WHEN salary_avg < 200000 THEN '150K - 200K'
        ELSE '200K+'
    END AS salary_band,
    COUNT(*) AS job_count
FROM jobs
WHERE salary_avg IS NOT NULL
GROUP BY salary_band
ORDER BY
    CASE salary_band
        WHEN '< 50K' THEN 1
        WHEN '50K - 100K' THEN 2
        WHEN '100K - 150K' THEN 3
        WHEN '150K - 200K' THEN 4
        WHEN '200K+' THEN 5
    END;


-- ============================================================
-- 9. JOB TYPE ANALYSIS
-- ============================================================

SELECT
    job_type,
    COUNT(*) AS job_count,
    ROUND(
        COUNT(*) * 100.0 /
        (SELECT COUNT(*) FROM jobs),
        2
    ) AS percentage
FROM jobs
WHERE job_type IS NOT NULL
  AND TRIM(job_type) <> ''
GROUP BY job_type
ORDER BY job_count DESC;


-- ============================================================
-- 10. REMOTE WORK ANALYSIS
-- ============================================================

SELECT
    remote_type,
    COUNT(*) AS job_count,
    ROUND(
        COUNT(*) * 100.0 /
        (SELECT COUNT(*) FROM jobs),
        2
    ) AS percentage
FROM jobs
GROUP BY remote_type
ORDER BY job_count DESC;


-- ============================================================
-- 11. JOB DEMAND BY SOURCE
-- ============================================================

SELECT
    source,
    COUNT(*) AS job_count,
    ROUND(
        COUNT(*) * 100.0 /
        (SELECT COUNT(*) FROM jobs),
        2
    ) AS source_share
FROM jobs
GROUP BY source
ORDER BY job_count DESC;


-- ============================================================
-- 12. SOURCE × ROLE ANALYSISs
-- ============================================================

SELECT
    source,
    role_category,
    COUNT(*) AS job_count
FROM jobs
GROUP BY source, role_category
ORDER BY source, job_count DESC;


-- ============================================================
-- 13. ROLE × EXPERIENCE ANALYSIS
-- ============================================================

SELECT
    role_category,
    experience_required,
    COUNT(*) AS job_count
FROM jobs
WHERE experience_required IS NOT NULL
GROUP BY role_category, experience_required
ORDER BY role_category, job_count DESC;


-- ============================================================
-- 14. TOP PAYING JOBS
-- ============================================================

SELECT
    job_title,
    company,
    role_category,
    location,
    salary_avg,
    salary_currency,
    source
FROM jobs
WHERE salary_avg IS NOT NULL
ORDER BY salary_avg DESC
LIMIT 20;


-- ============================================================
-- 15. DATA QUALITY SUMMARY
-- ============================================================

SELECT
    COUNT(*) AS total_jobs,

    SUM(
        CASE
            WHEN salary_avg IS NOT NULL THEN 1
            ELSE 0
        END
    ) AS jobs_with_salary,

    ROUND(
        SUM(
            CASE
                WHEN salary_avg IS NOT NULL THEN 1
                ELSE 0
            END
        ) * 100.0 / COUNT(*),
        2
    ) AS salary_coverage_percentage,

    SUM(
        CASE
            WHEN location IS NOT NULL
             AND TRIM(location) <> ''
            THEN 1
            ELSE 0
        END
    ) AS jobs_with_location,

    SUM(
        CASE
            WHEN job_description IS NOT NULL
             AND TRIM(job_description) <> ''
            THEN 1
            ELSE 0
        END
    ) AS jobs_with_description

FROM jobs;

-- ============================================================
-- 16. SALARY QUALITY BY CURRENCY AND PERIOD
-- ============================================================

SELECT
    COALESCE(NULLIF(TRIM(salary_currency), ''), 'unknown')
        AS salary_currency,

    COALESCE(NULLIF(LOWER(TRIM(salary_period)), ''), 'unknown')
        AS salary_period,

    COUNT(*) AS jobs_with_salary,

    ROUND(MIN(salary_avg), 2) AS minimum_recorded_value,
    ROUND(AVG(salary_avg), 2) AS average_recorded_value,
    ROUND(MAX(salary_avg), 2) AS maximum_recorded_value

FROM jobs
WHERE salary_avg IS NOT NULL

GROUP BY
    COALESCE(NULLIF(TRIM(salary_currency), ''), 'unknown'),
    COALESCE(NULLIF(LOWER(TRIM(salary_period)), ''), 'unknown')

ORDER BY jobs_with_salary DESC;

SELECT
    COALESCE(NULLIF(TRIM(salary_currency), ''), 'unknown')
        AS salary_currency,
    COALESCE(NULLIF(LOWER(TRIM(salary_period)), ''), 'unknown')
        AS salary_period,
    COUNT(*) AS jobs_with_salary,
    ROUND(MIN(salary_avg), 2) AS minimum_recorded_value,
    ROUND(AVG(salary_avg), 2) AS average_recorded_value,
    ROUND(MAX(salary_avg), 2) AS maximum_recorded_value
FROM jobs
WHERE salary_avg IS NOT NULL
GROUP BY
    COALESCE(NULLIF(TRIM(salary_currency), ''), 'unknown'),
    COALESCE(NULLIF(LOWER(TRIM(salary_period)), ''), 'unknown')
ORDER BY jobs_with_salary DESC;

-- ============================================================
-- 17. SKILL DEMAND ANALYSIS
-- ============================================================

WITH RECURSIVE split_skills(job_id, skill_name, remaining) AS (
    -- Base case: take the initial string from the skills column
    SELECT 
        job_id,
        '' AS skill_name,
        skills AS remaining
    FROM jobs
    WHERE skills IS NOT NULL AND TRIM(skills) <> ''

    UNION ALL

    -- Recursive step: peel off each skill separated by a comma
    SELECT 
        job_id,
        TRIM(
            CASE 
                WHEN INSTR(remaining, ',') > 0 THEN SUBSTR(remaining, 1, INSTR(remaining, ',') - 1)
                ELSE remaining
            END
        ) AS skill_name,
        CASE 
            WHEN INSTR(remaining, ',') > 0 THEN SUBSTR(remaining, INSTR(remaining, ',') + 1)
            ELSE ''
        END AS remaining
    FROM split_skills
    WHERE remaining <> ''
)
SELECT 
    LOWER(skill_name) AS skill_name,
    COUNT(DISTINCT job_id) AS job_count
FROM split_skills
WHERE skill_name IS NOT NULL 
  AND skill_name <> ''
GROUP BY LOWER(skill_name)
ORDER BY job_count DESC
LIMIT 20;