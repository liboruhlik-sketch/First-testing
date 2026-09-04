"""Sync organizací, kontaktů a dealů z Pipedrive API.

Použití:
    export PIPEDRIVE_API_TOKEN=xxx
    python -m app.sync_pipedrive
"""

import os
import sys

import httpx

from .db import connect
from .matching import upsert_company, upsert_person
from .scoring import recompute_all

BASE = os.environ.get("PIPEDRIVE_BASE", "https://api.pipedrive.com/v1")


def fetch_all(client: httpx.Client, endpoint: str) -> list[dict]:
    items, start = [], 0
    while True:
        resp = client.get(f"{BASE}/{endpoint}", params={"start": start, "limit": 500})
        resp.raise_for_status()
        payload = resp.json()
        items.extend(payload.get("data") or [])
        more = (payload.get("additional_data") or {}).get("pagination", {})
        if not more.get("more_items_in_collection"):
            return items
        start = more["next_start"]


def first_value(field) -> str | None:
    """Pipedrive vrací e-maily/telefony jako seznam {label, value, primary}."""
    if isinstance(field, list) and field:
        primary = next((f for f in field if f.get("primary")), field[0])
        return primary.get("value")
    if isinstance(field, str):
        return field
    return None


def run() -> None:
    token = os.environ.get("PIPEDRIVE_API_TOKEN")
    if not token:
        sys.exit("Chybí PIPEDRIVE_API_TOKEN — Pipedrive → Settings → Personal preferences → API.")

    conn = connect()
    with httpx.Client(params={"api_token": token}, timeout=30) as client:
        org_map: dict[int, int] = {}
        for org in fetch_all(client, "organizations"):
            org_map[org["id"]] = upsert_company(
                conn,
                {
                    "name": org.get("name"),
                    "pipedrive_org_id": org["id"],
                    "country": (org.get("address_country") or None),
                    "city": (org.get("address_locality") or None),
                },
                source="pipedrive",
            )

        person_map: dict[int, int] = {}
        for person in fetch_all(client, "persons"):
            org = person.get("org_id") or {}
            org_id = org.get("value") if isinstance(org, dict) else org
            person_map[person["id"]] = upsert_person(
                conn,
                {
                    "full_name": person.get("name"),
                    "pipedrive_person_id": person["id"],
                    "email": first_value(person.get("email")),
                    "phone": first_value(person.get("phone")),
                    "company_id": org_map.get(org_id),
                },
                source="pipedrive",
            )

        for deal in fetch_all(client, "deals"):
            org = deal.get("org_id") or {}
            org_id = org.get("value") if isinstance(org, dict) else org
            person = deal.get("person_id") or {}
            pid = person.get("value") if isinstance(person, dict) else person
            conn.execute(
                """INSERT INTO deals (pipedrive_deal_id, company_id, person_id, title, status, value, currency, closed_at)
                   VALUES (?,?,?,?,?,?,?,?)
                   ON CONFLICT(pipedrive_deal_id) DO UPDATE SET
                     status=excluded.status, value=excluded.value, closed_at=excluded.closed_at""",
                (
                    deal["id"],
                    org_map.get(org_id),
                    person_map.get(pid),
                    deal.get("title"),
                    deal.get("status"),
                    deal.get("value"),
                    deal.get("currency"),
                    deal.get("won_time") or deal.get("lost_time"),
                ),
            )

    recompute_all(conn)
    conn.commit()
    print(f"Hotovo: {len(org_map)} organizací, {len(person_map)} kontaktů.")


if __name__ == "__main__":
    run()
