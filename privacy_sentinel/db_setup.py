import sqlite3
import json
from pathlib import Path


def init_db(db_path: str = "data/privacy_sentinel.db") -> str:
    path = Path(db_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(path))
    cur = conn.cursor()

    cur.execute("PRAGMA foreign_keys = ON;")

    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS applications (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            developer TEXT
        );
        """
    )

    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS labels (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            app_id INTEGER NOT NULL,
            platform TEXT NOT NULL,
            data_categories TEXT,
            data_types TEXT,
            raw JSON,
            FOREIGN KEY (app_id) REFERENCES applications(id) ON DELETE CASCADE
        );
        """
    )

    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS scores (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            app_id INTEGER NOT NULL,
            overall REAL,
            completeness REAL,
            specificity REAL,
            consistency REAL,
            FOREIGN KEY (app_id) REFERENCES applications(id) ON DELETE CASCADE
        );
        """
    )

    conn.commit()
    conn.close()
    return str(path)


if __name__ == "__main__":
    print(init_db())
