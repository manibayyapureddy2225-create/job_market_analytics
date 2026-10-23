"""
Initialize the Job Market Analytics database.
"""

from pathlib import Path

from sqlalchemy import text

from src.database.db import get_engine

BASE_DIR = Path(__file__).resolve().parents[2]
SCHEMA_FILE = BASE_DIR / "sql" / "schema.sql"


def initialize_database():
    engine = get_engine()

    schema = SCHEMA_FILE.read_text(encoding="utf-8")

    with engine.begin() as connection:
        # SQLite executes statements individually
        for statement in schema.split(";"):
            statement = statement.strip()

            if statement:
                connection.execute(text(statement))

    print("Database initialized successfully.")


if __name__ == "__main__":
    initialize_database()