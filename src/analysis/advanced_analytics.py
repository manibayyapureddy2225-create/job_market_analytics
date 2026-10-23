"""
Job Market Analytics
Step 7 - Advanced Market Analytics Engine

Generates advanced job-market insights:
- Market KPIs
- Skill demand and salary
- Role salary analysis
- Location salary analysis
- Experience salary analysis
- Skill combinations
- Top-paying jobs
"""

from pathlib import Path
from itertools import combinations

import pandas as pd


# ============================================================
# PATHS
# ============================================================

BASE_DIR = Path(__file__).resolve().parents[2]

INPUT_FILE = BASE_DIR / "data" / "processed" / "jobs_cleaned.csv"
SKILL_FILE = BASE_DIR / "data" / "processed" / "job_skills.csv"

OUTPUT_DIR = BASE_DIR / "data" / "processed"


# ============================================================
# LOAD DATA
# ============================================================

def load_data():
    print("=" * 60)
    print("LOADING DATA")
    print("=" * 60)

    jobs_df = pd.read_csv(INPUT_FILE)
    skills_df = pd.read_csv(SKILL_FILE)

    print(f"Jobs loaded   : {len(jobs_df)}")
    print(f"Skill records : {len(skills_df)}")

    return jobs_df, skills_df


# ============================================================
# MARKET KPI ANALYSIS
# ============================================================

def market_summary(df):
    total_jobs = len(df)

    companies = df["company"].nunique()

    locations = df["location"].nunique()

    avg_salary = df["salary_avg"].mean()

    median_salary = df["salary_avg"].median()

    min_salary = df["salary_avg"].min()

    max_salary = df["salary_avg"].max()

    summary = pd.DataFrame([
        {
            "metric": "Total Jobs",
            "value": total_jobs
        },
        {
            "metric": "Unique Companies",
            "value": companies
        },
        {
            "metric": "Unique Locations",
            "value": locations
        },
        {
            "metric": "Average Salary",
            "value": round(avg_salary, 2)
        },
        {
            "metric": "Median Salary",
            "value": round(median_salary, 2)
        },
        {
            "metric": "Minimum Salary",
            "value": round(min_salary, 2)
        },
        {
            "metric": "Maximum Salary",
            "value": round(max_salary, 2)
        }
    ])

    return summary


# ============================================================
# ROLE + SALARY ANALYSIS
# ============================================================

def role_salary_analysis(df):

    result = (
        df.groupby("job_title")
        .agg(
            job_count=("job_title", "count"),
            average_salary=("salary_avg", "mean"),
            minimum_salary=("salary_min", "min"),
            maximum_salary=("salary_max", "max")
        )
        .reset_index()
    )

    result["average_salary"] = result["average_salary"].round(2)

    return result.sort_values(
        by="average_salary",
        ascending=False
    )


# ============================================================
# LOCATION + SALARY ANALYSIS
# ============================================================

def location_salary_analysis(df):

    result = (
        df.groupby("location")
        .agg(
            job_count=("job_title", "count"),
            average_salary=("salary_avg", "mean"),
            minimum_salary=("salary_min", "min"),
            maximum_salary=("salary_max", "max")
        )
        .reset_index()
    )

    result["average_salary"] = result["average_salary"].round(2)

    return result.sort_values(
        by="average_salary",
        ascending=False
    )


# ============================================================
# EXPERIENCE + SALARY
# ============================================================

def experience_salary_analysis(df):

    result = (
        df.groupby("experience_required")
        .agg(
            job_count=("job_title", "count"),
            average_salary=("salary_avg", "mean"),
            minimum_salary=("salary_min", "min"),
            maximum_salary=("salary_max", "max")
        )
        .reset_index()
    )

    result["average_salary"] = result["average_salary"].round(2)

    return result.sort_values(
        by="average_salary",
        ascending=False
    )


# ============================================================
# SKILL + SALARY ANALYSIS
# ============================================================

def skill_salary_analysis(skills_df):

    result = (
        skills_df.groupby("skill")
        .agg(
            job_count=("job_id", "nunique"),
            average_salary=("salary_avg", "mean"),
            minimum_salary=("salary_avg", "min"),
            maximum_salary=("salary_avg", "max")
        )
        .reset_index()
    )

    total_jobs = skills_df["job_id"].nunique()

    result["demand_percentage"] = (
        result["job_count"] / total_jobs * 100
    ).round(2)

    result["average_salary"] = result["average_salary"].round(2)
    result["minimum_salary"] = result["minimum_salary"].round(2)
    result["maximum_salary"] = result["maximum_salary"].round(2)

    return result.sort_values(
        by="job_count",
        ascending=False
    )


# ============================================================
# SKILL COMBINATIONS
# ============================================================

def skill_combinations(skills_df):

    job_skills = (
        skills_df
        .groupby("job_id")["skill"]
        .apply(lambda x: sorted(set(x)))
    )

    records = []

    for job_id, skills in job_skills.items():

        if len(skills) < 2:
            continue

        for skill_a, skill_b in combinations(skills, 2):

            records.append({
                "job_id": job_id,
                "skill_1": skill_a,
                "skill_2": skill_b
            })

    if not records:
        return pd.DataFrame(
            columns=[
                "skill_1",
                "skill_2",
                "job_count"
            ]
        )

    combinations_df = pd.DataFrame(records)

    result = (
        combinations_df
        .groupby(["skill_1", "skill_2"])
        .agg(
            job_count=("job_id", "nunique")
        )
        .reset_index()
    )

    return result.sort_values(
        by="job_count",
        ascending=False
    )


# ============================================================
# TOP PAYING JOBS
# ============================================================

def top_paying_jobs(df):

    columns = [
        "job_title",
        "company",
        "location",
        "experience_required",
        "salary_avg"
    ]

    result = (
        df[columns]
        .sort_values(
            by="salary_avg",
            ascending=False
        )
        .head(10)
    )

    return result


# ============================================================
# SAVE OUTPUT
# ============================================================

def save_output(df, filename):

    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    output_path = OUTPUT_DIR / filename

    df.to_csv(
        output_path,
        index=False
    )

    print(f"Saved: {output_path}")


# ============================================================
# DISPLAY SECTION
# ============================================================

def display_section(title, df):

    print("\n" + "=" * 60)
    print(title)
    print("=" * 60)

    print(df.to_string(index=False))


# ============================================================
# MAIN
# ============================================================

def main():

    print("=" * 60)
    print("JOB MARKET ANALYTICS")
    print("STEP 7 - ADVANCED MARKET ANALYTICS")
    print("=" * 60)

    jobs_df, skills_df = load_data()

    # --------------------------------------------------------
    # 1. MARKET SUMMARY
    # --------------------------------------------------------

    summary = market_summary(jobs_df)

    display_section(
        "MARKET SUMMARY",
        summary
    )

    save_output(
        summary,
        "market_summary.csv"
    )

    # --------------------------------------------------------
    # 2. ROLE SALARY
    # --------------------------------------------------------

    role_salary = role_salary_analysis(jobs_df)

    display_section(
        "ROLE + SALARY ANALYSIS",
        role_salary
    )

    save_output(
        role_salary,
        "role_salary_analysis.csv"
    )

    # --------------------------------------------------------
    # 3. LOCATION SALARY
    # --------------------------------------------------------

    location_salary = location_salary_analysis(jobs_df)

    display_section(
        "LOCATION + SALARY ANALYSIS",
        location_salary
    )

    save_output(
        location_salary,
        "location_salary_analysis.csv"
    )

    # --------------------------------------------------------
    # 4. EXPERIENCE SALARY
    # --------------------------------------------------------

    experience_salary = experience_salary_analysis(
        jobs_df
    )

    display_section(
        "EXPERIENCE + SALARY ANALYSIS",
        experience_salary
    )

    save_output(
        experience_salary,
        "experience_salary.csv"
    )

    # --------------------------------------------------------
    # 5. SKILL SALARY
    # --------------------------------------------------------

    skill_salary = skill_salary_analysis(
        skills_df
    )

    display_section(
        "SKILL + SALARY ANALYSIS",
        skill_salary
    )

    save_output(
        skill_salary,
        "skill_salary_analysis.csv"
    )

    # --------------------------------------------------------
    # 6. SKILL COMBINATIONS
    # --------------------------------------------------------

    combinations_df = skill_combinations(
        skills_df
    )

    display_section(
        "TOP SKILL COMBINATIONS",
        combinations_df
    )

    save_output(
        combinations_df,
        "skill_combinations.csv"
    )

    # --------------------------------------------------------
    # 7. TOP PAYING JOBS
    # --------------------------------------------------------

    top_jobs = top_paying_jobs(
        jobs_df
    )

    display_section(
        "TOP PAYING JOBS",
        top_jobs
    )

    save_output(
        top_jobs,
        "top_paying_jobs.csv"
    )

    # --------------------------------------------------------
    # COMPLETE
    # --------------------------------------------------------

    print("\n" + "=" * 60)
    print("ADVANCED ANALYTICS COMPLETED SUCCESSFULLY")
    print("=" * 60)


if __name__ == "__main__":
    main()