"""
Creates the Vendor Agreement SQLite database in the mockup_db folder
using the DDL defined in vendor_agreement_schema.sql.
"""

import logging
import sqlite3
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
SCHEMA_FILE = BASE_DIR / "vendor_agreement_schema.sql"
DB_FILE = BASE_DIR / "vendor_agreement.db"

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)


def create_database(db_file: Path = DB_FILE, schema_file: Path = SCHEMA_FILE) -> None:
    """Create the SQLite database file and apply the DDL schema."""
    schema_sql = schema_file.read_text(encoding="utf-8")

    conn = sqlite3.connect(db_file)
    try:
        conn.executescript(schema_sql)
        conn.commit()
    finally:
        conn.close()

    logger.info("Database created at: %s", db_file)


def list_tables(db_file: Path = DB_FILE) -> None:
    """Print the tables that exist in the database (sanity check)."""
    conn = sqlite3.connect(db_file)
    try:
        cursor = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name;"
        )
        tables = [row[0] for row in cursor.fetchall()]
    finally:
        conn.close()

    logger.info("Tables in database:")
    for table in tables:
        logger.info("  - %s", table)


if __name__ == "__main__":
    create_database()
    list_tables()
