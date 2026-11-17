"""Run inside firebase emulators:exec. Uses a temporary SQLite database."""
import os
from dotenv import load_dotenv
load_dotenv()
if os.getenv("FIREBASE_AUTH_EMULATOR_HOST") != "127.0.0.1:9099" or os.getenv("FIREBASE_PROJECT_ID") != "demo-novaworks":
    raise SystemExit("Use the local demo emulator and the README test command.")
import tempfile
import requests
from fastapi.testclient import TestClient
from directory import PEOPLE, email_for, password_for
from main import app
from seed import seed
from firebase_admin import auth

def login(name, password):
    return requests.post(
        "http://127.0.0.1:9099/identitytoolkit.googleapis.com/v1/accounts:signInWithPassword?key=demo",
        json={"email": email_for(name), "password": password, "returnSecureToken": True}, timeout=10)

with tempfile.TemporaryDirectory() as folder:
    os.environ['DATABASE_URL'] = ''  # Always isolate regression fixtures from hosted data.
    os.environ["DATABASE_PATH"] = folder + "/test.sqlite3"
    seed()
    seed()
    assert len(list(auth.list_users().iterate_all())) == 10
    with TestClient(app) as client:
        assert client.get("/health").status_code == 200
        for path in ("/api/team", "/api/me"):
            assert client.get(path).status_code == 401
            assert client.get(path, headers={"Authorization":"Bearer invalid"}).status_code == 401
        for uid, name, role, _, skills in PEOPLE:
            signed = login(name, password_for(name))
            signed.raise_for_status()
            header = {"Authorization": "Bearer " + signed.json()["idToken"]}
            me = client.get("/api/me", headers=header).json()
            assert (me["id"], me["role"], me["skills"]) == (uid, role, skills)
            members = client.get("/api/team", headers=header).json()["members"]
            assert len(members) == 10
            assert all(set(m) == {"id","name","role","specialization","skills"} for m in members)
        assert login("Admin", "wrong-password").status_code == 400
        outsider = auth.create_user(email=email_for("outsider"), password="Demo123!")
        try:
            token = login("outsider", "Demo123!").json()["idToken"]
            assert client.get("/api/me", headers={"Authorization":"Bearer "+token}).status_code == 403
        finally:
            auth.delete_user(outsider.uid)
print("PASS: repeat seed, 10 logins, roles, directory, wrong password, missing/invalid token, unseeded identity.")
