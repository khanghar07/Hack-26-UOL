"""Real Firebase Emulator sign-ins, isolated SQLite fixtures, API access checks."""
import os
import tempfile
import requests
from dotenv import load_dotenv

load_dotenv()
if os.getenv("FIREBASE_AUTH_EMULATOR_HOST") != "127.0.0.1:9099" or os.getenv("FIREBASE_PROJECT_ID") != "demo-novaworks":
    raise SystemExit("Use the local demo emulator and the README test command.")

from fastapi.testclient import TestClient
from main import app
from seed import seed
from directory import email_for, password_for
from storage import database

# Fixtures are used exclusively inside this temporary test database.
PROJECTS = [
    ("web", "UrbanCart Website", "UrbanCart Clothing", "Responsive demo store", "PM01", "2026-10-20"),
    ("mobile", "QuickServe Mobile App", "QuickServe Services", "Customer booking demo", "PM02", "2026-10-24"),
    ("ai", "HelpDeskPro AI Assistant", "HelpDeskPro Solutions", "FAQ support demo", "PM03", "2026-10-22"),
]
TASKS = [
    ("catalog", "web", "Product catalog UI", "Listing and detail screens", "DEV01", "2026-10-12", 12),
    ("cart", "web", "Demo cart UI", "Cart quantities and total", "DEV01", "2026-10-15", 8),
    ("web-api", "web", "Product and cart APIs", "Product data and demo endpoints", "DEV02", "2026-10-14", 14),
    ("web-test", "web", "Website integration and testing", "Connect screens and test", "DEV01", "2026-10-19", 6),
    ("login", "mobile", "Login and profile screens", "Customer account UI", "DEV03", "2026-10-12", 8),
    ("booking", "mobile", "Service booking screens", "Request and confirmation", "DEV03", "2026-10-17", 12),
    ("mobile-api", "mobile", "Booking and account APIs", "Accounts and booking status", "DEV02", "2026-10-16", 16),
    ("mobile-test", "mobile", "Mobile integration and testing", "Customer flow and errors", "DEV04", "2026-10-22", 10),
    ("faq", "ai", "FAQ document processing", "Prepare and retrieve FAQ", "DEV06", "2026-10-13", 10),
    ("answers", "ai", "Assistant answer generation", "Grounded answers", "DEV05", "2026-10-17", 14),
    ("escalation", "ai", "Human escalation flow", "Save unresolved questions", "DEV05", "2026-10-18", 6),
    ("ai-test", "ai", "Assistant evaluation and testing", "Answers and escalation", "DEV06", "2026-10-21", 8),
]
EXPECTED = {
    "admin": {"web": 4, "mobile": 4, "ai": 4},
    "ayesha": {"web": 4}, "bilal": {"mobile": 4}, "hina": {"ai": 4},
    "ali": {"web": 3}, "hamza": {"web": 1, "mobile": 1},
    "sara": {"mobile": 2}, "usman": {"mobile": 1}, "zain": {"ai": 2}, "maryam": {"ai": 2},
}

with tempfile.TemporaryDirectory() as folder:
    os.environ['DATABASE_URL'] = ''  # Always isolate regression fixtures from hosted data.
    os.environ["DATABASE_PATH"] = folder + "/test.sqlite3"
    seed()
    with TestClient(app) as client:
        headers_by_name = {}
        for name in EXPECTED:
            response = requests.post(
                "http://127.0.0.1:9099/identitytoolkit.googleapis.com/v1/accounts:signInWithPassword?key=demo",
                json={"email": email_for(name), "password":password_for(name), "returnSecureToken":True}, timeout=10)
            response.raise_for_status()
            headers_by_name[name] = {"Authorization":"Bearer "+response.json()["idToken"]}
        for header in headers_by_name.values():
            assert client.get("/api/projects", headers=header).json() == {"projects":[]}
        with database() as db:
            db.executemany("INSERT INTO projects VALUES(?,?,?,?,?,?)", PROJECTS)
            db.executemany("INSERT INTO tasks VALUES(?,?,?,?,?,?,?)", TASKS)
        for name, expected in EXPECTED.items():
            header = headers_by_name[name]
            me = client.get("/api/me", headers=header).json()
            response = client.get("/api/projects", headers=header)
            assert response.status_code == 200
            projects = response.json()["projects"]
            assert {p["id"]:p["taskCount"] for p in projects} == expected
            for project in projects:
                assert client.get("/api/projects/"+project["id"], headers=header).json() == project
                if me["role"] == "AGENT":
                    assert all(t["assigneeId"] == me["id"] for t in project["tasks"])
            for denied in {"web","mobile","ai","missing"} - set(expected):
                assert client.get("/api/projects/"+denied, headers=header).status_code == 404
            mine = client.get("/api/tasks/mine", headers=header)
            if me["role"] == "AGENT":
                tasks = mine.json()["tasks"]
                assert mine.status_code == 200 and len(tasks) == sum(expected.values())
                assert all(t["assigneeId"] == me["id"] for t in tasks)
                assert {t["projectId"] for t in tasks} == set(expected)
                assert [t["deadline"] for t in tasks] == sorted(t["deadline"] for t in tasks)
            else:
                assert mine.status_code == 403
        for path in ("/api/projects","/api/projects/web","/api/tasks/mine"):
            assert client.get(path).status_code == 401
            assert client.get(path, headers={"Authorization":"Bearer invalid"}).status_code == 401
        assert client.get("/api/projects/' OR 1=1 --", headers=headers_by_name["ali"]).status_code == 404
        assert len(client.get("/api/projects?role=ADMIN&userId=ADMIN", headers=headers_by_name["ali"]).json()["projects"]) == 1
    with TestClient(app) as restarted:
        assert len(restarted.get("/api/tasks/mine", headers=headers_by_name["hamza"]).json()["tasks"]) == 2
print("PASS: all 10 users, empty state, project lists/details/counts, task isolation, denied IDs, spoofed role, restart persistence.")
