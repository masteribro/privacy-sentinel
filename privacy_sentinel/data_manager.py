import json
from typing import Optional


def insert_application(conn, name: str, developer: Optional[str] = None, category: Optional[str] = None) -> int:
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO applications (name, developer, category) VALUES (?, ?, ?)",
        (name, developer, category),
    )
    conn.commit()
    return cur.lastrowid


def insert_label(conn, app_id: int, platform: str,
                 data_categories: Optional[str] = None,
                 data_types: Optional[str] = None,
                 tracking_disclosed: Optional[str] = None,
                 shares_data: Optional[str] = None,
                 data_deletion_option: Optional[str] = None,
                 raw: Optional[dict] = None) -> int:
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO labels (app_id, platform, data_categories, data_types, "
        "tracking_disclosed, shares_data, data_deletion_option, raw) "
        "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
        (app_id, platform, data_categories, data_types,
         tracking_disclosed, shares_data, data_deletion_option, json.dumps(raw or {})),
    )
    conn.commit()
    return cur.lastrowid


def insert_scores(conn, app_id: int, scores: dict) -> int:
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO scores (app_id, overall, completeness, specificity, consistency, risk_flag) "
        "VALUES (?, ?, ?, ?, ?, ?)",
        (app_id, scores.get("overall"), scores.get("completeness"),
         scores.get("specificity"), scores.get("consistency"), scores.get("risk_flag")),
    )
    conn.commit()
    return cur.lastrowid


def get_labels_for_app(conn, app_id: int) -> dict:
    cur = conn.cursor()
    cur.execute(
        "SELECT platform, data_categories, data_types, tracking_disclosed, "
        "shares_data, data_deletion_option, raw FROM labels WHERE app_id = ?",
        (app_id,),
    )
    result = {}
    for platform, cats, types, tracking, shares, deletion, raw in cur.fetchall():
        result[platform] = {
            "data_categories": cats,
            "data_types": types,
            "tracking_disclosed": tracking,
            "shares_data": shares,
            "data_deletion_option": deletion,
            "raw": json.loads(raw) if raw else {},
        }
    return result


def get_all_apps(conn) -> list:
    cur = conn.cursor()
    cur.execute("""
        SELECT a.id, a.name, a.developer, a.category, a.created_at,
               s.overall, s.risk_flag
        FROM applications a
        LEFT JOIN scores s ON s.app_id = a.id
        ORDER BY a.created_at DESC
    """)
    apps = []
    for row in cur.fetchall():
        apps.append({
            "id": row[0],
            "name": row[1],
            "developer": row[2],
            "category": row[3],
            "created_at": row[4],
            "overall": row[5],
            "risk_flag": row[6],
        })
    return apps


def delete_app(conn, app_id: int):
    cur = conn.cursor()
    cur.execute("DELETE FROM applications WHERE id = ?", (app_id,))
    conn.commit()
