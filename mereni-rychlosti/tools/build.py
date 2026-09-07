# -*- coding: utf-8 -*-
import base64, json, math, os

d = os.path.dirname(os.path.abspath(__file__))
meta = json.load(open(os.path.join(d, "tilemeta.json")))
pts = json.load(open(os.path.join(d, "points.json")))

Z, X1, Y1, TS = meta["z"], meta["x1"], meta["y1"], meta["ts"]

def px(lon): return ((lon + 180) / 360 * (2 ** Z) - X1) * TS
def py(lat):
    r = math.radians(lat)
    return ((1 - math.asinh(math.tan(r)) / math.pi) / 2 * (2 ** Z) - Y1) * TS

out_pts = []
for p in pts:
    out_pts.append({"n": p["n"], "cat": p["cat"], "mc": p["mc"], "t": p["t"], "d": p["d"],
                    "x": round(px(p["lon"]), 1), "y": round(py(p["lat"]), 1)})

img = base64.b64encode(open(os.path.join(d, "praha.jpg"), "rb").read()).decode()
tpl = open(os.path.join(d, "template.html"), encoding="utf-8").read()
html = (tpl.replace("{POINTS}", json.dumps(out_pts, ensure_ascii=False))
           .replace("{IMG}", "data:image/jpeg;base64," + img)
           .replace("{W}", str(meta["w"])).replace("{H}", str(meta["h"])))
open(os.path.join(d, "mereni-rychlosti-praha.html"), "w", encoding="utf-8").write(html)
print("written", len(html), "bytes,", len(out_pts), "points")
