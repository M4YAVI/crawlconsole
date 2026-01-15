import aiosqlite
import json
from typing import Optional, Dict, Any, List
import os

DB_PATH = "crawlconsole.db"

async def init_db():
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
        CREATE TABLE IF NOT EXISTS jobs (
            id TEXT PRIMARY KEY,
            created_at TEXT,
            status TEXT,
            spec_json TEXT,
            error TEXT,
            stats_json TEXT
        )""")
        await db.execute("""
        CREATE TABLE IF NOT EXISTS results (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            job_id TEXT,
            url TEXT,
            status_code INTEGER,
            depth INTEGER,
            fetched_at TEXT,
            content_type TEXT,
            title TEXT,
            text TEXT,
            html TEXT,
            markdown TEXT,
            links_json TEXT,
            extracted_json TEXT,
            error TEXT
        )""")
        # Added markdown column above
        await db.commit()
    
    # Simple migration check (rudimentary) - if column missing, ignore for now or we rely on fresh db
    # Since this is a new install, it's fine.

async def create_job(job_id: str, created_at: str, spec: Dict[str, Any]):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT INTO jobs (id, created_at, status, spec_json) VALUES (?,?,?,?)",
            (job_id, created_at, "queued", json.dumps(spec))
        )
        await db.commit()

async def update_job(job_id: str, **fields):
    if not fields:
        return
    keys = ", ".join([f"{k}=?" for k in fields.keys()])
    values = list(fields.values())
    values.append(job_id)
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(f"UPDATE jobs SET {keys} WHERE id=?", values)
        await db.commit()

async def get_job(job_id: str) -> Optional[Dict[str, Any]]:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cur = await db.execute("SELECT * FROM jobs WHERE id=?", (job_id,))
        row = await cur.fetchone()
        return dict(row) if row else None

async def get_next_queued_job() -> Optional[Dict[str, Any]]:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cur = await db.execute("SELECT * FROM jobs WHERE status='queued' ORDER BY created_at LIMIT 1")
        row = await cur.fetchone()
        return dict(row) if row else None

async def insert_result(job_id: str, result: Dict[str, Any]):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
        INSERT INTO results (job_id, url, status_code, depth, fetched_at, content_type, title, text, html, markdown, links_json, extracted_json, error)
        VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)
        """, (
            job_id,
            result.get("url"),
            result.get("status_code"),
            result.get("depth"),
            result.get("fetched_at"),
            result.get("content_type"),
            result.get("title"),
            result.get("text"),
            result.get("html"),
            result.get("markdown"),
            json.dumps(result.get("links", [])),
            json.dumps(result.get("extracted", {})),
            result.get("error")
        ))
        await db.commit()

async def list_results(job_id: str, limit: int = 100, offset: int = 0) -> List[Dict[str, Any]]:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cur = await db.execute(
            "SELECT * FROM results WHERE job_id=? ORDER BY id LIMIT ? OFFSET ?",
            (job_id, limit, offset)
        )
        rows = await cur.fetchall()
        return [dict(r) for r in rows]
