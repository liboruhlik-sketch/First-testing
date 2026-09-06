"""Fiktivní demo dataset — malý výsek trhu PR profesionálů (CZ/SK + okolí).

Všechny firmy i osoby jsou smyšlené. Použití: python -m app.demo_seed
"""

from .db import DB_PATH, connect
from .matching import upsert_company, upsert_person
from .scoring import recompute_all

# (název, doména, země, město, segment, zaměstnanci, nástroj, pipedrive_org_id, zdroj)
COMPANIES = [
    ("Bluenote Communications", "bluenote.cz", "Česko", "Praha", "PR agentura", 35, "Mediaboard", 101, "pipedrive"),
    ("Vltava PR", "vltavapr.cz", "Česko", "Praha", "PR agentura", 18, "Mediaboard", 102, "pipedrive"),
    ("Helios Energy", "heliosenergy.cz", "Česko", "Praha", "In-house komunikace", 850, "Mediaboard", 103, "pipedrive"),
    ("Orbis Media Relations", "orbismedia.cz", "Česko", "Brno", "PR agentura", 22, "Monitora", 104, "pipedrive"),
    ("Skylark PR Partners", "skylarkpr.sk", "Slovensko", "Bratislava", "PR agentura", 14, None, 105, "pipedrive"),
    ("Nordwind Software", "nordwind.io", "Česko", "Praha", "In-house komunikace", 320, "žádný", 106, "pipedrive"),
    ("Granit Corporate Affairs", "granitca.cz", "Česko", "Praha", "Public affairs", 12, "Newton Media", 107, "pipedrive"),
    ("Aurora Public Affairs", "aurorapa.at", "Rakousko", "Vídeň", "Public affairs", 25, "Meltwater", None, "apollo"),
    ("Wisła Communications", "wislacomms.pl", "Polsko", "Varšava", "PR agentura", 40, "Meltwater", None, "apollo"),
    ("Redwood & Steiner", "redwoodsteiner.de", "Německo", "Mnichov", "PR agentura", 60, None, None, "apollo"),
    ("Ateliér Komunikace", "atelierkomunikace.cz", "Česko", "Ostrava", "PR agentura", 8, "žádný", None, "apra"),
    ("Lumen Health PR", "lumenhealth.cz", "Česko", "Praha", "PR agentura", 11, "Newton Media", None, "apra"),
    ("Signum Crisis Management", "signumcrisis.cz", "Česko", "Praha", "PR agentura", 6, None, None, "lemlist"),
    ("Danube Media House", "danubemedia.sk", "Slovensko", "Bratislava", "PR agentura", 19, "Monitora", None, "lemlist"),
]

# (jméno, pozice, firma-doména, e-mail, telefon, linkedin, pipedrive_person_id, zdroj)
PEOPLE = [
    ("Jana Skalická", "Managing Director", "bluenote.cz", "jana.skalicka@bluenote.cz", "+420601111222", "linkedin.com/in/janaskalicka", 201, "pipedrive"),
    ("Tomáš Vrba", "Account Director", "bluenote.cz", "tomas.vrba@bluenote.cz", None, "linkedin.com/in/tomasvrba", 202, "pipedrive"),
    ("Klára Dunková", "Head of Digital", "bluenote.cz", None, None, "linkedin.com/in/klaradunkova", None, "apollo"),
    ("Petr Hájenka", "CEO", "vltavapr.cz", "petr@vltavapr.cz", "+420602333444", None, 203, "pipedrive"),
    ("Alice Zimová", "Senior PR Manager", "vltavapr.cz", "alice.zimova@vltavapr.cz", None, "linkedin.com/in/alicezimova", None, "lemlist"),
    ("Marek Louda", "Ředitel komunikace", "heliosenergy.cz", "marek.louda@heliosenergy.cz", "+420603555666", "linkedin.com/in/marekloud", 204, "pipedrive"),
    ("Eva Krásová", "Tisková mluvčí", "heliosenergy.cz", None, None, "linkedin.com/in/evakrasova", None, "apollo"),
    ("Filip Otava", "Managing Partner", "orbismedia.cz", "filip.otava@orbismedia.cz", None, "linkedin.com/in/filipotava", 205, "pipedrive"),
    ("Lucie Bártová", "PR Specialist", "orbismedia.cz", "lucie.bartova@orbismedia.cz", None, None, None, "apollo"),
    ("Zuzana Kováčová", "Head of Communications", "skylarkpr.sk", "zuzana@skylarkpr.sk", None, "linkedin.com/in/zuzanakovacova", 206, "pipedrive"),
    ("Milan Hruška", "Account Manager", "skylarkpr.sk", None, None, "linkedin.com/in/milanhruska", None, "lemlist"),
    ("Barbora Nguyen", "Communications Lead", "nordwind.io", "barbora.nguyen@nordwind.io", None, "linkedin.com/in/barboranguyen", 207, "pipedrive"),
    ("Ondřej Šindel", "Managing Partner", "granitca.cz", "ondrej.sindel@granitca.cz", "+420604777888", None, 208, "pipedrive"),
    ("Ingrid Bauer", "Managing Director", "aurorapa.at", "i.bauer@aurorapa.at", None, "linkedin.com/in/ingridbauer", None, "apollo"),
    ("Stefan Krall", "Senior Consultant", "aurorapa.at", None, None, "linkedin.com/in/stefankrall", None, "apollo"),
    ("Agnieszka Wolska", "Head of Media Relations", "wislacomms.pl", "a.wolska@wislacomms.pl", None, "linkedin.com/in/agnieszkawolska", None, "apollo"),
    ("Paweł Zieliński", "PR Executive", "wislacomms.pl", None, None, None, None, "apollo"),
    ("Ute Steiner", "Managing Partner", "redwoodsteiner.de", "steiner@redwoodsteiner.de", None, "linkedin.com/in/utesteiner", None, "apollo"),
    ("Jonas Beck", "Communications Manager", "redwoodsteiner.de", None, None, "linkedin.com/in/jonasbeck", None, "apollo"),
    ("Radka Přibylová", "Majitelka & PR ředitelka", "atelierkomunikace.cz", "radka@atelierkomunikace.cz", "+420605999000", None, None, "apra"),
    ("Vojtěch Malík", "Managing Director", "lumenhealth.cz", "vojtech.malik@lumenhealth.cz", None, "linkedin.com/in/vojtechmalik", None, "apra"),
    ("Šárka Rosová", "Healthcare PR Manager", "lumenhealth.cz", None, None, "linkedin.com/in/sarkarosova", None, "apra"),
    ("David Signer", "Crisis Director", "signumcrisis.cz", None, None, None, None, "lemlist"),
    ("Nina Ďurišová", "Head of Client Service", "danubemedia.sk", "nina@danubemedia.sk", None, "linkedin.com/in/ninadurisova", None, "lemlist"),
]

# (pipedrive_deal_id, firma-doména, titul, pipeline, status, hodnota, uzavřeno)
DEALS = [
    (301, "bluenote.cz", "Mediaboard licence 2025", "MB CZ - New clients", "won", 96000, "2025-01-15"),
    (308, "bluenote.cz", "Obnova 2026", "MB CZ - Retention", "open", 102000, None),
    (302, "vltavapr.cz", "Obnova licence 2026", "MB CZ - Retention", "won", 54000, "2025-11-02"),
    (303, "heliosenergy.cz", "Enterprise obnova", "MB CZ - Retention", "open", 180000, None),
    (304, "orbismedia.cz", "Nabídka pro Orbis", "MB CZ - New clients", "open", 60000, None),
    (305, "skylarkpr.sk", "Skylark trial → licence", "MB SK - New clients", "open", 42000, None),
    (306, "nordwind.io", "Nordwind — pilot", "MB CZ - New clients", "open", 75000, None),
    (307, "granitca.cz", "Granit licence", "MB CZ - New clients", "lost", 48000, "2026-02-10"),
]


def run() -> None:
    if DB_PATH.exists():
        DB_PATH.unlink()
    conn = connect()

    company_ids: dict[str, int] = {}
    for name, domain, country, city, segment, employees, tool, pd_org, source in COMPANIES:
        company_ids[domain] = upsert_company(
            conn,
            {
                "name": name, "domain": domain, "country": country, "city": city,
                "segment": segment, "employees": employees, "monitoring_tool": tool,
                "pipedrive_org_id": pd_org,
                "linkedin_url": f"linkedin.com/company/{domain.split('.')[0]}",
            },
            source=source,
        )

    for full_name, title, domain, email, phone, linkedin, pd_person, source in PEOPLE:
        upsert_person(
            conn,
            {
                "full_name": full_name, "title": title, "email": email, "phone": phone,
                "linkedin_url": linkedin, "company_id": company_ids[domain],
                "pipedrive_person_id": pd_person,
            },
            source=source,
        )

    for pd_deal, domain, title, pipeline, status, value, closed_at in DEALS:
        conn.execute(
            "INSERT INTO deals (pipedrive_deal_id, company_id, title, pipeline, status, value, currency, closed_at)"
            " VALUES (?,?,?,?,?,?,?,?)",
            (pd_deal, company_ids[domain], title, pipeline, status, value, "CZK", closed_at),
        )

    recompute_all(conn)
    conn.commit()
    print(f"Demo data nahrána do {DB_PATH}: {len(COMPANIES)} firem, {len(PEOPLE)} lidí, {len(DEALS)} dealů.")


if __name__ == "__main__":
    run()
