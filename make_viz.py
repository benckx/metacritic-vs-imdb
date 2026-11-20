#!/usr/bin/env python3
"""Build index.html: scatter of critic/user rating discrepancies.

Data = top N extremes per side (highlighted) + popular movies of the
last 40 years (>= min votes) as context dots.
"""
import csv
import json

MIN_YEAR = 1980  # everything older is excluded entirely
CONTEXT = 300  # most-voted popular movies kept as context

rows = []
for path in ("critics_over_users.csv", "users_over_critics.csv"):
    for r in csv.DictReader(open(path)):
        rows.append({
            "t": r["title"],
            "y": int(r["year"]) if r["year"] else None,
            "d": float(r["diff_pct"]),
            "mc": int(r["metascore_pct"]),
            "im": float(r["imdb_pct"]),
            "v": int(r["imdb_votes"]),
        })
rows = [r for r in rows if r["y"] and r["y"] >= MIN_YEAR]

# Per year: most extreme positive (critics > users) and most extreme
# negative (users > critics) movie.
by_year = {}
for r in rows:
    by_year.setdefault(r["y"], []).append(r)

tops = []
for yr, items in by_year.items():
    p = max(items, key=lambda r: r["d"])
    n = min(items, key=lambda r: r["d"])
    if p["d"] > 0:
        tops.append(p)
    if n["d"] < 0 and n is not p:
        tops.append(n)
for r in tops:
    r["top"] = 1

# Chart 2: global most extreme per side (Metascore vs IMDb scatter).
TOP2 = 10
for r in sorted((r for r in rows if r["d"] > 0), key=lambda r: -r["d"])[:TOP2]:
    r["e2"] = 1
for r in sorted((r for r in rows if r["d"] < 0), key=lambda r: r["d"])[:TOP2]:
    r["e2"] = 1

top_keys = {(r["t"], r["y"]) for r in tops}
context = [r for r in rows if (r["t"], r["y"]) not in top_keys]
context = sorted(context, key=lambda r: -r["v"])[:CONTEXT]

included = {id(r) for r in context + tops}
extra_e2 = [r for r in rows if r.get("e2") and id(r) not in included]

# Extra context for chart 2 only (flag c2 keeps it out of chart 1).
CONTEXT2 = 1200
for r in extra_e2:
    r["c2"] = 1
pool = sorted(rows, key=lambda r: -r["v"])
extra_c2 = []
taken = included | {id(r) for r in extra_e2}
for r in pool:
    if len(context) + len(extra_c2) >= CONTEXT2:
        break
    if id(r) not in taken:
        r["c2"] = 1
        extra_c2.append(r)

data = context + extra_c2 + extra_e2 + tops  # tops last, drawn on top
print(f"{len(tops)} per-year extremes, "
      f"{sum(1 for r in rows if r.get('e2'))} chart-2 extremes, "
      f"{len(context)} shared + {len(extra_c2)} chart-2-only context movies")

# Tables: global top 20 per side.
tables = {
    "pos": sorted((r for r in rows if r["d"] > 0),
                  key=lambda r: -r["d"])[:20],
    "neg": sorted((r for r in rows if r["d"] < 0),
                  key=lambda r: r["d"])[:20],
}

with open("template.html") as f:
    html = f.read()
html = html.replace("/*DATA*/", json.dumps(data, separators=(",", ":")))
html = html.replace("/*TABLES*/", json.dumps(tables, separators=(",", ":")))
with open("index.html", "w") as f:
    f.write(html)
print("wrote index.html")
