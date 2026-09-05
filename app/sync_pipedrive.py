"""Sync organizací, kontaktů a dealů z Pipedrive API v2 (kurzorové stránkování).

Použití:
    export PIPEDRIVE_API_TOKEN=xxx
    python -m app.sync_pipedrive

Volitelné:
    PIPEDRIVE_BASE       výchozí https://api.pipedrive.com/api/v2
    PIPEDRIVE_ORG_FIELDS JSON mapa {naše_pole: hash_custom_fieldu} — přepíše výchozí
                         mapování níže (odpovídá Mediaboard CRM, kde saleskit/Merk
                         plní IČO, web, obor a velikost firmy).
"""

import json
import os
import re
import sys

import httpx

from .db import connect
from .matching import upsert_company, upsert_person
from .scoring import recompute_all

BASE = os.environ.get("PIPEDRIVE_BASE", "https://api.pipedrive.com/api/v2")

# Hashe custom fieldů organizací v Mediaboard CRM (plněné saleskit/Merk integrací).
DEFAULT_ORG_FIELDS = {
    "ico": "68e8d45bf22dd1063bcb5da9eebcd6987e23ffac",
    "domain": "d1291d1d34fd4d1daadbd2b8a4eb6dad3364acab",          # web firmy
    "segment": "00c1c87f0775e15448750312cc106da51a7125d7",         # obor (NACE text)
    "employees_bucket": "5e0b51d1e8e2171e0e3678d090e8a6169baa9153",  # „25 - 49 zaměstnanců"
    "saleskit_url": "3a2364318da8a366c314a903949fec3f0696ce68",
}
ORG_FIELDS = {**DEFAULT_ORG_FIELDS, **json.loads(os.environ.get("PIPEDRIVE_ORG_FIELDS", "{}"))}


def fetch_all(client: httpx.Client, endpoint: str):
    cursor = None
    while True:
        params = {"limit": 500}
        if cursor:
            params["cursor"] = cursor
        resp = client.get(f"{BASE}/{endpoint}", params=params)
        resp.raise_for_status()
        payload = resp.json()
        yield from payload.get("data") or []
        cursor = (payload.get("additional_data") or {}).get("next_cursor")
        if not cursor:
            return


def cf(record: dict, key: str):
    """Hodnota custom fieldu — enum/objektové typy vrací defenzivně jako text."""
    value = (record.get("custom_fields") or {}).get(ORG_FIELDS.get(key, ""), None)
    if isinstance(value, dict):
        value = value.get("value") or value.get("label")
    return value


def primary(items: list | None) -> str | None:
    """První primární hodnota z v2 polí emails/phones."""
    for item in items or []:
        if item.get("primary"):
            return item.get("value")
    return (items or [{}])[0].get("value") if items else None


def employees_from_bucket(bucket) -> int | None:
    match = re.match(r"\s*(\d+)", str(bucket or ""))
    return int(match.group(1)) if match else None


def run() -> None:
    token = os.environ.get("PIPEDRIVE_API_TOKEN")
    if not token:
        sys.exit("Chybí PIPEDRIVE_API_TOKEN — Pipedrive → Settings → Personal preferences → API.")

    conn = connect()
    with httpx.Client(params={"api_token": token}, timeout=60) as client:
        org_map: dict[int, int] = {}
        for org in fetch_all(client, "organizations"):
            address = org.get("address") or {}
            org_map[org["id"]] = upsert_company(
                conn,
                {
                    "name": org.get("name"),
                    "pipedrive_org_id": org["id"],
                    "country": address.get("country") if isinstance(address, dict) else None,
                    "city": address.get("locality") if isinstance(address, dict) else None,
                    "domain": cf(org, "domain"),
                    "ico": cf(org, "ico"),
                    "segment": cf(org, "segment"),
                    "employees": employees_from_bucket(cf(org, "employees_bucket")),
                    "note": cf(org, "saleskit_url"),
                },
                source="pipedrive",
            )

        person_map: dict[int, int] = {}
        for person in fetch_all(client, "persons"):
            person_map[person["id"]] = upsert_person(
                conn,
                {
                    "full_name": person.get("name"),
                    "pipedrive_person_id": person["id"],
                    "title": person.get("job_title"),
                    "email": primary(person.get("emails")),
                    "phone": primary(person.get("phones")),
                    "company_id": org_map.get(person.get("org_id")),
                },
                source="pipedrive",
            )

        deal_count = 0
        for deal in fetch_all(client, "deals"):
            conn.execute(
                """INSERT INTO deals (pipedrive_deal_id, company_id, person_id, title, status, value, currency, closed_at)
                   VALUES (?,?,?,?,?,?,?,?)
                   ON CONFLICT(pipedrive_deal_id) DO UPDATE SET
                     status=excluded.status, value=excluded.value, closed_at=excluded.closed_at""",
                (
                    deal["id"],
                    org_map.get(deal.get("org_id")),
                    person_map.get(deal.get("person_id")),
                    deal.get("title"),
                    deal.get("status"),
                    deal.get("value"),
                    deal.get("currency"),
                    deal.get("won_time") or deal.get("lost_time"),
                ),
            )
            deal_count += 1

    recompute_all(conn)
    conn.commit()
    print(f"Hotovo: {len(org_map)} organizací, {len(person_map)} kontaktů, {deal_count} dealů.")


if __name__ == "__main__":
    run()
