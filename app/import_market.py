"""CSV import tržních dat (firmy i lidé). Mapuje běžné hlavičky včetně Apollo exportu.

Použití:
    python -m app.import_market companies data/samples/market_companies.csv --source apollo
    python -m app.import_market people    data/samples/market_people.csv    --source apollo
"""

import argparse
import csv

from .db import connect
from .matching import upsert_company, upsert_person
from .scoring import recompute_all

COMPANY_COLUMNS = {
    "name": ("name", "company", "company name", "organization"),
    "domain": ("domain", "website", "company website", "primary domain"),
    "country": ("country", "company country"),
    "city": ("city", "company city"),
    "segment": ("segment", "industry"),
    "employees": ("employees", "# employees", "company size"),
    "linkedin_url": ("linkedin_url", "company linkedin url"),
    "monitoring_tool": ("monitoring_tool", "current tool"),
}

PERSON_COLUMNS = {
    "full_name": ("full_name", "name", "full name"),
    "title": ("title", "job title", "position"),
    "email": ("email", "work email"),
    "phone": ("phone", "mobile phone", "work direct phone"),
    "linkedin_url": ("linkedin_url", "person linkedin url", "linkedin"),
    "country": ("country",),
    "company": ("company", "company name", "organization"),
    "company_domain": ("company_domain", "website", "company website"),
}


def pick(row: dict, aliases: tuple[str, ...]) -> str | None:
    lowered = {k.strip().lower(): v for k, v in row.items() if k}
    for alias in aliases:
        if lowered.get(alias):
            return lowered[alias].strip()
    return None


def run() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("kind", choices=("companies", "people"))
    parser.add_argument("csv_path")
    parser.add_argument("--source", default="csv", help="označení zdroje (apollo, lemlist, apra…)")
    args = parser.parse_args()

    conn = connect()
    count = 0
    with open(args.csv_path, newline="", encoding="utf-8-sig") as fh:
        for row in csv.DictReader(fh):
            if args.kind == "companies":
                fields = {key: pick(row, aliases) for key, aliases in COMPANY_COLUMNS.items()}
                if not fields.get("name"):
                    continue
                if fields.get("employees"):
                    fields["employees"] = int("".join(c for c in fields["employees"] if c.isdigit()) or 0)
                upsert_company(conn, fields, source=args.source)
            else:
                fields = {key: pick(row, aliases) for key, aliases in PERSON_COLUMNS.items()}
                if not fields.get("full_name"):
                    continue
                company_name = fields.pop("company", None)
                company_domain = fields.pop("company_domain", None)
                if company_name or company_domain:
                    fields["company_id"] = upsert_company(
                        conn,
                        {"name": company_name or company_domain, "domain": company_domain},
                        source=args.source,
                    )
                upsert_person(conn, fields, source=args.source)
            count += 1

    recompute_all(conn)
    conn.commit()
    print(f"Importováno {count} řádků z {args.csv_path} (zdroj: {args.source}).")


if __name__ == "__main__":
    run()
