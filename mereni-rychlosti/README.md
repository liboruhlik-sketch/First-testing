# Mapa míst měření rychlosti v Praze

Interaktivní mapa 133 míst, kde smí Městská policie hl. m. Prahy měřit rychlost
(seznam Krajského ředitelství policie hl. m. Prahy č. j. KRPA-203411-1/ČJ-2026-0000DŽ,
účinnost od 1. 9. 2026).

Zdroj dat: https://mppraha.cz/dalsi-informace/mereni-rychlosti

- `index.html` — samostatná mapa (offline, bez závislostí): podklad OSM vložený jako
  obrázek, 133 bodů ve 4 kategoriích, filtr, vyhledávání, seznam s detailem.
- `tools/items.py` — přepis úředního seznamu do strukturované podoby
- `tools/geocode.py` — geokódování přes Nominatim (výstup `points.json`)
- `tools/build.py` + `tools/template.html` — sestavení `index.html`
  (podklad `praha.jpg` vzniká slepením OSM dlaždic z13, viz `tilemeta.json`)

Polohy bodů jsou orientační — u úseků jde o střed popsaného úseku, u míst
„v celé délce ulice" o střed ulice. Rozhodující je úřední popis v seznamu.

Mapový podklad © přispěvatelé OpenStreetMap (ODbL).
