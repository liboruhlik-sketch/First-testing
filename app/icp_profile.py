"""ICP profil odvozený z existujících zákazníků.

Porovná zákazníky (status=customer) s celou databází a spočítá lift:
o kolik častěji se daný obor / velikost / země / slovo v pozici vyskytuje
u zákazníků než v celém trhu. Z liftů vzniknou váhy pro scoring
(data/icp_weights.json) a čitelný report (docs/ICP_PROFILE.md).

Použití: python -m app.icp_profile
"""

import json
import re
from collections import Counter
from pathlib import Path

from .db import connect

WEIGHTS_PATH = Path("data/icp_weights.json")
REPORT_PATH = Path("docs/ICP_PROFILE.md")

MIN_CUSTOMERS_SEGMENT = 8     # menší vzorek = náhoda, ne signál
MIN_CUSTOMERS_TOKEN = 15
STOP_TOKENS = {"and", "the", "for", "von", "der", "pro", "the", "als", "des", "manager", "specialist"}


def size_bucket(employees) -> str | None:
    if not employees:
        return None
    e = int(employees)
    if e < 10:
        return "1-9"
    if e < 50:
        return "10-49"
    if e < 250:
        return "50-249"
    if e < 1000:
        return "250-999"
    return "1000+"


def lift_weight(lift: float, max_weight: int) -> int:
    """Převod liftu na váhu: 1× = nic, 2× = polovina, 4×+ = maximum."""
    if lift < 1.2:
        return 0
    if lift >= 4:
        return max_weight
    return round(max_weight * (lift - 1) / 3)


def lifts(customer_counter: Counter, all_counter: Counter, n_cust: int, n_all: int,
          min_support: int) -> list[tuple[str, int, float]]:
    out = []
    for key, c_count in customer_counter.items():
        if c_count < min_support:
            continue
        share_cust = c_count / n_cust
        share_all = all_counter[key] / n_all
        out.append((key, c_count, share_cust / share_all if share_all else 0.0))
    return sorted(out, key=lambda x: -x[2])


def tokenize(title: str):
    for tok in re.split(r"[^a-zA-Zá-žÁ-Ž]+", (title or "").lower()):
        if len(tok) >= 3 and tok not in STOP_TOKENS:
            yield tok


def run() -> None:
    conn = connect()
    companies = [dict(r) for r in conn.execute("SELECT segment, employees, country, status FROM companies")]
    customers = [c for c in companies if c["status"] == "customer"]
    if len(customers) < 30:
        print(f"Jen {len(customers)} zákazníků — na statistiku málo, váhy negeneruji (scoring má fallback).")
        return

    n_all, n_cust = len(companies), len(customers)

    def counter(rows, key_fn):
        return Counter(k for k in (key_fn(r) for r in rows) if k)

    seg_l = lifts(counter(customers, lambda c: c["segment"]),
                  counter(companies, lambda c: c["segment"]), n_cust, n_all, MIN_CUSTOMERS_SEGMENT)
    size_l = lifts(counter(customers, lambda c: size_bucket(c["employees"])),
                   counter(companies, lambda c: size_bucket(c["employees"])), n_cust, n_all, MIN_CUSTOMERS_SEGMENT)
    country_l = lifts(counter(customers, lambda c: c["country"]),
                      counter(companies, lambda c: c["country"]), n_cust, n_all, MIN_CUSTOMERS_SEGMENT)

    people = [dict(r) for r in conn.execute(
        """SELECT p.title, c.status FROM people p
           JOIN companies c ON c.id = p.company_id WHERE p.title IS NOT NULL"""
    )]
    cust_people = [p for p in people if p["status"] == "customer"]
    tok_l = lifts(Counter(t for p in cust_people for t in set(tokenize(p["title"]))),
                  Counter(t for p in people for t in set(tokenize(p["title"]))),
                  max(len(cust_people), 1), max(len(people), 1), MIN_CUSTOMERS_TOKEN)

    weights = {
        "generated_from": {"customers": n_cust, "companies": n_all},
        "segments": {k: w for k, c, l in seg_l if (w := lift_weight(l, 30))},
        "size_buckets": {k: w for k, c, l in size_l if (w := lift_weight(l, 12))},
        "countries": {k: w for k, c, l in country_l if (w := lift_weight(l, 8))},
        "title_tokens": {k: w for k, c, l in tok_l[:40] if (w := lift_weight(l, 15))},
    }
    WEIGHTS_PATH.parent.mkdir(parents=True, exist_ok=True)
    WEIGHTS_PATH.write_text(json.dumps(weights, ensure_ascii=False, indent=1))

    def table(rows, label):
        lines = [f"| {label} | Zákazníků | Lift |", "|---|---:|---:|"]
        lines += [f"| {k} | {c} | {l:.1f}× |" for k, c, l in rows[:25]]
        return "\n".join(lines)

    REPORT_PATH.write_text(f"""# ICP profil z existujících zákazníků

Vygenerováno z {n_cust} zákaznických firem (vs. {n_all} firem celkem v Radaru).
Lift = kolikrát častěji se hodnota vyskytuje u zákazníků než v celém trhu.
Váhy pro scoring: data/icp_weights.json (přegenerovat: `python -m app.icp_profile`).

## Obory (NACE), kde skutečně nakupují
{table(seg_l, "Obor")}

## Velikost firmy
{table(size_l, "Zaměstnanců")}

## Země
{table(country_l, "Země")}

## Slova v pozicích lidí u zákazníků
{table(tok_l, "Slovo v pozici")}
""")
    print(f"Váhy: {WEIGHTS_PATH} · Report: {REPORT_PATH} "
          f"({len(weights['segments'])} oborů, {len(weights['title_tokens'])} tokenů)")


if __name__ == "__main__":
    run()
