import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).resolve().parents[2] / "data" / "job_market.db"

def initialize_tracker():
    connection = sqlite3.connect(DB_PATH)

    try:
        connection.execute("""
            CREATE TABLE IF NOT EXISTS job_applications (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                job_id INTEGER NOT NULL UNIQUE,
                status TEXT NOT NULL DEFAULT 'Saved'
                    CHECK (status IN (
                        'Saved', 'Applied', 'Interview',
                        'Rejected', 'Offer'
                    )),
                notes TEXT DEFAULT '',
                application_date TEXT,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (job_id) REFERENCES jobs(job_id)
                    ON DELETE CASCADE
            )
        """)

        connection.commit()
        print("Application tracker table created successfully.")

        result = connection.execute("""
            SELECT name
            FROM sqlite_master
            WHERE type = 'table'
              AND name = 'job_applications'
        """).fetchone()

        print("Verified table:", result[0])

    finally:
        connection.close()

if __name__ == "__main__":
    initialize_tracker()