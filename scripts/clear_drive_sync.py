import sqlite3
import os
import sys
from pathlib import Path
import logging
logger = logging.getLogger(__name__)

PROJECT_ROOT = Path(__file__).resolve().parent.parent

def clear_sync():
    db_path = PROJECT_ROOT / "data" / "drive_sync.db"
    if not db_path.exists():
        print(f"Sync DB not found: {db_path}")
        return

    print(f"Database: {db_path}")
    confirm = input("This will DELETE all sync history. Type 'yes' to confirm: ").strip().lower()
    if confirm != "yes":
        print("Cancelled.")
        return

    conn = None
    try:
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM synced_files")
        count = cursor.fetchone()[0]
        print(f"Found {count} synced file records.")
        cursor.execute("DELETE FROM synced_files")
        conn.commit()
        print("Drive sync history cleared.")
    except sqlite3.OperationalError as e:
        print(f"Database error: {e}")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    clear_sync()
