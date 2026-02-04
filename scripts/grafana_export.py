import sqlite3
import json
import os

# ================= CONFIG =================
SOURCE_DB_PATH = "C:\\grafana\\grafana-12.3.1\\data\\grafana.db"  # path to source Grafana SQLite DB
EXPORT_DIR = "grafana_export"
TABLES = ["folder","data_source", "library_element","library_element_connection", "dashboard", "dashboard_tag", "dashboard_version", "playlist", "playlist_item"]
# ==========================================

os.makedirs(EXPORT_DIR, exist_ok=True)

def export_table(conn, table):
    cursor = conn.cursor()
    cursor.execute(f"SELECT * FROM {table}")
    rows = cursor.fetchall()
    columns = [desc[0] for desc in cursor.description]

    data = [dict(zip(columns, row)) for row in rows]
    file_path = os.path.join(EXPORT_DIR, f"{table}.json")
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
    print(f"[INFO] Exported {len(data)} rows from table: {table} -> {file_path}")

def main():
    if not os.path.exists(SOURCE_DB_PATH):
        print(f"[ERROR] Source DB not found: {SOURCE_DB_PATH}")
        return

    conn = sqlite3.connect(SOURCE_DB_PATH)
    try:
        for table in TABLES:
            export_table(conn, table)
    finally:
        conn.close()
    print("[INFO] Export completed. Copy the 'grafana_export' folder to the target machine.")

if __name__ == "__main__":
    main()
