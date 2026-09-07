# -*- coding: utf-8 -*-
import json, os, sys, time, urllib.parse, urllib.request

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from items import ITEMS

CACHE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "geocache.json")
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "points.json")
cache = json.load(open(CACHE)) if os.path.exists(CACHE) else {}

# viewbox Prahy (lon1,lat1,lon2,lat2), bounded=1 -> jen výsledky uvnitř
VIEWBOX = "14.20,50.20,14.75,49.93"

def geocode(q):
    if q in cache:
        return cache[q]
    url = ("https://nominatim.openstreetmap.org/search?format=json&limit=1&bounded=1"
           f"&viewbox={VIEWBOX}&q=" + urllib.parse.quote(q + ", Praha"))
    req = urllib.request.Request(url, headers={"User-Agent": "prague-speed-map/1.0 (one-off)"})
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            data = json.loads(r.read().decode())
    except Exception as e:
        print(f"  ERR {q}: {e}", flush=True)
        return None
    time.sleep(1.15)
    res = None
    if data:
        res = {"lat": float(data[0]["lat"]), "lon": float(data[0]["lon"]),
               "name": data[0]["display_name"].split(",")[0]}
    cache[q] = res
    json.dump(cache, open(CACHE, "w"), ensure_ascii=False)
    return res

points = []
missing = []
for it in ITEMS:
    if "fix" in it:
        lat, lon = it["fix"]
        src = "fix"
    else:
        found = []
        for q in it["q"]:
            r = geocode(q)
            if r:
                found.append(r)
        if not found:
            missing.append(it["n"])
            print(f"MISSING #{it['n']} {it['t']} ({it['q']})", flush=True)
            continue
        lat = sum(f["lat"] for f in found) / len(found)
        lon = sum(f["lon"] for f in found) / len(found)
        src = ";".join(f["name"] for f in found)
    if "off" in it:
        de, dn = it["off"]
        lat += dn / 111320.0
        lon += de / (111320.0 * 0.6428)
    points.append({"n": it["n"], "cat": it["cat"], "mc": it["mc"], "t": it["t"],
                   "d": it["d"], "lat": round(lat, 6), "lon": round(lon, 6), "src": src})
    print(f"#{it['n']:>3} {it['t']:<40} {lat:.5f},{lon:.5f}  [{src[:60]}]", flush=True)

json.dump(points, open(OUT, "w"), ensure_ascii=False, indent=1)
print(f"\nDONE: {len(points)} points, missing: {missing}", flush=True)
