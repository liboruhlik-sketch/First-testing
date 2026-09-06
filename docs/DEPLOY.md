# Nasazení Market Radaru na vlastní URL s Google přihlášením

Cíl: `https://radar.mediaboard.com` (nebo jiná adresa), dostupné jen lidem
s Google účtem `@mediaboard.com`. Doporučená sestava: **Fly.io** (hosting
aplikace, ~5 min setup) + **Cloudflare Access** (přihlášení přes Google,
zdarma do 50 uživatelů). Aplikace sama pak nepotřebuje žádný vlastní login kód.

## 1. Hosting na Fly.io (jednorázově ~10 minut)

```bash
# instalace CLI a účet (platební karta je potřeba, provoz vyjde na ~2-5 USD/měsíc)
curl -L https://fly.io/install.sh | sh
fly auth signup            # nebo fly auth login

# z kořene repozitáře (Dockerfile a fly.toml už tu jsou)
fly launch --no-deploy     # potvrdit existující fly.toml, název appky, region fra
fly volumes create radar_data --size 3 --region fra

# tajemství — tokeny nikdy nepatří do gitu
fly secrets set PIPEDRIVE_API_TOKEN=… MERK_API_TOKEN=… LEMLIST_API_KEY=…
# záložní zámek, dokud nebude zapnutý Cloudflare Access:
fly secrets set RADAR_PASSWORD=silné-heslo

fly deploy
```

První naplnění a průběžná aktualizace dat (spouští sync uvnitř stroje):

```bash
fly ssh console -C "python -m app.sync_pipedrive"
```

Automatizace: `fly machines` cron, GitHub Action na plánu, nebo Routine —
zatím stačí ručně jednou za den/týden.

## 2. Google přihlášení jen pro @mediaboard.com (Cloudflare Access)

Předpoklad: doména mediaboard.com (nebo aspoň subdoména) je v Cloudflare.

1. Cloudflare dashboard → **Zero Trust** (one.dash.cloudflare.com) → založit
   tým (Free plán stačí, do 50 uživatelů zdarma).
2. **Settings → Authentication → Login methods → Add new → Google** — návod
   provede založením OAuth klienta v Google Cloud Console (10 kliků).
3. DNS: `radar.mediaboard.com` → CNAME na `mediaboard-market-radar.fly.dev`,
   proxy zapnutá (oranžový mráček). Ve Fly: `fly certs add radar.mediaboard.com`.
4. **Access → Applications → Add application → Self-hosted**:
   - doména: `radar.mediaboard.com`
   - policy „Mediaboard only": *Allow* → include → **Emails ending in**
     `@mediaboard.com`, login method Google.
5. Otestovat z anonymního okna: musí vynutit Google login a pustit jen
   firemní účet. Pak je možné `RADAR_PASSWORD` vypnout (`fly secrets unset
   RADAR_PASSWORD`), nebo ho nechat jako druhou vrstvu.

Poznámka: dokud běží jen Fly bez Cloudflare, aplikaci chrání `RADAR_PASSWORD`
(HTTP Basic) — nasdílet jde i tak, ale všichni sdílejí jedno heslo, takže to
berte jen jako přechodné řešení.

## Alternativy

- **Google Cloud Run + IAP** — totéž v Google ekosystému; víc kroků, login
  řeší Google Identity-Aware Proxy, vhodné pokud firma žije v GCP.
- **Railway/Render** — podobné Fly.io; Access od Cloudflare funguje stejně.

## Co je hotové v repozitáři

- `Dockerfile` — kontejner aplikace (uvicorn na :8080, DB na /data).
- `fly.toml` — konfigurace Fly.io (Frankfurt, persistentní svazek, HTTPS).
- HTTP Basic fallback (`RADAR_PASSWORD`/`RADAR_USER`) v `app/main.py`.
