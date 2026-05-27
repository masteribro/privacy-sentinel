import sqlite3
import json
from typing import Optional


def insert_application(conn: sqlite3.Connection, name: str, developer: Optional[str] = None) -> int:
    cur = conn.cursor()
    cur.execute("INSERT INTO applications (name, developer) VALUES (?, ?)", (name, developer))
    conn.commit()
    return cur.lastrowid


def insert_label(conn: sqlite3.Connection, app_id: int, platform: str, data_categories: Optional[str], data_types: Optional[str], raw: Optional[dict] = None) -> int:
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO labels (app_id, platform, data_categories, data_types, raw) VALUES (?, ?, ?, ?, ?)",
        (app_id, platform, data_categories, data_types, json.dumps(raw or {})),
    )
    conn.commit()
    return cur.lastrowid


def get_labels_for_app(conn: sqlite3.Connection, app_id: int):
    cur = conn.cursor()
    cur.execute("SELECT platform, data_categories, data_types, raw FROM labels WHERE app_id = ?", (app_id,))
    rows = cur.fetchall()
    result = {}
    for platform, cats, types, raw in rows:
        try:
            parsed = json.loads(raw) if raw else {}
        except Exception:
            parsed = {}
        result[platform] = {"data_categories": cats, "data_types": types, "raw": parsed}
    return result
