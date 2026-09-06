# Report: statusy podle Mediaboard pipeline

Datum: 2026-09-06 · Větev: `claude/pipedriveova-trzni-prehled-eyzgoc`

Ostrý sync z Pipedrive (API v2) doběhl čistě:

```
Hotovo: 86814 organizací, 111473 kontaktů, 57590 dealů.
```

Po deduplikaci je v `data/radar.db` 83 271 firem. Endpoint `/api/v2/pipelines` vrací očekávaný tvar (`data: [{id, name, …}]`), takže `app/sync_pipedrive.py` nebylo potřeba upravovat — **všech 57 590 dealů má vyplněný název pipeline** (kontrola: `filled = 57 590 / 57 590`).

## 1. Přehled pipeline (unikátní názvy + počty dealů)

MB pipeline jsou v tabulce tučně. Pozor: názvy nezačínají doslova na „MB" — mají prefix vlajkového emoji (viz Poznámky).

| Pipeline | Dealů |
|---|---:|
| **🇨🇿 MB CZ - New clients** | 12 900 |
| Leadgen | 10 252 |
| Imper CZ | 7 025 |
| Retence | 6 662 |
| **🇨🇿 MB CZ - Retention** | 3 706 |
| Partneri | 3 047 |
| IMPER_Up-sell/Cross- sell | 2 364 |
| Registrations Mediaboard Global | 2 093 |
| **🇵🇱 MB PL - New clients** | 1 897 |
| Imper SK | 1 114 |
| **🇸🇰 MB SK - Retention** | 1 050 |
| **🇸🇮 MB SLO - New clients** | 791 |
| **🇸🇰 MB SK - New clients** | 785 |
| **🇭🇷 MB HR - New clients** | 780 |
| Spoluprace | 711 |
| **🇵🇱 MB PL - Retention** | 605 |
| Mediaboard Global | 554 |
| **MB_upsell_CZ** | 347 |
| Vydavatelé | 337 |
| Registrace Imper SK | 248 |
| **🇭🇷 MB HR - Retention** | 178 |
| **MB Data & MMOs** | 76 |
| SLPV_dočasná | 51 |
| Sales process 2.0 | 13 |
| Pipeline | 3 |
| BDR + Mediaboard CZ | 1 |

Celkem 26 pipeline; jako Mediaboard („MB …") se počítá 11 z nich s **23 115 dealy** (40 % všech dealů). Zbytek jsou pipeline Imperu a sdílené procesní pipeline.

## 2. Statusy firem a lidí

| Status | Firmy | Lidé |
|---|---:|---:|
| market | 72 692 | 48 555 |
| lost | 6 847 | 16 015 |
| customer | 2 393 | 11 100 |
| prospect | 1 339 | 24 311 |
| **celkem** | **83 271** | **99 981** |

Logika: firma s dealem v MB Retention pipeline (otevřeným, nebo posledním vyhraným) = `customer`; poslední prohraný retention = `lost`; otevřený MB deal mimo retention = `prospect`; firma bez jakéhokoli MB dealu = `market` (nepokrytý trh — sdílené CRM s Imperem). Lidé dědí status své firmy.

## 3. Top zákazníci (customer firmy podle score)

Firem se statusem **customer je 2 393**. Prvních 15 podle score (všechny sdílejí maximum 85, řazeno abecedně; sloupec země je prázdný — viz Poznámky):

| Firma | Země | Segment | Score |
|---|---|---|---:|
| "GREENPEACE Slovensko" | — | Činnosti ostatných členských organizácií | 85 |
| ABB, s.r.o. | — | Inštalácia priemyselných strojov a prístrojov | 85 |
| ABS Jets, a.s. | — | Mezinárodní nepravidelná letecká osobní doprava | 85 |
| AC & C, Public Relations, s.r.o. | — | Vydávání knih, periodických publikací a ostatní vydavatelské činnosti | 85 |
| ADRA, o.p.s. | — | Ostatní ambulantní nebo terénní sociální služby j. n. | 85 |
| AKCENTA CZ a.s. | — | Obchodování s cennými papíry na vlastní účet | 85 |
| ALENSA, s.r.o. | — | Ostatní maloobchod s novým zbožím ve specializovaných prodejnách | 85 |
| AMI Communications Group SE | — | Pronájem a správa vlastních nebo pronajatých nemovitostí | 85 |
| AVANT investiční společnost, a.s. | — | Činnosti trustů, fondů a podobných finančních subjektů | 85 |
| Agentura pro podporu podnikání a investic CzechInvest | — | Ostatní poradenství v oblasti podnikání a řízení | 85 |
| Air Bank a.s. | — | Ostatní peněžní zprostředkování | 85 |
| Albatros Media a.s. | — | Vydávání knih | 85 |
| Algotech, a.s. | — | Činnosti v oblasti informačních technologií | 85 |
| Amundi Czech Republic, investiční společnost, a.s. | — | Správa fondů | 85 |
| Armáda spásy - misijní | — | Činnosti náboženských organizací | 85 |

## 4. Top nepokrytí lidé (status market podle score)

Nejzajímavější kontakty, na které se z pohledu Mediaboardu zatím nesahá (jejich firma nemá žádný MB deal):

| Jméno | Pozice | Firma | Score | Approach |
|---|---|---|---:|---|
| Amine Kecha | Head of Intelligence & Offensive Security | Devoteam | 75 | E-mail sekvence (lemlist) |
| Agnes Dancs | CEO Assistant | Nitrogenmuvek Zrt. | 60 | E-mail sekvence (lemlist) |
| Andras R Nagy | managing director | PRBK Communications | 60 | E-mail sekvence (lemlist) |
| Anne Gayat | Co CEO | EsterLaw | 60 | E-mail sekvence (lemlist) |
| Anthony Lam | Head of Account Management | Orbit Dot Limited | 60 | E-mail sekvence (lemlist) |
| Beata Móriová | Head of Marketing Nivy Mall and PR Manager | Stanica Nivy s. r. o. | 60 | E-mail sekvence (lemlist) |
| Bogdan Berceanu | CEO | Editia de Timis | 60 | E-mail sekvence (lemlist) |
| Catalina Ionescu | CEO | InteliPR SRL | 60 | E-mail sekvence (lemlist) |
| Cristopher Ugarte | CEO | Puente OS | 60 | E-mail sekvence (lemlist) |
| Damian Juszczyk | Founder & CEO | EXECUTIVE PR Damian Juszczyk | 60 | E-mail sekvence (lemlist) |
| Diego Lorenzo | Ceo | Xngroup | 60 | E-mail sekvence (lemlist) |
| Doreen Faith Motshegwa | Chief Public Relations Officer | Government Communication | 60 | E-mail sekvence (lemlist) |
| Heiko Loy | Head of PR | PEARL GmbH | 60 | E-mail sekvence (lemlist) |
| Jan Ursíny | Director Czech Republic | Switzerland Tourism | 60 | E-mail sekvence (lemlist) |
| John Smith | CEO | The Testing LTD | 60 | E-mail sekvence (lemlist) |

Všichni mají decision-maker pozici a ověřený e-mail, proto approach „E-mail sekvence (lemlist)". Mnoho z nich je mimo CZ/SK (HU, PL, RO, DE, …) — CRM obsahuje i globální leady.

## 5. Poznámky k opravám a limitům

1. **Oprava detekce MB pipeline** (`app/scoring.py`, commit „Detekce MB pipeline i s vlajkovým emoji prefixem"): pipeline se nejmenují doslova „MB …", ale „🇨🇿 MB CZ - Retention" apod. Původní `startswith("MB")` chytal jen `MB_upsell_CZ` a `MB Data & MMOs` (výsledkem bylo jen 187 zákazníků). Nová detekce před testem prefixu odstraní úvodní ne-písmenné znaky (emoji, mezery); po opravě a přepočtu je zákazníků 2 393.
2. **`app/sync_pipedrive.py` beze změny** — `/api/v2/pipelines` vrací standardní v2 tvar, mapování `pipeline_id → name` funguje a pipeline je vyplněná u 100 % dealů.
3. **Pipeline „Mediaboard Global" a „Registrations Mediaboard Global"** (554 + 2 093 dealů) konvenci „MB …" nesplňují, a proto se do statusů **nepočítají**. Pokud jde o skutečné Mediaboard pipeline, je potřeba je do detekce doplnit (nebo je v Pipedrivu přejmenovat) — počty prospect/customer by pak narostly.
4. **Země u firem prakticky chybí**: vyplněná jen u 46 z 83 271 firem — adresní pole `address.country` se v Pipedrivu skoro nepoužívá. Proto je sloupec Země v top zákaznících prázdný; do budoucna lze zemi odvozovat z měny dealu nebo MB pipeline (CZ/SK/PL/SLO/HR).
5. Mezi top „market" lidmi jsou i zjevně testovací záznamy (např. „John Smith / The Testing LTD") — CRM by zasloužilo úklid.

## Export pro online dashboard

**Datum:** 6. 9. 2026

Ostrý sync z Pipedrivu a export kurátorovaného výběru pro online dashboard (`data/export/radar_slice.json`).

**Sync (zdroj, plná databáze `data/radar.db`, necommituje se):**
- 86 814 organizací, 111 473 kontaktů, 57 590 dealů z Pipedrivu.
- Po zpracování: 83 271 firem (2 393 customer / 1 339 prospect / 6 847 lost / 72 692 market) a 99 981 lidí (11 100 / 24 311 / 16 015 / 48 555).

**Export (`radar_slice.json`, commitnutý ve větvi):**
- 14 442 firem a 23 500 lidí, velikost 11,8 MB (12 584 872 B by původní limit 15k/25k překročil 12 MB, proto limity výběru sníženy na 14 000 firem / 23 500 lidí v `app/export_slice.py`).
- Výběr: všechny firmy se vztahem (customer/prospect/lost), z nepokrytého trhu nejdřív relevantní obory (PR/komunikace/média) a pak nejvyšší skóre; top lidé podle skóre + firmy zmíněných lidí.
- Ověřeno: validní JSON, `meta.slice` = {companies: 14442, companies_total: 83271, people: 23500, people_total: 99981}.
