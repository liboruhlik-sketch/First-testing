"""Normalizace a párování záznamů napříč zdroji (Pipedrive vs. tržní databáze)."""

import re
import unicodedata

LEGAL_SUFFIXES = re.compile(
    r"[,\s]+(s\.?\s?r\.?\s?o\.?|a\.?\s?s\.?|spol\.? s r\.?o\.?|z\.?\s?s\.?|k\.?\s?s\.?"
    r"|gmbh|ag|ltd\.?|llc|inc\.?|s\.?a\.?|sp\.? z o\.?o\.?|b\.?v\.?|oy|ab)\s*$",
    re.IGNORECASE,
)


def normalize_name(name: str) -> str:
    if not name:
        return ""
    text = unicodedata.normalize("NFKD", name)
    text = "".join(c for c in text if not unicodedata.combining(c))
    text = LEGAL_SUFFIXES.sub("", text.strip())
    ascii_norm = re.sub(r"[^a-z0-9]+", " ", text.lower()).strip()
    # Nelatinkové názvy (arabština, azbuka…) by se vyprázdnily — drž aspoň lowercase originálu.
    return ascii_norm or text.lower().strip()


def normalize_domain(value: str) -> str:
    if not value:
        return ""
    value = value.strip().lower()
    value = re.sub(r"^https?://", "", value)
    value = value.split("/")[0]
    return value.removeprefix("www.")


def normalize_email(value: str) -> str:
    return (value or "").strip().lower()


def find_company(conn, *, pipedrive_org_id=None, domain=None, name=None):
    """Vrátí id firmy podle nejsilnějšího dostupného klíče, jinak None."""
    if pipedrive_org_id:
        row = conn.execute(
            "SELECT id FROM companies WHERE pipedrive_org_id=?", (pipedrive_org_id,)
        ).fetchone()
        if row:
            return row["id"]
    domain = normalize_domain(domain or "")
    if domain:
        row = conn.execute("SELECT id FROM companies WHERE domain=?", (domain,)).fetchone()
        if row:
            return row["id"]
    name_norm = normalize_name(name or "")
    if name_norm:
        row = conn.execute("SELECT id FROM companies WHERE name_norm=?", (name_norm,)).fetchone()
        if row:
            return row["id"]
    return None


def find_person(conn, *, pipedrive_person_id=None, email=None, name=None, company_id=None):
    if pipedrive_person_id:
        row = conn.execute(
            "SELECT id FROM people WHERE pipedrive_person_id=?", (pipedrive_person_id,)
        ).fetchone()
        if row:
            return row["id"]
    email = normalize_email(email)
    if email:
        row = conn.execute("SELECT id FROM people WHERE email=?", (email,)).fetchone()
        if row:
            return row["id"]
    name_norm = normalize_name(name or "")
    if name_norm and company_id:
        row = conn.execute(
            "SELECT id FROM people WHERE name_norm=? AND company_id=?", (name_norm, company_id)
        ).fetchone()
        if row:
            return row["id"]
    return None


def upsert_company(conn, fields: dict, source: str) -> int:
    from .db import insert_row, merge_row

    fields = dict(fields)
    fields["domain"] = normalize_domain(fields.get("domain", ""))
    fields["name_norm"] = normalize_name(fields.get("name", ""))
    existing = find_company(
        conn,
        pipedrive_org_id=fields.get("pipedrive_org_id"),
        domain=fields.get("domain"),
        name=fields.get("name"),
    )
    if existing:
        return merge_row(conn, "companies", existing, fields, source)
    return insert_row(conn, "companies", fields, source)


def upsert_person(conn, fields: dict, source: str) -> int:
    from .db import insert_row, merge_row

    fields = dict(fields)
    fields["email"] = normalize_email(fields.get("email", ""))
    fields["name_norm"] = normalize_name(fields.get("full_name", ""))
    existing = find_person(
        conn,
        pipedrive_person_id=fields.get("pipedrive_person_id"),
        email=fields.get("email"),
        name=fields.get("full_name"),
        company_id=fields.get("company_id"),
    )
    if existing:
        return merge_row(conn, "people", existing, fields, source)
    return insert_row(conn, "people", fields, source)
