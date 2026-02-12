import sqlite3
import os
import logging
logger = logging.getLogger(__name__)

def clear_sync():
    db_path = "data/drive_sync.db"
    if not os.path.exists(db_path):
        print(f"Sync DB not found: {db_path}")
        return

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM synced_files")
    conn.commit()
    conn.close()
    print("Drive sync history cleared.")

if __name__ == "__main__":
    clear_sync()
