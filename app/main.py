"""FastAPI server Market Radaru — jedno API (/api/data) + statický dashboard.

Zabezpečení: nastav RADAR_PASSWORD (a volitelně RADAR_USER, výchozí „mediaboard")
a celá aplikace se schová za HTTP Basic přihlášení. Bez nastavené proměnné běží
otevřeně — určeno jen pro lokální vývoj. Detaily v docs/NAVRH.md, sekce Security.
"""

import base64
import os
import secrets
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import FileResponse, Response
from fastapi.staticfiles import StaticFiles

from .db import DB_PATH, connect

app = FastAPI(title="Market Radar")
STATIC = Path(__file__).parent / "static"


@app.middleware("http")
async def basic_auth(request: Request, call_next):
    password = os.environ.get("RADAR_PASSWORD")
    if password:
        user_expected = os.environ.get("RADAR_USER", "mediaboard")
        header = request.headers.get("authorization", "")
        authorized = False
        if header.startswith("Basic "):
            try:
                user, _, pwd = base64.b64decode(header[6:]).decode().partition(":")
                authorized = secrets.compare_digest(user, user_expected) and secrets.compare_digest(pwd, password)
            except Exception:
                authorized = False
        if not authorized:
            return Response(status_code=401, headers={"WWW-Authenticate": 'Basic realm="Market Radar"'})
    return await call_next(request)


def snapshot() -> dict:
    """Kompletní data pro dashboard. Prototyp filtruje na klientu —
    při větším objemu se sem přidá stránkování a server-side filtry."""
    conn = connect()
    companies = [dict(r) for r in conn.execute("SELECT * FROM companies ORDER BY score DESC, name")]
    people = [dict(r) for r in conn.execute(
        """SELECT p.*, c.name AS company_name, c.domain AS company_domain,
                  c.segment AS company_segment, c.country AS company_country,
                  c.status AS company_status
           FROM people p LEFT JOIN companies c ON c.id = p.company_id
           ORDER BY p.score DESC, p.full_name"""
    )]
    deals = [dict(r) for r in conn.execute("SELECT * FROM deals")]
    conn.close()

    def counts(rows):
        out = {"customer": 0, "prospect": 0, "lost": 0, "market": 0}
        for row in rows:
            out[row.get("status") or "market"] += 1
        return out

    return {
        "generated_from": str(DB_PATH),
        "summary": {"companies": counts(companies), "people": counts(people)},
        "companies": companies,
        "people": people,
        "deals": deals,
    }


@app.get("/api/data")
def data():
    return snapshot()


@app.get("/")
def index():
    return FileResponse(STATIC / "index.html")


app.mount("/static", StaticFiles(directory=STATIC), name="static")
