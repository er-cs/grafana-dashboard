import sqlite3
import json
import os

# ================= CONFIG =================
TARGET_DB_PATH = "C:\\grafana\\grafana-12.3.1\\data\\grafana.db"  # path to source Grafana SQLite DB
IMPORT_DIR = "grafana_export"  # copied folder from source machine
TABLES = ["folder", "library_element","library_element_connection", "dashboard", "dashboard_tag", "dashboard_version", "playlist", "playlist_item"]
# ==========================================

def import_table(conn, table, file_path):
    with open(file_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    if not data:
        print(f"[INFO] No data to import for table: {table}")
        return

    columns = list(data[0].keys())
    placeholders = ", ".join("?" * len(columns))
    cols = ", ".join(columns)
    values = [tuple(d[col] for col in columns) for d in data]

    cursor = conn.cursor()
    try:
        cursor.executemany(
            f"INSERT OR IGNORE INTO {table} ({cols}) VALUES ({placeholders})",
            values
        )
        conn.commit()
        print(f"[INFO] Imported {len(values)} rows into table: {table}")
    except Exception as e:
        print(f"[ERROR] Failed to import table {table}: {e}")

def main():
    if not os.path.exists(TARGET_DB_PATH):
        print(f"[ERROR] Target DB not found: {TARGET_DB_PATH}")
        return

    conn = sqlite3.connect(TARGET_DB_PATH)
    try:
        for table in TABLES:
            file_path = os.path.join(IMPORT_DIR, f"{table}.json")
            if os.path.exists(file_path):
                import_table(conn, table, file_path)
            else:
                print(f"[WARN] File not found for table {table}: {file_path}")
    finally:
        conn.close()
    print("[INFO] Import completed. Restart Grafana to see the changes.")

if __name__ == "__main__":
    main()
