# Market Radar

Interní nástroj Mediaboardu: mapa celého trhu PR profesionálů (firmy i lidé),
propojená s Pipedrivem. Každá firma a každý člověk na trhu má status
**zákazník / prospekt / ztracený / nepokrytý trh** a doporučení, **kudy na něj jít**.

Kompletní návrh a architektura: [docs/NAVRH.md](docs/NAVRH.md)

## Rychlé spuštění (prototyp)

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# 1) naplnit demo daty (fiktivní trh, ~14 firem / ~24 lidí)
python -m app.demo_seed

# 2) nebo napojit reálný Pipedrive
export PIPEDRIVE_API_TOKEN=xxx           # Pipedrive → Settings → Personal → API
python -m app.sync_pipedrive

# 3) import tržních dat z CSV (Apollo / lemlist / ruční export)
python -m app.import_market companies data/samples/market_companies.csv --source apollo
python -m app.import_market people    data/samples/market_people.csv    --source apollo

# 4) spustit dashboard
uvicorn app.main:app --reload
# → http://localhost:8000

# volitelně: schovat aplikaci za přihlášení (HTTP Basic)
export RADAR_PASSWORD=silné-heslo   # uživatel: mediaboard (změna přes RADAR_USER)
```

Frontend (`app/static/index.html`) funguje i samostatně bez backendu —
má v sobě zabudovaný demo snapshot, takže jde otevřít přímo v prohlížeči.

## Struktura

| Cesta | Účel |
|---|---|
| `app/db.py` | SQLite schéma + upserty |
| `app/matching.py` | normalizace, deduplikace (doména → název, e-mail → jméno+firma) |
| `app/scoring.py` | statusová logika, priorita 0–100, atribuce „kudy na ně" |
| `app/sync_pipedrive.py` | sync organizací, kontaktů a dealů z Pipedrive API |
| `app/import_market.py` | CSV import tržních dat (mapuje i hlavičky Apollo exportu) |
| `app/demo_seed.py` | fiktivní demo dataset |
| `app/main.py` | FastAPI — `/api/data` + statický dashboard |
| `app/static/index.html` | dashboard (jeden soubor, bez build kroku) |
