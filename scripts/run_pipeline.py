
from pathlib import Path
import subprocess
import sys
import logging

ROOT = Path(__file__).resolve().parents[1]
PYTHON = sys.executable

logging.basicConfig(
    level=logging.INFO,
    format="%(levelname)s: %(message)s"
)


def run_step(name, script):
    script_path = ROOT / "scripts" / script

    if not script_path.exists():
        raise FileNotFoundError(f"Script not found: {script_path}")

    logging.info("Starting: %s", name)

    result = subprocess.run(
        [PYTHON, str(script_path)],
        cwd=ROOT,
        check=False,
    )

    if result.returncode != 0:
        raise RuntimeError(
            f"{name} failed with exit code {result.returncode}"
        )

    logging.info("Completed: %s", name)


def main():
    run_step("SQL analytics CSV export", "export_analytics.py")
    run_step("HTML report generation", "generate_report.py")
    logging.info("SUCCESS: Complete analytics pipeline finished.")


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        logging.error("Pipeline failed: %s", exc)
        sys.exit(1)
