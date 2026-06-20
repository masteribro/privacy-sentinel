import sqlite3
from pathlib import Path


DEFAULT_EMAIL = "admin@sentinel.com"
DEFAULT_PASSWORD = "sentinel123"


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

    cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            email TEXT NOT NULL UNIQUE,
            password_hash TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """)

    _migrate(cur)
    _seed_default_user(cur)
    conn.commit()
    conn.close()
    return str(path)


def _seed_default_user(cur):
    # only inserts the default account on a brand-new database, so a fresh clone is usable
    # immediately — once real accounts exist this never touches the users table again
    cur.execute("SELECT COUNT(*) FROM users")
    if cur.fetchone()[0] == 0:
        from privacy_sentinel.auth import hash_password
        cur.execute(
            "INSERT INTO users (email, password_hash) VALUES (?, ?)",
            (DEFAULT_EMAIL, hash_password(DEFAULT_PASSWORD)),
        )


def _migrate(cur):
    # lets an older database (e.g. from before the users table existed) catch up to the
    # current schema without wiping anything — each column only gets added if it's missing
    _add_col(cur, "applications", "category", "TEXT")
    _add_col(cur, "applications", "created_at", "TIMESTAMP DEFAULT CURRENT_TIMESTAMP")
    _add_col(cur, "labels", "tracking_disclosed", "TEXT")
    _add_col(cur, "labels", "shares_data", "TEXT")
    _add_col(cur, "labels", "data_deletion_option", "TEXT")
    _add_col(cur, "scores", "risk_flag", "TEXT")
    _add_col(cur, "scores", "created_at", "TIMESTAMP DEFAULT CURRENT_TIMESTAMP")
    _add_col(cur, "users", "name", "TEXT")


def _add_col(cur, table, column, col_type):
    cur.execute(f"PRAGMA table_info({table})")
    existing = [row[1] for row in cur.fetchall()]
    if column not in existing:
        cur.execute(f"ALTER TABLE {table} ADD COLUMN {column} {col_type}")


if __name__ == "__main__":
    print(init_db())
