
from pathlib import Path
import pandas as pd

DATA_PATH = Path("data/processed/jobs_cleaned.csv")

def main():
    df = pd.read_csv(DATA_PATH)

    print("=" * 60)
    print("JOB MARKET ANALYTICS — SALARY DATA AUDIT")
    print("=" * 60)

    print(f"\nTotal job records: {len(df)}")

    salary_cols = [
        "salary_min",
        "salary_max",
        "salary_avg",
        "salary_currency",
    ]

    print("\nMissing values:")
    print(df[salary_cols].isna().sum().to_string())

    print("\nCurrency distribution:")
    print(
        df["salary_currency"]
        .fillna("UNKNOWN")
        .value_counts()
        .to_string()
    )

    print("\nSalary records by currency:")
    salary_data = df[df["salary_avg"].notna()]

    print(
        salary_data.groupby("salary_currency", dropna=False)
        .agg(
            jobs_with_salary=("salary_avg", "count"),
            minimum=("salary_avg", "min"),
            median=("salary_avg", "median"),
            maximum=("salary_avg", "max"),
        )
        .round(2)
        .to_string()
    )

    print("\nPotentially unusual salary values:")
    columns = [
        "job_title",
        "salary_min",
        "salary_max",
        "salary_avg",
        "salary_currency",
    ]

    print(
        salary_data[
            salary_data["salary_avg"] < 1000
        ][columns].to_string(index=False)
    )

    print("\nAudit complete. Original data was not modified.")

if __name__ == "__main__":
    main()
