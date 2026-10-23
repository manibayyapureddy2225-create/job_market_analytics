import sqlite3
import pandas as pd
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parents[2]

DB_PATH = BASE_DIR / "data" / "job_market.db"
SKILLS_FILE = BASE_DIR / "data" / "processed" / "job_skills.csv"


def load_skills():

    print("=" * 60)
    print("JOB SKILLS LOADER")
    print("=" * 60)

    if not SKILLS_FILE.exists():
        print(f"ERROR: Skill file not found: {SKILLS_FILE}")
        return

    df = pd.read_csv(SKILLS_FILE)

    print(f"Skill records found: {len(df)}")

    required_columns = {
        "job_id",
        "skill"
    }

    missing = required_columns - set(df.columns)

    if missing:
        print(f"ERROR: Missing columns: {missing}")
        return

    df = df[
        ["job_id", "skill"]
    ].copy()

    df["job_id"] = pd.to_numeric(
        df["job_id"],
        errors="coerce"
    )

    df["skill"] = (
        df["skill"]
        .astype(str)
        .str.strip()
    )

    df = df.dropna(subset=["job_id"])

    df = df[
        df["skill"].notna()
        & (df["skill"] != "")
        & (df["skill"].str.lower() != "nan")
    ]

    df["job_id"] = df["job_id"].astype(int)

    df = df.drop_duplicates(
        subset=["job_id", "skill"]
    )

    connection = sqlite3.connect(DB_PATH)

    # Make sure the table exists
    connection.execute("""
        CREATE TABLE IF NOT EXISTS job_skills (
            skill_id INTEGER PRIMARY KEY AUTOINCREMENT,
            job_id INTEGER NOT NULL,
            skill TEXT NOT NULL,
            FOREIGN KEY (job_id)
                REFERENCES jobs(job_id),
            UNIQUE(job_id, skill)
        )
    """)

    inserted = 0
    skipped = 0

    for _, row in df.iterrows():

        try:

            connection.execute(
                """
                INSERT INTO job_skills
                (job_id, skill)
                VALUES (?, ?)
                """,
                (
                    int(row["job_id"]),
                    row["skill"]
                )
            )

            inserted += 1

        except sqlite3.IntegrityError:

            skipped += 1

    connection.commit()

    total = connection.execute(
        "SELECT COUNT(*) FROM job_skills"
    ).fetchone()[0]

    unique_skills = connection.execute(
        "SELECT COUNT(DISTINCT skill) FROM job_skills"
    ).fetchone()[0]

    jobs_with_skills = connection.execute(
        "SELECT COUNT(DISTINCT job_id) FROM job_skills"
    ).fetchone()[0]

    connection.close()

    print()
    print("RESULT")
    print("-" * 60)
    print(f"Inserted records : {inserted}")
    print(f"Skipped records  : {skipped}")
    print(f"Total skill rows : {total}")
    print(f"Unique skills    : {unique_skills}")
    print(f"Jobs with skills : {jobs_with_skills}")
    print("=" * 60)


if __name__ == "__main__":
    load_skills()