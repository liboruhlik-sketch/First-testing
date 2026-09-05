# Report z ostrého testu tokenů a Pipedrive syncu

Datum: 2026-09-05 · Větev: `claude/pipedriveova-trzni-prehled-eyzgoc`

## 1. Přítomnost proměnných prostředí

| Proměnná | Stav |
|---|---|
| `PIPEDRIVE_API_TOKEN` | přítomna |
| `MERK_API_TOKEN` | přítomna |
| `LEMLIST_API_KEY` | přítomna |

## 2. Pipedrive sync

První běh `python -m app.sync_pipedrive` spadl na `sqlite3.IntegrityError: NOT NULL constraint failed: companies.name_norm`. Příčina: jedna organizace s čistě arabským názvem — `normalize_name()` po odstranění diakritiky a ne-ASCII znaků vrátila prázdný řetězec, `insert_row()` prázdné hodnoty zahazuje a NOT NULL sloupec `name_norm` zůstal nevyplněný.

**Oprava** (`app/matching.py`, minimální): když ASCII normalizace vrátí prázdno, `normalize_name()` nově použije jako fallback lowercase původního (ořezaného) názvu. Nelatinkové názvy tak dostanou stabilní normalizační klíč.

Druhý běh doběhl čistě:

```
Hotovo: 86814 organizací, 111473 kontaktů, 57590 dealů.
```

V databázi je po deduplikaci (párování podle domény/názvu) 83 271 firem.

## 3. Data v data/radar.db

### Firmy podle statusu

| Status | Počet |
|---|---:|
| prospect | 61 724 |
| lost | 16 364 |
| customer | 5 183 |

### Lidé podle statusu

| Status | Počet |
|---|---:|
| prospect | 56 374 |
| lost | 22 101 |
| customer | 21 506 |

### Dealy podle statusu

| Status | Počet |
|---|---:|
| lost | 34 692 |
| won | 17 929 |
| open | 4 969 |

### Top 10 lidí podle score

| Jméno | Pozice | Firma | Status | Score | Approach |
|---|---|---|---|---:|---|
| Miroslav Dinga | Managing Partner | DDeM, s.r.o. | customer | 95 | Péče & upsell |
| Pavel Mojžíš | Výkonný ředitel | SVĚT V BEZPEČÍ s.r.o. | customer | 95 | Péče & upsell |
| Žaneta Dlouhá | tisková mluvčí a specialistka komunikace | ELTODO OSVĚTLENÍ, s.r.o. | customer | 95 | Péče & upsell |
| Jan Vavřík | Head of PR | NERUDA PRODUCTION s.r.o. | customer | 95 | Péče & upsell |
| Berenika Alexandre | Head of Communications | Karel Janeček | customer | 95 | Péče & upsell |
| Gabriela Semová | Head of Corporate and Internal PR | FTV Prima, spol. s r.o. | customer | 95 | Péče & upsell |
| Dominika Janik | Senior Account Executive | FLEISHMAN-HILLARD Sp. z o.o. | customer | 95 | Péče & upsell |
| Lucie Gottwaldová | Head of Customer Experience | TV Nova s.r.o. | customer | 95 | Péče & upsell |
| Matylda Pietrykowska | Junior Account Executive | PR HUB Sp. z o.o. | customer | 95 | Péče & upsell |
| Nikola Vangeli | Marketingový ředitel | MAFRA, a.s. | customer | 95 | Péče & upsell |

### Vyplněnost custom fieldů (kontrola mapování `DEFAULT_ORG_FIELDS`)

| Pole | Vyplněno | Podíl |
|---|---:|---:|
| ico | 79 558 / 83 271 | 96 % |
| domain | 55 427 / 83 271 | 67 % |
| segment | 69 240 / 83 271 | 83 % |
| employees | 52 430 / 83 271 | 63 % |

Mapování custom fieldů funguje — `cf()` nebylo potřeba upravovat.

## 4. Merk API

- `Authorization: Token <MERK_API_TOKEN>` header → **200** (na `/company/?regno=…&country_code=cz` i na kořeni API).
- Token jako query parametr (`?token=…`) → 401.

Tvar odpovědi (jedna řádka): JSON pole s 1 položkou (záznam firmy); klíče položky mj. `address`, `bank_accounts`, `categories`, `company_index`, `court`, `databox_ids`, `emails`, `regno`, …

## 5. Lemlist API

`curl -u ":<LEMLIST_API_KEY>" https://api.lemlist.com/api/team` → **200**.

## Shrnutí

Všechny tři tokeny fungují. Pipedrive sync běží po jednořádkové opravě `normalize_name()`; databáze je naplněná a mapování custom fieldů je v pořádku. Merk vyžaduje auth přes header `Authorization: Token …`, Lemlist přes HTTP Basic (prázdný user, klíč jako heslo).
