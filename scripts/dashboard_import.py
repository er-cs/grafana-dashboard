import json
import os
import requests
import sys

sys.stdout.reconfigure(encoding='utf-8')


# ================= CONFIG =================
GRAFANA_URL = "http://localhost:3000"
API_TOKEN = os.environ["GRAFANA_API_KEY"]
DASHBOARD_DIR = DASHBOARD_DIR = os.path.join(os.path.dirname(__file__), "..", "dashboards")   # folder containing *.json files
FOLDER_ID = None                 # set to an int if you want a specific folder
OVERWRITE = True
TIMEOUT = 30
# ==========================================

HEADERS = {
    "Authorization": f"Bearer {API_TOKEN}",
    "Content-Type": "application/json",
}


def patch_dashboard(dashboard: dict) -> dict:
    # REQUIRED for API imports
    dashboard["id"] = None
    dashboard.setdefault("uid", dashboard.get("uid"))  # KEEP UID

    # Force Grafana to treat this as a brand-new dashboard
    dashboard["version"] = 0
    dashboard.pop("iteration", None)

    # Force dashboard-level refresh & render
    dashboard["refresh"] = "30s"
    dashboard["liveNow"] = False
    dashboard["time"] = dashboard.get("time", {"from": "now-6h", "to": "now"})

    # Remove cached panel state that breaks first render
    for panel in dashboard.get("panels", []):
        panel.pop("scopedVars", None)
        panel.pop("transformations", None)

        # FORCE query execution
        for target in panel.get("targets", []):
            target.setdefault("refId", "A")

        # IMPORTANT: let panel inherit dashboard datasource
        if isinstance(panel.get("datasource"), dict):
            panel["datasource"].pop("uid", None)

    # Force variable execution on load
    templating = dashboard.get("templating", {})
    for var in templating.get("list", []):
        if var.get("type") == "query":
            var["refresh"] = 1
            var.pop("current", None)

    # Remove inputs/requires (breaks API imports in 12.x)
    dashboard.pop("__inputs", None)
    dashboard.pop("__requires", None)

    # Annotations must exist
    dashboard.setdefault(
        "annotations",
        {"list": [{"builtIn": 1, "datasource": "DS_INFLUXDB-1", "enable": True, "hide": True, "iconColor": "rgba(0, 211, 255, 1)", "name": "Annotations", "type": "dashboard"}]},
    )

    return dashboard




def import_dashboard(file_path: str) -> bool:
    with open(file_path, "r", encoding="utf-8") as f:
        dashboard = json.load(f)

    dashboard = patch_dashboard(dashboard)

    payload = {
        "dashboard": dashboard,
        "overwrite": OVERWRITE,
    }

    if FOLDER_ID is not None:
        payload["folderId"] = FOLDER_ID

    response = requests.post(
        f"{GRAFANA_URL}/api/dashboards/db",
        headers=HEADERS,
        json=payload,
        timeout=TIMEOUT,
    )

    if response.status_code == 200:
        title = dashboard.get("title", os.path.basename(file_path))
        print(f"Imported: {title}")
        return True
    else:
        print(f"Failed: {file_path}")
        print(f"   {response.status_code}: {response.text}")
        return False


def main():
    if not os.path.isdir(DASHBOARD_DIR):
        raise FileNotFoundError(f"Dashboard dir not found: {DASHBOARD_DIR}")

    files = sorted(
        f for f in os.listdir(DASHBOARD_DIR)
        if f.lower().endswith(".json")
    )

    if not files:
        print("No dashboard JSON files found.")
        return

    print(f"Found {len(files)} dashboard(s)")

    success = 0
    for filename in files:
        path = os.path.join(DASHBOARD_DIR, filename)
        if import_dashboard(path):
            success += 1

    print(f"\nDone: {success}/{len(files)} dashboards imported")


if __name__ == "__main__":
    main()
