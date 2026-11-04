from __future__ import annotations

import json
import os
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

from .models import Project


def atomic_json(path: Path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + f".{uuid4().hex}.tmp")
    try:
        with temporary.open("w", encoding="utf-8") as handle:
            json.dump(data, handle, ensure_ascii=False, indent=2, allow_nan=False)
            handle.flush()
            os.fsync(handle.fileno())
        temporary.replace(path)
    finally:
        temporary.unlink(missing_ok=True)


class Store:
    def __init__(self, root: Path):
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True)
        self.database = self.root / "vex.sqlite"
        with self.connect() as db:
            db.execute("CREATE TABLE IF NOT EXISTS projects (id TEXT PRIMARY KEY, title TEXT, path TEXT, updated TEXT)")
            db.execute("CREATE TABLE IF NOT EXISTS jobs (id TEXT PRIMARY KEY, kind TEXT, status TEXT, progress REAL, error TEXT, updated TEXT)")
            db.execute("UPDATE jobs SET status='INTERRUPTED' WHERE status IN ('RUNNING', 'PENDING')")

    def connect(self):
        return sqlite3.connect(self.database, timeout=30)

    def save(self, project: Project, folder: Path | None = None) -> Path:
        # Revalidate nested models which may have been edited programmatically.
        project = Project.model_validate(project.model_dump())
        folder = Path(folder) if folder else self.root / "projects" / project.id
        for sub in ("scenes", "assets", "audio", "subtitles", "cache", "exports"):
            (folder / sub).mkdir(parents=True, exist_ok=True)
        manifest = folder / "project.json"
        atomic_json(manifest, project.model_dump())
        with self.connect() as db:
            db.execute("INSERT OR REPLACE INTO projects VALUES (?,?,?,?)", (project.id, project.title, str(manifest.resolve()), datetime.now(timezone.utc).isoformat()))
        return manifest

    def load(self, manifest: Path) -> Project:
        manifest = Path(manifest)
        if manifest.stat().st_size > 20_000_000:
            raise ValueError("Proje dosyası 20 MB sınırını aşıyor")
        project = Project.model_validate_json(manifest.read_text(encoding="utf-8"))
        self.save(project, manifest.parent)
        return project

    def recent(self):
        with self.connect() as db:
            return [dict(id=r[0], title=r[1], path=r[2], updated=r[3]) for r in db.execute("SELECT * FROM projects ORDER BY updated DESC LIMIT 20")]

    def job(self, job_id, kind, status, progress=0, error=""):
        with self.connect() as db:
            db.execute("INSERT OR REPLACE INTO jobs VALUES (?,?,?,?,?,?)", (job_id, kind, status, progress, error, datetime.now(timezone.utc).isoformat()))

    def history(self):
        with self.connect() as db:
            return [dict(id=r[0], kind=r[1], status=r[2], progress=r[3], error=r[4]) for r in db.execute("SELECT * FROM jobs ORDER BY updated DESC LIMIT 20")]
