"""Status, priorita 0–100 a atribuce „kudy na ně".

Verze 1 je záměrně pravidlová a čitelná — obchodník musí rozumět, proč je
někdo nahoře. Viz docs/NAVRH.md, sekce Skóre priority.
"""

import re
from datetime import datetime, timedelta

DECISION_WORDS = ("ředitel", "director", "head", "chief", "cco", "ceo", "vp", "managing", "partner", "mluvčí", "spokesperson")
MID_WORDS = ("manager", "manažer", "lead", "senior")

SEGMENT_FIT = {
    "PR agentura": 30,
    "In-house komunikace": 25,
    "Public affairs": 20,
}


def seniority(title: str) -> str:
    t = (title or "").lower()
    if any(w in t for w in DECISION_WORDS):
        return "decision"
    if any(w in t for w in MID_WORDS):
        return "mid"
    return "junior"


def _is_mb_pipeline(name: str | None) -> bool:
    """Mediaboard pipeline: název začíná „MB" — často až po vlajkovém emoji („🇨🇿 MB CZ - Retention")."""
    return re.sub(r"^[^A-Za-z]+", "", name or "").upper().startswith("MB")


def company_status(deals: list[dict]) -> str:
    """Status firmy podle Mediaboard („MB …") pipeline v Pipedrivu.

    Retention pipeline drží stávající klienty: otevřený nebo poslední vyhraný
    retention deal = zákazník, poslední prohraný = churn. Firma bez jakéhokoli
    MB dealu je z pohledu Mediaboardu nepokrytý trh (sdílené CRM s Imperem).
    """
    mb = [d for d in deals if _is_mb_pipeline(d.get("pipeline"))]
    if not mb:
        return "market"
    retention = [d for d in mb if "retention" in (d.get("pipeline") or "").lower()]
    if retention:
        if any(d["status"] == "open" for d in retention):
            return "customer"
        closed = sorted((d for d in retention if d.get("closed_at")), key=lambda d: d["closed_at"])
        if closed:
            return "customer" if closed[-1]["status"] == "won" else "lost"
    if any(d["status"] == "open" for d in mb):
        return "prospect"
    if any(d["status"] == "won" for d in mb):
        return "customer"
    return "lost"


def _recent(closed_at: str | None, months: int) -> bool:
    if not closed_at:
        return False
    try:
        when = datetime.fromisoformat(closed_at[:19])
    except ValueError:
        return False
    return datetime.now() - when < timedelta(days=months * 30)


def score_person(person: dict, company: dict, company_deals: list[dict]) -> tuple[int, str, str]:
    """Vrací (skóre, atribuce, důvod). Pravidla shora, první vyhovující vyhrává."""
    level = seniority(person.get("title"))
    score = {"decision": 30, "mid": 20, "junior": 10}[level]
    score += SEGMENT_FIT.get(company.get("segment"), 10)
    if person.get("email"):
        score += 15
    if person.get("linkedin_url"):
        score += 10
    if person.get("phone"):
        score += 5

    c_status = company.get("status", "market")
    p_status = person.get("status", "market")
    lost_recent = any(d["status"] == "lost" and _recent(d.get("closed_at"), 18) for d in company_deals)
    tool = company.get("monitoring_tool")

    if c_status == "customer":
        score += 20
    if lost_recent:
        score += 15
    if tool and tool.lower() not in ("mediaboard", "žádný", "zadny"):
        score += 10

    score = min(score, 100)

    if p_status == "customer" or (c_status == "customer" and p_status != "market"):
        return score, "Péče & upsell", "Aktivní zákazník — rozšíření licencí a modulů."
    if c_status == "customer":
        return score, "Expanze u zákazníka", f"{company.get('name')} už Mediaboard používá — warm intro přes CS tým."
    if c_status == "lost" or p_status == "lost":
        why = "ztracený deal v posledních 18 měsících" if lost_recent else "starší ztracený deal"
        return score, "Win-back", f"Vrátit se s novinkami v produktu ({why})."
    if c_status == "prospect" and p_status == "market":
        return score, "Multithreading", "Ve firmě běží deal — přidat dalšího stakeholdera."
    if c_status == "prospect":
        return score, "Podpora dealu", "Otevřený deal — držet momentum, další krok v Pipedrivu."
    if tool and tool.lower() not in ("mediaboard", "žádný", "zadny"):
        return score, "Competitive switch", f"Používají {tool} — srovnávací pitch + trial."
    if person.get("linkedin_url") and level == "decision":
        return score, "LinkedIn outreach", "Senior role s LinkedIn profilem — personalizovaný connect."
    if person.get("email"):
        return score, "E-mail sekvence (lemlist)", "Ověřený e-mail — zařadit do segmentované sekvence."
    if person.get("phone"):
        return score, "Telefon", "Máme jen telefon — krátký discovery call."
    return score, "Enrichment", "Chybí kontakt — dohledat e-mail/LinkedIn (Apollo, lemlist)."


def score_company(company: dict, deals: list[dict], people_count: int) -> tuple[int, str, str]:
    score = SEGMENT_FIT.get(company.get("segment"), 10)
    if (company.get("employees") or 0) >= 5:
        score += 10
    if company.get("domain"):
        score += 10
    score += min(people_count * 5, 20)

    status = company.get("status", "market")
    tool = company.get("monitoring_tool")
    lost_recent = any(d["status"] == "lost" and _recent(d.get("closed_at"), 18) for d in deals)
    if status == "customer":
        score += 20
    if lost_recent:
        score += 15
    if tool and tool.lower() not in ("mediaboard", "žádný", "zadny"):
        score += 10
    score = min(score, 100)

    if status == "customer":
        return score, "Péče & upsell", "Zákazník — hlídat adopci, nabídnout další moduly a týmy."
    if status == "lost":
        return score, "Win-back", "Ztracený deal — vrátit se s novou nabídkou."
    if status == "prospect":
        return score, "Podpora dealu", "V CRM — dotáhnout běžící konverzaci."
    if tool and tool.lower() not in ("mediaboard", "žádný", "zadny"):
        return score, "Competitive switch", f"Používají {tool} — srovnávací pitch."
    if people_count == 0:
        return score, "Enrichment", "Nemáme kontakty — dohledat lidi (Apollo, lemlist)."
    return score, "Otevřít konverzaci", "Nepokrytá firma se známými kontakty — první outreach."


def recompute_all(conn):
    """Přepočítá status, skóre a atribuci pro všechny firmy i lidi."""
    companies = {row["id"]: dict(row) for row in conn.execute("SELECT * FROM companies")}
    deals_by_company: dict[int, list[dict]] = {}
    for row in conn.execute("SELECT * FROM deals"):
        deals_by_company.setdefault(row["company_id"], []).append(dict(row))

    for cid, company in companies.items():
        deals = deals_by_company.get(cid, [])
        if company.get("pipedrive_org_id"):
            company["status"] = company_status(deals)
        people_count = conn.execute(
            "SELECT COUNT(*) c FROM people WHERE company_id=?", (cid,)
        ).fetchone()["c"]
        score, approach, reason = score_company(company, deals, people_count)
        conn.execute(
            "UPDATE companies SET status=?, score=?, approach=?, approach_reason=? WHERE id=?",
            (company["status"], score, approach, reason, cid),
        )

    for row in conn.execute("SELECT * FROM people"):
        person = dict(row)
        company = companies.get(person.get("company_id"), {})
        deals = deals_by_company.get(person.get("company_id"), [])
        if person.get("pipedrive_person_id"):
            person["status"] = company.get("status") if company.get("pipedrive_org_id") else "prospect"
        score, approach, reason = score_person(person, company, deals)
        conn.execute(
            "UPDATE people SET status=?, score=?, approach=?, approach_reason=? WHERE id=?",
            (person["status"], score, approach, reason, person["id"]),
        )
    conn.commit()
