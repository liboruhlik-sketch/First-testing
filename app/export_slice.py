"""Export kurátorovaného výběru z radar.db pro online dashboard.

Do stránky se nevejde celá databáze (100k+ záznamů), takže se vybírá:
- všechny firmy se vztahem (customer/prospect/lost),
- z nepokrytého trhu firmy z PR/komunikačních/mediálních oborů a nejvyšší skóre,
- top lidé podle skóre + všichni lidé zahrnutých firem do limitu.

Použití: python -m app.export_slice  → data/export/radar_slice.json
"""

import json
import re
from pathlib import Path

from .db import connect

OUT = Path("data/export/radar_slice.json")
MAX_COMPANIES = 15000
MAX_PEOPLE = 25000

RELEVANT_SEGMENT = re.compile(
    r"public relations|komunikac|komunikác|reklam|marketing|médi|medi[aá]|vydáv|vydav|tisk|publish|advertis|broadcast|rozhlas|televiz",
    re.IGNORECASE,
)

COMPANY_FIELDS = ("id", "name", "domain", "ico", "country", "city", "segment",
                  "employees", "linkedin_url", "monitoring_tool", "status",
                  "sources", "score", "approach", "approach_reason", "pipedrive_org_id")
PERSON_FIELDS = ("id", "company_id", "full_name", "title", "email", "phone",
                 "linkedin_url", "country", "status", "sources", "score",
                 "approach", "approach_reason", "pipedrive_person_id")


def slim(row, fields):
    return {k: row[k] for k in fields if row[k] not in (None, "")}


def run() -> None:
    conn = connect()

    def counts(table):
        out = {"customer": 0, "prospect": 0, "lost": 0, "market": 0}
        for row in conn.execute(f"SELECT status, COUNT(*) c FROM {table} GROUP BY status"):
            out[row["status"]] = row["c"]
        return out

    summary = {"companies": counts("companies"), "people": counts("people")}

    companies: dict[int, dict] = {}
    for row in conn.execute(
        "SELECT * FROM companies WHERE status != 'market' ORDER BY score DESC, name"
    ):
        companies[row["id"]] = slim(row, COMPANY_FIELDS)

    market_rows = conn.execute(
        "SELECT * FROM companies WHERE status = 'market' ORDER BY score DESC, name"
    ).fetchall()
    for row in market_rows:  # nejdřív relevantní obory…
        if len(companies) >= MAX_COMPANIES:
            break
        if row["segment"] and RELEVANT_SEGMENT.search(row["segment"]):
            companies[row["id"]] = slim(row, COMPANY_FIELDS)
    for row in market_rows:  # …pak zbytek podle skóre
        if len(companies) >= MAX_COMPANIES:
            break
        companies.setdefault(row["id"], slim(row, COMPANY_FIELDS))

    people = []
    for row in conn.execute("SELECT * FROM people ORDER BY score DESC, full_name"):
        if len(people) >= MAX_PEOPLE:
            break
        people.append(slim(row, PERSON_FIELDS))
        cid = row["company_id"]
        if cid and cid not in companies:  # firma zmíněného člověka musí být v datech
            company = conn.execute("SELECT * FROM companies WHERE id=?", (cid,)).fetchone()
            if company:
                companies[cid] = slim(company, COMPANY_FIELDS)

    total_c = sum(summary["companies"].values())
    total_p = sum(summary["people"].values())
    payload = {
        "meta": {
            "label": "ostrá data",
            "slice": {"companies": len(companies), "companies_total": total_c,
                      "people": len(people), "people_total": total_p},
        },
        "summary": summary,
        "companies": list(companies.values()),
        "people": people,
        "deals": [],
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(payload, ensure_ascii=False, separators=(",", ":")))
    print(f"Export: {len(companies)} firem, {len(people)} lidí → {OUT} "
          f"({OUT.stat().st_size/1e6:.1f} MB)")


if __name__ == "__main__":
    run()
