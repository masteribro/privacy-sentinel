import sqlite3
from pathlib import Path


def init_db(db_path: str = "data/privacy_sentinel.db") -> str:
    path = Path(db_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(path))
    cur = conn.cursor()

    cur.execute("PRAGMA foreign_keys = ON;")

    cur.execute("""
        CREATE TABLE IF NOT EXISTS applications (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            developer TEXT,
            category TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS labels (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            app_id INTEGER NOT NULL,
            platform TEXT NOT NULL,
            data_categories TEXT,
            data_types TEXT,
            tracking_disclosed TEXT,
            shares_data TEXT,
            data_deletion_option TEXT,
            raw JSON,
            FOREIGN KEY (app_id) REFERENCES applications(id) ON DELETE CASCADE
        );
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS scores (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            app_id INTEGER NOT NULL,
            overall REAL,
            completeness REAL,
            specificity REAL,
            consistency REAL,
            risk_flag TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (app_id) REFERENCES applications(id) ON DELETE CASCADE
        );
    """)

    _migrate(cur)
    conn.commit()
    conn.close()
    return str(path)


def _migrate(cur):
    _add_col(cur, "applications", "category", "TEXT")
    _add_col(cur, "applications", "created_at", "TIMESTAMP DEFAULT CURRENT_TIMESTAMP")
    _add_col(cur, "labels", "tracking_disclosed", "TEXT")
    _add_col(cur, "labels", "shares_data", "TEXT")
    _add_col(cur, "labels", "data_deletion_option", "TEXT")
    _add_col(cur, "scores", "risk_flag", "TEXT")
    _add_col(cur, "scores", "created_at", "TIMESTAMP DEFAULT CURRENT_TIMESTAMP")


def _add_col(cur, table, column, col_type):
    cur.execute(f"PRAGMA table_info({table})")
    existing = [row[1] for row in cur.fetchall()]
    if column not in existing:
        cur.execute(f"ALTER TABLE {table} ADD COLUMN {column} {col_type}")


if __name__ == "__main__":
    print(init_db())
