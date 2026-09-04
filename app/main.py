"""FastAPI server Market Radaru — jedno API (/api/data) + statický dashboard."""

from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from .db import DB_PATH, connect

app = FastAPI(title="Market Radar")
STATIC = Path(__file__).parent / "static"


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
