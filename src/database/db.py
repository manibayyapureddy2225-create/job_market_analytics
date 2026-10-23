"""
Database connection module
Job Market Analytics Project
"""

from pathlib import Path

from sqlalchemy import create_engine


# Project root
BASE_DIR = Path(__file__).resolve().parents[2]

# Database location
DATABASE_DIR = BASE_DIR / "data"
DATABASE_PATH = DATABASE_DIR / "job_market.db"

# SQLite connection
DATABASE_URL = f"sqlite:///{DATABASE_PATH}"

engine = create_engine(
    DATABASE_URL,
    echo=False
)


def get_engine():
    """Return the SQLAlchemy database engine."""
    return engine