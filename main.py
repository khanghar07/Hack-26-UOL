import os
from contextlib import asynccontextmanager
from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from firebase_admin import auth, exceptions
from google.auth.exceptions import DefaultCredentialsError
from access import visible_projects, assigned_tasks
from identity import verify, BackendNotConfigured
from storage import database, initialize, profile

@asynccontextmanager
async def lifespan(app):
    if not os.getenv("VERCEL") or os.getenv("DATABASE_URL"):
        initialize()
    yield

app = FastAPI(title="NovaWorks CRM", version="0.3.1", lifespan=lifespan)
app.add_middleware(CORSMiddleware, allow_origins=[os.getenv("FRONTEND_ORIGIN", "http://localhost:5173")],
                   allow_methods=["GET", "POST"], allow_headers=["Authorization", "Content-Type"])
bearer = HTTPBearer(auto_error=False)

def current_user(credentials: HTTPAuthorizationCredentials | None = Depends(bearer)):
    if not credentials:
        raise HTTPException(401, "Sign in to continue.")
    if os.getenv("VERCEL") and not os.getenv("DATABASE_URL"):
        raise HTTPException(503, "Production database is not configured.")
    try:
        uid = verify(credentials.credentials)
    except (DefaultCredentialsError, BackendNotConfigured):
        raise HTTPException(503, "Firebase Admin credentials are not configured on this backend.")
    except auth.CertificateFetchError:
        raise HTTPException(503, "Firebase verification temporarily unavailable.")
    except (auth.InvalidIdTokenError, auth.RevokedIdTokenError, auth.UserDisabledError, auth.UserNotFoundError, ValueError):
        raise HTTPException(401, "Session invalid. Sign in again.")
    except exceptions.FirebaseError:
        raise HTTPException(503, "Firebase verification temporarily unavailable.")
    with database() as db:
        row = db.execute("SELECT * FROM users WHERE id=?", (uid,)).fetchone()
    if not row:
        raise HTTPException(403, "This account has no NovaWorks team profile.")
    return profile(row)

@app.get("/health")
def health():
    if os.getenv("VERCEL") and not os.getenv("DATABASE_URL"):
        raise HTTPException(503, "Production database is not configured.")
    return {"status": "ok"}

@app.get("/api/me")
def me(user=Depends(current_user)):
    return user

@app.get("/api/team")
def team(user=Depends(current_user)):
    with database() as db:
        rows = db.execute("""SELECT id,name,role,specialization,skills FROM users
            ORDER BY CASE role WHEN 'ADMIN' THEN 1 WHEN 'MANAGER' THEN 2 ELSE 3 END, id""").fetchall()
    return {"members": [profile(row) for row in rows]}

@app.get("/api/projects")
def projects(user=Depends(current_user)):
    return {"projects": visible_projects(user)}

@app.get("/api/projects/{project_id}")
def project_detail(project_id: str, user=Depends(current_user)):
    projects = visible_projects(user, project_id)
    if not projects:
        raise HTTPException(404, "Project unavailable.")
    return projects[0]

@app.get("/api/tasks/mine")
def my_tasks(user=Depends(current_user)):
    if user["role"] != "AGENT":
        raise HTTPException(403, "My Tasks is available to agents.")
    return {"tasks": assigned_tasks(user)}


from extraction import ImportRequest, Correction, ProviderError, generate, validate, save, import_key, previous

@app.post("/api/transcript")
def create_from_transcript(body: ImportRequest, user=Depends(current_user)):
    if user["role"] != "ADMIN":
        raise HTTPException(403, "Only administrators can import meetings.")
    key = import_key(body)
    cached = previous(key)
    if cached:
        return {**cached, "replayed": True}
    with database() as db:
        directory = [profile(row) for row in db.execute(
            "SELECT id,name,role,specialization,skills FROM users").fetchall()]
    try:
        raw, provider, model = generate(body, directory)
        parsed = validate(raw, directory, body.meetingDate, body.transcript)
        return save(parsed, key, provider, model)
    except Correction as exc:
        raise HTTPException(422, {"code": "correction_required", "issues": exc.issues})
    except ProviderError as exc:
        raise HTTPException(503, {"code": "provider_unavailable", "message": str(exc)})

# API routes are registered first. Hash-based browser navigation serves one entry point.
from pathlib import Path
from fastapi.staticfiles import StaticFiles
frontend_dist = Path(__file__).parent / "frontend" / "dist"
if frontend_dist.is_dir():
    app.mount("/", StaticFiles(directory=frontend_dist, html=True), name="frontend")
