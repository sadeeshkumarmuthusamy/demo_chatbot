"""
Exports every table in vendor_agreement.db to a CSV file under
mockup_db/csv_exports/ for manual verification.
"""
import csv
import sqlite3
from pathlib import Path

from DB_schema import DB_FILE

BASE_DIR = Path(__file__).resolve().parent
OUT_DIR = BASE_DIR / "csv_exports"


def export_all_tables(db_file: Path = DB_FILE, out_dir: Path = OUT_DIR) -> None:
    out_dir.mkdir(exist_ok=True)
    conn = sqlite3.connect(db_file)
    try:
        tables = [
            row[0]
            for row in conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
            ).fetchall()
        ]
        for table in tables:
            cursor = conn.execute(f"SELECT * FROM {table}")
            columns = [d[0] for d in cursor.description]
            rows = cursor.fetchall()
            csv_path = out_dir / f"{table}.csv"
            with open(csv_path, "w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow(columns)
                writer.writerows(rows)
            print(f"{table}: {len(rows)} rows -> {csv_path.relative_to(BASE_DIR)}")
    finally:
        conn.close()


if __name__ == "__main__":
    export_all_tables()
