"""SQLite vrstva Market Radaru — schéma a upserty se slévacím pravidlem:
hodnota z Pipedrivu se nikdy nepřepisuje hodnotou z tržního zdroje."""

import os
import sqlite3
from pathlib import Path

DB_PATH = Path(os.environ.get("RADAR_DB", "data/radar.db"))

SCHEMA = """
CREATE TABLE IF NOT EXISTS companies (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    name_norm TEXT NOT NULL,
    domain TEXT,
    ico TEXT,
    country TEXT,
    city TEXT,
    segment TEXT,
    employees INTEGER,
    linkedin_url TEXT,
    monitoring_tool TEXT,
    pipedrive_org_id INTEGER UNIQUE,
    status TEXT NOT NULL DEFAULT 'market',
    sources TEXT NOT NULL DEFAULT '',
    score INTEGER NOT NULL DEFAULT 0,
    approach TEXT,
    approach_reason TEXT,
    note TEXT,
    updated_at TEXT DEFAULT (datetime('now'))
);
CREATE INDEX IF NOT EXISTS idx_companies_domain ON companies(domain);
CREATE INDEX IF NOT EXISTS idx_companies_name_norm ON companies(name_norm);

CREATE TABLE IF NOT EXISTS people (
    id INTEGER PRIMARY KEY,
    company_id INTEGER REFERENCES companies(id),
    full_name TEXT NOT NULL,
    name_norm TEXT NOT NULL,
    title TEXT,
    seniority TEXT,
    email TEXT,
    phone TEXT,
    linkedin_url TEXT,
    country TEXT,
    pipedrive_person_id INTEGER UNIQUE,
    status TEXT NOT NULL DEFAULT 'market',
    sources TEXT NOT NULL DEFAULT '',
    score INTEGER NOT NULL DEFAULT 0,
    approach TEXT,
    approach_reason TEXT,
    updated_at TEXT DEFAULT (datetime('now'))
);
CREATE INDEX IF NOT EXISTS idx_people_email ON people(email);
CREATE INDEX IF NOT EXISTS idx_people_name ON people(name_norm, company_id);

CREATE TABLE IF NOT EXISTS deals (
    id INTEGER PRIMARY KEY,
    pipedrive_deal_id INTEGER UNIQUE,
    company_id INTEGER REFERENCES companies(id),
    person_id INTEGER REFERENCES people(id),
    title TEXT,
    status TEXT,              -- open / won / lost
    value REAL,
    currency TEXT,
    closed_at TEXT
);
"""

PROTECTED_SOURCE = "pipedrive"


def connect() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.executescript(SCHEMA)
    try:  # migrace starších databází
        conn.execute("ALTER TABLE companies ADD COLUMN ico TEXT")
    except sqlite3.OperationalError:
        pass
    return conn


def merge_sources(existing: str, new: str) -> str:
    items = {s for s in (existing or "").split(",") if s}
    items.update(s for s in (new or "").split(",") if s)
    return ",".join(sorted(items))


def merge_row(conn, table: str, row_id: int, fields: dict, source: str):
    """Doplní chybějící pole; existující hodnoty přepisuje jen Pipedrive."""
    current = dict(conn.execute(f"SELECT * FROM {table} WHERE id=?", (row_id,)).fetchone())
    from_pipedrive = source == PROTECTED_SOURCE
    updates = {}
    for key, value in fields.items():
        if value in (None, ""):
            continue
        if not current.get(key) or (from_pipedrive and current.get(key) != value):
            updates[key] = value
    updates["sources"] = merge_sources(current.get("sources", ""), source)
    updates["updated_at"] = None  # nastaví se níž
    sets = ", ".join(f"{k}=?" for k in updates if k != "updated_at")
    values = [v for k, v in updates.items() if k != "updated_at"]
    conn.execute(
        f"UPDATE {table} SET {sets}, updated_at=datetime('now') WHERE id=?",
        (*values, row_id),
    )
    return row_id


def insert_row(conn, table: str, fields: dict, source: str) -> int:
    fields = {k: v for k, v in fields.items() if v not in (None, "")}
    fields["sources"] = source
    cols = ", ".join(fields)
    marks = ", ".join("?" for _ in fields)
    cur = conn.execute(f"INSERT INTO {table} ({cols}) VALUES ({marks})", list(fields.values()))
    return cur.lastrowid
