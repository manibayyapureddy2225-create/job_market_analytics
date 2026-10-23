"""
Job Market Analytics
Step 6 - Skill Extraction Engine

Extracts technical and analytical skills from job titles,
job descriptions, and existing skill fields.
"""

from pathlib import Path
import re
import pandas as pd


# ---------------------------------------------------------
# PROJECT PATHS
# ---------------------------------------------------------

BASE_DIR = Path(__file__).resolve().parents[2]

INPUT_FILE = BASE_DIR / "data" / "processed" / "jobs_cleaned.csv"

OUTPUT_DIR = BASE_DIR / "data" / "processed"

SKILL_OUTPUT_FILE = OUTPUT_DIR / "job_skills.csv"
SKILL_SUMMARY_FILE = OUTPUT_DIR / "skill_demand.csv"


# ---------------------------------------------------------
# SKILL DICTIONARY
# ---------------------------------------------------------

SKILL_PATTERNS = {

    # Programming
    "Python": [r"\bpython\b"],
    "Java": [r"\bjava\b"],
    "JavaScript": [r"\bjavascript\b"],
    "TypeScript": [r"\btypescript\b"],
    "C++": [r"\bc\+\+\b"],
    "C#": [r"\bc#\b"],

    # Data
    "SQL": [r"\bsql\b"],
    "Pandas": [r"\bpandas\b"],
    "NumPy": [r"\bnumpy\b"],
    "Excel": [r"\bexcel\b"],
    "Power BI": [r"\bpower\s*bi\b"],
    "Tableau": [r"\btableau\b"],

    # Data Science / AI
    "Machine Learning": [
        r"\bmachine learning\b",
        r"\bml\b"
    ],
    "Deep Learning": [
        r"\bdeep learning\b"
    ],
    "NLP": [
        r"\bnlp\b",
        r"\bnatural language processing\b"
    ],

    # Backend / Web
    "FastAPI": [r"\bfastapi\b"],
    "Flask": [r"\bflask\b"],
    "Django": [r"\bdjango\b"],
    "REST API": [
        r"\brest api\b",
        r"\brestful api\b",
        r"\brestful\b"
    ],
    "React": [r"\breact(?:\.js)?\b"],
    "Vue.js": [r"\bvue(?:\.js)?\b"],
    "Node.js": [r"\bnode(?:\.js)?\b"],

    # Java ecosystem
    "Spring Boot": [r"\bspring boot\b"],
    "Maven": [r"\bmaven\b"],

    # Cloud
    "AWS": [r"\baws\b", r"\bamazon web services\b"],
    "Azure": [r"\bazure\b"],
    "Google Cloud": [
        r"\bgoogle cloud\b",
        r"\bgcp\b"
    ],

    # DevOps
    "Docker": [r"\bdocker\b"],
    "Kubernetes": [r"\bkubernetes\b", r"\bk8s\b"],
    "Git": [r"\bgit\b"],
    "CI/CD": [
        r"\bci/cd\b",
        r"\bcontinuous integration\b",
        r"\bcontinuous deployment\b"
    ],

    # Databases
    "MySQL": [r"\bmysql\b"],
    "PostgreSQL": [r"\bpostgresql\b", r"\bpostgres\b"],
    "MongoDB": [r"\bmongodb\b"],
    "SQLite": [r"\bsqlite\b"],

    # Analytics
    "Data Visualization": [
        r"\bdata visualization\b",
        r"\bdata visualisation\b",
        r"\bvisualization\b",
        r"\bvisualisation\b"
    ],
    "Statistics": [
        r"\bstatistics\b",
        r"\bstatistical\b"
    ],

    # General
    "Jupyter": [r"\bjupyter\b"],
}


# ---------------------------------------------------------
# NORMALIZE TEXT
# ---------------------------------------------------------

def normalize_text(value):
    """Normalize text for skill matching."""

    if pd.isna(value):
        return ""

    text = str(value).lower()

    # Normalize common separators
    text = text.replace("-", " ")
    text = re.sub(r"\s+", " ", text)

    return text


# ---------------------------------------------------------
# EXTRACT SKILLS
# ---------------------------------------------------------

def extract_skills(text):
    """
    Return all skills detected in the supplied text.
    """

    text = normalize_text(text)

    detected_skills = []

    for skill, patterns in SKILL_PATTERNS.items():

        for pattern in patterns:

            if re.search(pattern, text, flags=re.IGNORECASE):

                detected_skills.append(skill)

                break

    return detected_skills


# ---------------------------------------------------------
# BUILD SEARCH TEXT
# ---------------------------------------------------------

def build_search_text(row):
    """
    Combine job title, description and existing skills.
    """

    title = row.get("job_title", "")
    description = row.get("job_description", "")
    existing_skills = row.get("skills", "")

    return " ".join(
        [
            normalize_text(title),
            normalize_text(description),
            normalize_text(existing_skills)
        ]
    )


# ---------------------------------------------------------
# EXTRACT JOB SKILLS
# ---------------------------------------------------------

def extract_job_skills(df):
    """Extract skills for every job."""

    df["extracted_skills"] = df.apply(
        lambda row: extract_skills(
            build_search_text(row)
        ),
        axis=1
    )

    return df


# ---------------------------------------------------------
# CREATE SKILL RECORDS
# ---------------------------------------------------------

def create_skill_records(df):
    """
    Convert each job's skill list into one row per skill.
    """

    records = []

    for _, row in df.iterrows():

        skills = row["extracted_skills"]

        for skill in skills:

            records.append(
                {
                    "job_id": row.name + 1,
                    "job_title": row["job_title"],
                    "company": row["company"],
                    "location": row["location"],
                    "salary_avg": row["salary_avg"],
                    "skill": skill
                }
            )

    return pd.DataFrame(records)


# ---------------------------------------------------------
# SKILL DEMAND SUMMARY
# ---------------------------------------------------------

def create_skill_summary(skill_df, total_jobs):
    """Calculate skill demand statistics."""

    if skill_df.empty:

        return pd.DataFrame(
            columns=[
                "skill",
                "job_count",
                "demand_percentage",
                "average_salary"
            ]
        )

    summary = (
        skill_df
        .groupby("skill")
        .agg(
            job_count=("job_title", "count"),
            average_salary=("salary_avg", "mean")
        )
        .reset_index()
    )

    # A job may contain the same skill only once,
    # so job_count represents jobs containing the skill.
    summary["demand_percentage"] = (
        summary["job_count"] / total_jobs * 100
    ).round(2)

    summary["average_salary"] = (
        summary["average_salary"]
        .round(2)
    )

    summary = summary.sort_values(
        by="job_count",
        ascending=False
    )

    return summary


# ---------------------------------------------------------
# SAVE RESULTS
# ---------------------------------------------------------

def save_results(df, skill_df, summary):
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # Save one row per job-skill relationship
    skill_df.to_csv(SKILL_OUTPUT_FILE, index=False)

    # Save aggregated skill demand
    summary.to_csv(SKILL_SUMMARY_FILE, index=False)

    print(f"\nSaved job skill data:")
    print(SKILL_OUTPUT_FILE)

    print(f"\nSaved skill demand summary:")
    print(SKILL_SUMMARY_FILE)

# ---------------------------------------------------------
# DISPLAY RESULTS
# ---------------------------------------------------------

def display_results(skill_df, summary):

    print("\n" + "=" * 60)
    print("EXTRACTED SKILLS")
    print("=" * 60)

    if skill_df.empty:

        print("No skills detected.")

    else:

        print(
            skill_df[
                [
                    "job_title",
                    "skill",
                    "salary_avg"
                ]
            ].to_string(index=False)
        )

    print("\n" + "=" * 60)
    print("SKILL DEMAND SUMMARY")
    print("=" * 60)

    if summary.empty:

        print("No skill summary available.")

    else:

        print(
            summary.to_string(index=False)
        )


# ---------------------------------------------------------
# MAIN
# ---------------------------------------------------------

def main():

    print("=" * 60)
    print("JOB MARKET ANALYTICS - SKILL EXTRACTION")
    print("=" * 60)

    # Load cleaned jobs
    df = pd.read_csv(INPUT_FILE)

    print(f"Jobs loaded: {len(df)}")

    # Extract skills
    df = extract_job_skills(df)

    # Create normalized skill table
    skill_df = create_skill_records(df)

    # Calculate demand
    summary = create_skill_summary(
        skill_df,
        len(df)
    )

    # Save
    save_results(
        df,
        skill_df,
        summary
    )

    # Display
    display_results(
        skill_df,
        summary
    )

    print("\n" + "=" * 60)
    print("SKILL EXTRACTION COMPLETED SUCCESSFULLY")
    print("=" * 60)


if __name__ == "__main__":
    main()