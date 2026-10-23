
from pathlib import Path
from datetime import datetime
import csv
import html
import logging

ROOT = Path(__file__).resolve().parents[1]
REPORTS_DIR = ROOT / "reports"

logging.basicConfig(
    level=logging.INFO,
    format="%(levelname)s: %(message)s"
)


def read_csv(path):
    if not path.exists():
        return []
    with path.open("r", newline="", encoding="utf-8-sig") as file:
        return list(csv.DictReader(file))


def safe(value):
    return html.escape(str(value if value is not None else ""))


def make_table(rows, max_rows=50):
    if not rows:
        return "<p class='muted'>No data available.</p>"

    columns = list(rows[0].keys())
    header = "".join(f"<th>{safe(col)}</th>" for col in columns)

    body = ""
    for row in rows[:max_rows]:
        body += "<tr>" + "".join(
            f"<td>{safe(row.get(col, ''))}</td>" for col in columns
        ) + "</tr>"

    note = ""
    if len(rows) > max_rows:
        note = f"<p class='muted'>Showing {max_rows} of {len(rows)} rows.</p>"

    return (
        "<div class='table-wrap'><table><thead><tr>"
        + header
        + "</tr></thead><tbody>"
        + body
        + "</tbody></table></div>"
        + note
    )


def main():
    # Use the most recent timestamped analytics export folder.
    folders = sorted(
        [p for p in REPORTS_DIR.glob("analytics_*") if p.is_dir()],
        key=lambda p: p.stat().st_mtime,
        reverse=True,
    )

    if not folders:
        raise FileNotFoundError(
            "No analytics export folders found. Run export_analytics.py first."
        )

    export_dir = folders[0]
    summary_rows = read_csv(export_dir / "market_summary.csv")
    manifest_rows = read_csv(export_dir / "export_manifest.csv")

    # Read each exported query result.
    query_files = sorted(
        export_dir.glob("query_*.csv"),
        key=lambda p: p.name,
    )

    query_sections = []
    for path in query_files:
        rows = read_csv(path)
        query_sections.append(
            f"<section><h2>{safe(path.stem.replace('_', ' ').title())}</h2>"
            f"<p class='muted'>{len(rows)} rows</p>"
            f"{make_table(rows)}</section>"
        )

    # Read summary metrics as key-value pairs when possible.
    summary_html = make_table(summary_rows)
    manifest_success = sum(
        1 for row in manifest_rows
        if row.get("status", "").strip().upper() in {"SUCCESS", "OK"}
    )
    manifest_failed = sum(
        1 for row in manifest_rows
        if row.get("status", "").strip().upper() in {"FAILED", "ERROR"}
    )

    generated_at = datetime.now().astimezone().strftime("%d %b %Y, %I:%M %p %Z")
    output_path = REPORTS_DIR / f"job_market_report_{datetime.now():%Y%m%d_%H%M%S}.html"

    document = f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Job Market Analytics Report</title>
<style>
:root {{
  color-scheme: light;
  --ink: #172033;
  --muted: #667085;
  --line: #e4e7ec;
  --panel: #ffffff;
  --page: #f5f7fb;
  --accent: #315efb;
}}
* {{ box-sizing: border-box; }}
body {{
  margin: 0; background: var(--page); color: var(--ink);
  font: 15px/1.55 Arial, sans-serif;
}}
header {{
  padding: 34px max(20px, calc((100vw - 1100px)/2));
  background: #14213d; color: white;
}}
header p {{ color: #d0d7e7; margin-bottom: 0; }}
main {{ max-width: 1100px; margin: 26px auto; padding: 0 18px 50px; }}
section {{
  background: var(--panel); border: 1px solid var(--line);
  border-radius: 12px; padding: 20px; margin: 18px 0;
}}
h1 {{ margin: 0; font-size: clamp(26px, 4vw, 38px); }}
h2 {{ margin-top: 0; font-size: 21px; }}
.muted {{ color: var(--muted); font-size: 13px; }}
.cards {{
  display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
  gap: 12px; margin: 18px 0;
}}
.card {{
  background: white; border: 1px solid var(--line);
  border-radius: 12px; padding: 18px;
}}
.card strong {{ display: block; font-size: 25px; overflow-wrap: anywhere; }}
.card span {{ color: var(--muted); font-size: 13px; }}
.table-wrap {{ overflow-x: auto; }}
table {{ width: 100%; border-collapse: collapse; font-size: 13px; }}
th, td {{
  text-align: left; padding: 9px 11px;
  border-bottom: 1px solid var(--line); vertical-align: top;
}}
th {{ background: #f0f3fa; white-space: nowrap; }}
tr:last-child td {{ border-bottom: 0; }}
footer {{ text-align: center; color: var(--muted); padding: 20px; }}
@media print {{
  body {{ background: white; }}
  section, .card {{ break-inside: avoid; }}
  header {{ background: #14213d !important; print-color-adjust: exact; }}
}}
</style>
</head>
<body>
<header>
  <h1>Job Market Analytics</h1>
  <p>Automated analytics report · Generated {safe(generated_at)}</p>
  <p>Data source: {safe(export_dir.name)}</p>
</header>
<main>
  <section>
    <h2>Executive Summary</h2>
    <p>This report compiles the latest exported SQL analytics. Review salary
    results carefully: different currencies and salary periods should not be
    compared directly unless normalized.</p>
    <div class="cards">
      <div class="card"><strong>{len(query_files)}</strong><span>Query CSV files</span></div>
      <div class="card"><strong>{manifest_success}</strong><span>Manifest successful rows</span></div>
      <div class="card"><strong>{manifest_failed}</strong><span>Manifest failed rows</span></div>
    </div>
  </section>
  <section>
    <h2>Market Summary</h2>
    {summary_html}
  </section>
  {''.join(query_sections)}
  <footer>Job Market Analytics · Generated locally from CSV exports</footer>
</main>
</body>
</html>
"""

    output_path.write_text(document, encoding="utf-8")
    logging.info("Report created: %s", output_path)
    logging.info("Source export folder: %s", export_dir)
    logging.info("Query CSV files included: %d", len(query_files))
    logging.info("Open the HTML file in your browser to view or print as PDF.")


if __name__ == "__main__":
    main()
