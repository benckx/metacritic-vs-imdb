#!/usr/bin/env python3
"""Build index.html: critic vs user rating discrepancy dashboard.

Reads critics_over_users.csv / users_over_critics.csv and embeds a JSON
payload into template.html.
"""
import csv
import json
from collections import defaultdict
from statistics import mean

MIN_YEAR = 1980          # everything older is excluded entirely
CONTEXT1 = 300           # grey dots on the timeline chart
CONTEXT2 = 1200          # grey bubbles on the Metascore vs IMDb chart
TOP_TABLE = 20           # rows per table
TOP2 = 10                # extremes per side on the bubble chart
TOP_GENRE = 1            # extremes per side per genre
TOP_DECADE = 1           # extremes per side per decade
GENRE_COUNT = 12         # how many genres to show


def slim(r):
    return {"id": r["id"], "t": r["t"], "y": r["y"], "d": r["d"], "mc": r["mc"],
            "im": r["im"], "v": r["v"], "img": r["img"], "g": r["g"]}


rows = []
for path in ("critics_over_users.csv", "users_over_critics.csv"):
    for r in csv.DictReader(open(path)):
        rows.append({
            "id": r["tconst"],
            "t": r["title"],
            "y": int(r["year"]) if r["year"] else None,
            "d": float(r["diff_pct"]),
            "mc": int(r["metascore_pct"]),
            "im": float(r["imdb_pct"]),
            "v": int(r["imdb_votes"]),
            "g": r["genres"].split(",") if r["genres"] else [],
            "img": r["img"] or None,
        })
rows = [r for r in rows if r["y"] and r["y"] >= MIN_YEAR]
by_pop = sorted(rows, key=lambda r: -r["v"])

# Tables: global top N per side.
pos_all = sorted((r for r in rows if r["d"] > 0), key=lambda r: -r["d"])
neg_all = sorted((r for r in rows if r["d"] < 0), key=lambda r: r["d"])
tables = {"pos": [slim(r) for r in pos_all[:TOP_TABLE]],
          "neg": [slim(r) for r in neg_all[:TOP_TABLE]]}

# Chart 1 (timeline): most extreme per side per year + popular context.
by_year = defaultdict(list)
for r in rows:
    by_year[r["y"]].append(r)
ext1 = []
for items in by_year.values():
    p = max(items, key=lambda r: r["d"])
    n = min(items, key=lambda r: r["d"])
    if p["d"] > 0:
        ext1.append(p)
    if n["d"] < 0 and n is not p:
        ext1.append(n)
ids1 = {id(r) for r in ext1}
ctx1 = [r for r in by_pop if id(r) not in ids1][:CONTEXT1]
chart1 = {"ext": [slim(r) for r in ext1], "ctx": [slim(r) for r in ctx1]}

# Chart 2 (Metascore vs IMDb bubbles): global extremes + popular context.
ext2 = pos_all[:TOP2] + neg_all[:TOP2]
ids2 = {id(r) for r in ext2}
ctx2 = [r for r in by_pop if id(r) not in ids2][:CONTEXT2]
chart2 = {"ext": [slim(r) for r in ext2], "ctx": [slim(r) for r in ctx2]}

# By genre: most extreme per side for the most common genres.
genre_counts = defaultdict(int)
for r in rows:
    for g in r["g"]:
        genre_counts[g] += 1
top_genres = [g for g, _ in sorted(genre_counts.items(),
                                   key=lambda kv: -kv[1])[:GENRE_COUNT]]
genres = []
for g in top_genres:
    items = [r for r in rows if g in r["g"]]
    p = sorted((r for r in items if r["d"] > 0), key=lambda r: -r["d"])
    n = sorted((r for r in items if r["d"] < 0), key=lambda r: r["d"])
    genres.append({"g": g,
                   "average": mean(r["d"] for r in items),
                   "count": len(items),
                   "pos": [slim(r) for r in p[:TOP_GENRE]],
                   "neg": [slim(r) for r in n[:TOP_GENRE]]})

# By decade: most extreme per side, 1980s .. 2020s.
decades = []
for d0 in range(1980, 2030, 10):
    items = [r for r in rows if d0 <= r["y"] < d0 + 10]
    if not items:
        continue
    p = sorted((r for r in items if r["d"] > 0), key=lambda r: -r["d"])
    n = sorted((r for r in items if r["d"] < 0), key=lambda r: r["d"])
    decades.append({"g": f"{d0}s",
                    "average": mean(r["d"] for r in items),
                    "count": len(items),
                    "pos": [slim(r) for r in p[:TOP_DECADE]],
                    "neg": [slim(r) for r in n[:TOP_DECADE]]})

# Agreement: most popular movies where critics and users match (|diff| <= 1).
agree = [slim(r) for r in by_pop if abs(r["d"]) <= 1][:TOP_TABLE]

payload = {"tables": tables, "chart1": chart1, "chart2": chart2,
           "genres": genres, "decades": decades, "agree": agree,
           "average": mean(r["d"] for r in rows), "count": len(rows)}

print(f"{len(ext1)} timeline extremes, {len(ext2)} bubble extremes, "
      f"{len(genres)} genres, {len(decades)} decades, "
      f"{len(agree)} agreement movies")

with open("template.html") as f:
    html = f.read()
html = html.replace("/*PAYLOAD*/", json.dumps(payload, separators=(",", ":")))
with open("index.html", "w") as f:
    f.write(html)
print("wrote index.html")
