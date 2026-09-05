# Market Radar — návrh

Cíl: mít na jednom místě **celý adresovatelný trh Mediaboardu** (PR profesionálové —
agentury, in-house komunikační týmy, public affairs, tiskoví mluvčí) a u každé firmy
i člověka vědět:

1. **Kde stojí vůči nám** — zákazník / prospekt / ztracený / zatím bez kontaktu.
2. **Jak je pro nás zajímavý** — priorita 0–100 (ICP fit + dosažitelnost + „teplota").
3. **Kudy na něj jít** — doporučený kanál a hra (warm intro, win-back, lemlist sekvence…).

## Princip

```
   Pipedrive (pravda o vztahu)          Tržní databáze (pravda o trhu)
   organizace / kontakty / dealy        Apollo, lemlist People DB, CSV exporty,
            │                           asociace (APRA, PRCA…), ARES/Merk, eventy
            └──────────┬────────────────┘
                       ▼
              MATCHING & DEDUP  (doména → název firmy; e-mail → jméno+firma)
                       ▼
              STATUS + SCORING + ATRIBUCE  (pravidla v app/scoring.py)
                       ▼
              DASHBOARD  (seřazený přehled lidí a firem, filtry, detail)
```

Klíčová myšlenka: **Pipedrive nikdy není celý trh.** Trh nasáváme z externích zdrojů,
párujeme na Pipedrive, a co se nespáruje, je „nepokrytý trh" — právě ten chceme vidět.

## Datové zdroje

### CRM (zdroj pravdy o vztahu)
- **Pipedrive API** — `organizations`, `persons`, `deals`. Sync je idempotentní
  (párování přes `pipedrive_org_id` / `pipedrive_person_id`), stačí API token.

### Trh (zdroj pravdy o existenci firem a lidí)
| Zdroj | Co dá | Poznámka |
|---|---|---|
| **lemlist People Database** | lidé + firmy s ověřenými e-maily, filtry na roli/zemi | už ho máme, přirozeně navazuje na outreach |
| **Apollo.io** | největší pokrytí rolí typu „PR / Communications", export CSV i API | `import_market.py` mapuje jeho hlavičky rovnou |
| **Cognism / Kaspr** | kvalitní EU data, telefony, GDPR compliance | dražší, vhodné na dočištění |
| **ARES / Merk (CZ)** | úplný seznam českých firem podle NACE (70.21 – PR a komunikace) | základ pro úplnost CZ trhu |
| **Asociace a žebříčky** | APRA, PR Klub, ICCO/PRCA členské seznamy, žebříčky agentur | malé, ale 100% relevantní seznamy |
| **Eventy** | PR summity, marketingové konference — seznamy řečníků/partnerů | silný signál záměru |
| **Mediaboard sám** | naše mediální data: kdo je citovaný jako mluvčí, která agentura zastupuje kterého klienta | **proprietární signál, který konkurence nemá** — fáze 3 |

**LinkedIn:** přímý scraping porušuje podmínky LinkedInu — nedělat. Stejná data
legálně dodávají licencovaní poskytovatelé výše (Apollo, Cognism…); LinkedIn URL
u kontaktu ale evidujeme a používáme jako outreach kanál (Sales Navigator ručně).

## Datový model (SQLite v prototypu, později Postgres)

- **companies** — název (+ normalizovaný), doména, země, segment, velikost,
  `pipedrive_org_id`, status, monitorovací nástroj (konkurence), zdroje, skóre, atribuce.
- **people** — jméno (+ normalizované), pozice, seniorita, e-mail, telefon, LinkedIn,
  vazba na firmu, `pipedrive_person_id`, status, zdroje, skóre, atribuce.
- **deals** — zrcadlo Pipedrive dealů (open/won/lost) — z nich se počítá status.
- `sources` je množina („pipedrive,apollo,apra") — vidíme, odkud záznam známe,
  a záznam z více zdrojů = vyšší důvěra.

## Matching & dedup

Pořadí pravidel (první shoda vyhrává):

1. **Firma:** `pipedrive_org_id` → **doména** (bez www, lowercase) → **normalizovaný
   název** (bez diakritiky, bez právních forem s.r.o./a.s./GmbH/Ltd…).
2. **Člověk:** `pipedrive_person_id` → **e-mail** (lowercase) → **normalizované jméno
   + stejná firma**.

Při shodě se záznamy **slévají**: doplní se chybějící pole (nikdy se nepřepisuje
Pipedrive hodnota tržní hodnotou) a sjednotí `sources`.

## Statusová logika

| Status | Pravidlo |
|---|---|
| **Zákazník** | firma má won deal (a není označená churn) |
| **Prospekt** | otevřený deal, nebo je v Pipedrivu bez dealu (jsme v kontaktu) |
| **Ztracený** | pouze lost dealy |
| **Nepokrytý trh** | známe jen z tržních zdrojů, v Pipedrivu není |

Člověk dědí status firmy, pokud sám nemá vlastní záznam v Pipedrivu; člověk bez
Pipedrive záznamu u zákaznické firmy je „nepokrytý" — to je **expanzní příležitost**.

## Skóre priority (0–100) a atribuce „kudy na ně"

Verze 1 je záměrně **pravidlová a čitelná** (žádná černá skříňka — obchodník musí
rozumět, proč je někdo nahoře). Složky:

- **ICP fit** — role (ředitel komunikace > manažer > specialista), segment
  (PR agentura, in-house tým…), velikost firmy.
- **Dosažitelnost** — ověřený e-mail, LinkedIn, telefon.
- **Teplota** — kolega už je zákazník (warm intro), ztracený deal < 18 měsíců
  (win-back okno), známý konkurenční nástroj (switch pitch), shodný segment
  s existujícím zákazníkem (reference).

Atribuce je první vyhovující pravidlo shora:

1. zákazník → **Péče & upsell**
2. nepokrytý člověk u zákaznické firmy → **Expanze u zákazníka** (intro přes CS)
3. ztracený → **Win-back**
4. běžící deal → **Multithreading** (další stakeholder do dealu)
5. známá konkurence → **Competitive switch**
6. senior + LinkedIn → **LinkedIn outreach**
7. e-mail → **E-mail sekvence (lemlist)**
8. telefon → **Telefon**
9. nic → **Enrichment** (nejdřív dohledat kontakt)

Verze 2 přidá živé signály: změna práce (nový Head of Comms = 90denní okno),
výhra tendru agenturou, mediální aktivita firmy z dat Mediaboardu.

## Roadmap

- **F0 (tento prototyp):** datový model, matching, scoring, dashboard, Pipedrive
  sync, CSV import, demo data.
- **F1:** napojení na reálný Pipedrive účet, první plný import trhu
  (ARES NACE 70.21 + Apollo/lemlist pro role), ruční validace matchingu.
- **F2:** smyčka do outreache — výběr segmentu v Radaru → push do lemlist kampaně;
  zpětný zápis výsledků (odpověděl/unsubscribe) do skóre.
- **F3:** proprietární signály z Mediaboard dat (mluvčí v médiích, agentura–klient
  vztahy), job-change tracking, notifikace.
- **F4:** Postgres, auth, hosting, více uživatelů, práva.

## Security

Radar drží osobní údaje kontaktů a obchodní data — zabezpečení roste s tím, kde běží:

**Teď (prototyp, běží lokálně):**
- Databáze i API klíče zůstávají na jednom stroji; `data/radar.db` je v `.gitignore`,
  tokeny se čtou výhradně z env proměnných — nikdy je nedávat do kódu ani do gitu.
- Zapnutí přihlášení: `export RADAR_PASSWORD=silné-heslo` (uživatel `RADAR_USER`,
  výchozí „mediaboard") — celá aplikace pak vyžaduje HTTP Basic login.

**Až se bude hostovat (F4):**
1. **HTTPS vždy** — provozovat jen za reverse proxy s TLS (Caddy/nginx, nebo
   platforma typu Fly.io/Railway, která TLS řeší sama).
2. **Přihlášení přes firemní Google** — místo Basic auth dát aplikaci za
   Cloudflare Access nebo Google Identity-Aware Proxy: nulový kód, MFA zdarma,
   přístup jen pro @mediaboard.com účty a centrální odebrání přístupu.
3. **Tokeny do secret manageru** hostingu (ne do souborů na disku).
4. **Postgres místo SQLite** s vlastním DB uživatelem a zálohami.
5. **Audit log** — kdo se přihlásil a kdy (řeší Cloudflare Access samo).
6. **Rate limit a timeouty** na API, ať náhodný sken internetu nic nevytáhne.

Zásada: aplikace nikdy nesmí být na veřejné adrese bez bodů 1+2.

## GDPR poznámka

Jde o B2B prospecting na pracovní kontakty — opíráme se o oprávněný zájem, ale:
evidovat zdroj každého kontaktu (`sources` to už dělá), respektovat opt-out
(lemlist unsubscribe propsat zpět), neimportovat citlivé údaje, mít proces smazání.
