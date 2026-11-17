import json
import os
import sqlite3
from contextlib import contextmanager, closing
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

def pg_sql(sql):
    import re
    fields = "clientName managerId projectId assigneeId estimatedHours managerName assigneeName projectName projectDeadline".split()
    return re.sub(r"\b("+"|".join(fields)+r")\b", lambda m: '"'+m[0]+'"', sql).replace("?", "%s")

@contextmanager
def database():
    url = os.getenv("DATABASE_URL")
    if url:
        import psycopg
        from psycopg.rows import dict_row
        with psycopg.connect(url, row_factory=dict_row, connect_timeout=10) as conn:
            class Postgres:
                def execute(self, sql, params=()):
                    if sql == "BEGIN IMMEDIATE":
                        return conn.execute("LOCK TABLE transcript_imports IN SHARE ROW EXCLUSIVE MODE")
                    return conn.execute(pg_sql(sql), params)
                def executemany(self, sql, rows):
                    with conn.cursor() as cursor:
                        cursor.executemany(pg_sql(sql), rows)
                def executescript(self, sql):
                    for statement in sql.split(";"):
                        if statement.strip():
                            conn.execute(pg_sql(statement))
            yield Postgres()
        return
    path = Path(os.getenv("DATABASE_PATH", "data/novaworks.sqlite3"))
    path.parent.mkdir(parents=True, exist_ok=True)
    with closing(sqlite3.connect(path)) as db:
        db.row_factory = sqlite3.Row
        db.execute("PRAGMA foreign_keys = ON")
        with db:
            yield db

def initialize():
    with database() as db:
        db.executescript("""
            CREATE TABLE IF NOT EXISTS users (
                id TEXT PRIMARY KEY, name TEXT NOT NULL, email TEXT NOT NULL UNIQUE,
                role TEXT NOT NULL CHECK(role IN ('ADMIN','MANAGER','AGENT')),
                specialization TEXT NOT NULL, skills TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS transcript_imports (digest TEXT PRIMARY KEY, result TEXT NOT NULL);
            CREATE TABLE IF NOT EXISTS projects (
                id TEXT PRIMARY KEY, name TEXT NOT NULL, clientName TEXT NOT NULL,
                description TEXT NOT NULL, managerId TEXT NOT NULL REFERENCES users(id),
                deadline TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS tasks (
                id TEXT PRIMARY KEY, projectId TEXT NOT NULL REFERENCES projects(id),
                title TEXT NOT NULL, description TEXT NOT NULL,
                assigneeId TEXT NOT NULL REFERENCES users(id), deadline TEXT NOT NULL,
                estimatedHours REAL NOT NULL CHECK(estimatedHours > 0)
            );
        """)

def profile(row):
    return {**dict(row), "skills": json.loads(row["skills"])}
