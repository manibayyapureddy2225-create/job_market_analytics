
import csv
import logging
import re
import sqlite3
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DB_PATH = ROOT / "data" / "job_market.db"
SQL_PATH = ROOT / "sql" / "analytics.sql"
REPORTS_DIR = ROOT / "reports"

logging.basicConfig(
    level=logging.INFO,
    format="%(levelname)s: %(message)s",
)
log = logging.getLogger(__name__)


def split_queries(sql_text):
    """Split the analytics file at SQL semicolons outside quoted strings."""
    statements = []
    buffer = []
    single_quote = False
    double_quote = False
    i = 0

    while i < len(sql_text):
        char = sql_text[i]
        nxt = sql_text[i + 1] if i + 1 < len(sql_text) else ""

        # Skip SQL line comments.
        if not single_quote and not double_quote and char == "-" and nxt == "-":
            while i < len(sql_text) and sql_text[i] != "\n":
                i += 1
            continue

        if char == "'" and not double_quote:
            if single_quote and nxt == "'":
                buffer.extend([char, nxt])
                i += 2
                continue
            single_quote = not single_quote
        elif char == '"' and not single_quote:
            double_quote = not double_quote
        elif char == ";" and not single_quote and not double_quote:
            statement = "".join(buffer).strip()
            if statement:
                statements.append(statement)
            buffer = []
            i += 1
            continue

        buffer.append(char)
        i += 1

    remaining = "".join(buffer).strip()
    if remaining:
        statements.append(remaining)

    # Only execute read-only SELECT queries.
    return [
        query for query in statements
        if re.match(r"^(SELECT|WITH)\b", query, re.IGNORECASE)
    ]


def export_query(connection, query, output_file):
    cursor = connection.execute(query)
    headers = [column[0] for column in cursor.description]

    with output_file.open("w", newline="", encoding="utf-8-sig") as file:
        writer = csv.writer(file)
        writer.writerow(headers)
        writer.writerows(cursor.fetchall())

    return cursor.rowcount


def main():
    if not DB_PATH.exists():
        raise FileNotFoundError(f"Database not found: {DB_PATH}")
    if not SQL_PATH.exists():
        raise FileNotFoundError(f"SQL file not found: {SQL_PATH}")

    queries = split_queries(SQL_PATH.read_text(encoding="utf-8"))
    if not queries:
        raise RuntimeError("No SELECT queries found in analytics.sql")

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_dir = REPORTS_DIR / f"analytics_{timestamp}"
    output_dir.mkdir(parents=True, exist_ok=False)

    manifest = []
    failures = 0

    # Read-only connection protects the source database.
    uri = DB_PATH.resolve().as_uri() + "?mode=ro"
    with sqlite3.connect(uri, uri=True) as connection:
        connection.execute("PRAGMA query_only = ON")

        for number, query in enumerate(queries, start=1):
            output_name = f"query_{number:02d}.csv"
            output_path = output_dir / output_name

            try:
                cursor = connection.execute(query)
                headers = [column[0] for column in cursor.description]
                rows = cursor.fetchall()

                with output_path.open(
                    "w", newline="", encoding="utf-8-sig"
                ) as file:
                    writer = csv.writer(file)
                    writer.writerow(headers)
                    writer.writerows(rows)

                manifest.append({
                    "query": number,
                    "file": output_name,
                    "status": "success",
                    "rows": len(rows),
                    "error": "",
                })
                log.info("Exported %s (%d rows)", output_name, len(rows))

            except sqlite3.Error as error:
                failures += 1
                manifest.append({
                    "query": number,
                    "file": output_name,
                    "status": "failed",
                    "rows": 0,
                    "error": str(error),
                })
                log.error("Query %d failed: %s", number, error)

        # Generate a small summary directly from the database.
        summary_query = """
            SELECT
                COUNT(*) AS total_jobs,
                COUNT(DISTINCT company) AS unique_companies,
                COUNT(DISTINCT location) AS unique_locations,
                COUNT(DISTINCT source) AS job_sources,
                SUM(CASE WHEN salary_avg IS NOT NULL THEN 1 ELSE 0 END)
                    AS jobs_with_salary
            FROM jobs
        """
        summary_cursor = connection.execute(summary_query)
        summary_headers = [column[0] for column in summary_cursor.description]
        summary_row = summary_cursor.fetchone()

        with (output_dir / "market_summary.csv").open(
            "w", newline="", encoding="utf-8-sig"
        ) as file:
            writer = csv.writer(file)
            writer.writerow(summary_headers)
            writer.writerow(summary_row)

    with (output_dir / "export_manifest.csv").open(
        "w", newline="", encoding="utf-8-sig"
    ) as file:
        writer = csv.DictWriter(
            file,
            fieldnames=["query", "file", "status", "rows", "error"],
        )
        writer.writeheader()
        writer.writerows(manifest)

    log.info("Reports saved to: %s", output_dir)
    log.info("Successful queries: %d", len(queries) - failures)
    log.info("Failed queries: %d", failures)

    if failures:
        raise RuntimeError(
            f"{failures} analytics queries failed. Check export_manifest.csv."
        )


if __name__ == "__main__":
    main()
