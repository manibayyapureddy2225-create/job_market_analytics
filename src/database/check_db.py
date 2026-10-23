import sqlite3

database_path = "data/job_market.db"

db = sqlite3.connect(database_path)

tables = db.execute(
    "SELECT name FROM sqlite_master WHERE type='table'"
).fetchall()

print("Database:", database_path)
print("Tables:", tables)

db.close()