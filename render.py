#!/usr/bin/env python3
"""Build compact shared data for the critic vs user rating discrepancy dashboard.

Reads the ranking CSVs and writes the dashboard data and poster thumbnails.
"""
import csv
import json
import math
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor
from io import BytesIO
from statistics import mean
from pathlib import Path
from urllib.request import Request, urlopen

from PIL import Image

MIN_YEAR = 1980          # everything older is excluded entirely
CONTEXT1 = 1000          # grey dots on the timeline chart
CONTEXT2 = 750           # grey bubbles on the Metascore vs IMDb chart
TOP_TABLE = 50           # movies available per table
TOP_CONSENSUS = 35       # movies in the consensus gallery
TOP2 = 50                # extremes per side on the bubble chart
TOP_GENRE = 1            # extremes per side per genre
TOP_PERIOD = 1           # extremes per side per five-year period
GENRE_COUNT = 12         # how many genres to show
POSTER_DIR = Path("posters")
POSTER_SIZE = (236, 348)  # 2x the largest display size (gallery cards)
POSTER_SOURCE = "https://www.metacritic.com/a/img/catalog"


def slim(r, include_votes=True):
    movie = {key: r[key] for key in ("id", "t", "y", "d", "mc", "im", "img")}
    if include_votes:
        movie["v"] = r["v"]
    return movie


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
tables = {"pos": [slim(r, False) for r in pos_all[:TOP_TABLE]],
          "neg": [slim(r, False) for r in neg_all[:TOP_TABLE]]}

# Year-by-year chart: most extreme per side per year + popular context.
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
year_by_year = {"ext": [slim(r) for r in ext1], "ctx": [slim(r) for r in ctx1]}

# Plotted chart (Metascore vs IMDb bubbles): global extremes + popular context.
ext2 = pos_all[:TOP2] + neg_all[:TOP2]
ids2 = {id(r) for r in ext2}
ctx2 = [r for r in by_pop if id(r) not in ids2][:CONTEXT2]
plotted = {"ext": [slim(r) for r in ext2], "ctx": [slim(r) for r in ctx2]}

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
genres.sort(key=lambda group: abs(group["average"]))

# By period: most extreme per side in five-year slices.
periods = []
latest_year = max(r["y"] for r in rows)
for start in range(1980, latest_year + 1, 5):
    items = [r for r in rows if start <= r["y"] < start + 5]
    if not items:
        continue
    p = sorted((r for r in items if r["d"] > 0), key=lambda r: -r["d"])
    n = sorted((r for r in items if r["d"] < 0), key=lambda r: r["d"])
    end = min(start + 4, latest_year)
    periods.append({"g": f"{start}-{end}" if start != end else str(start),
                    "average": mean(r["d"] for r in items),
                    "count": len(items),
                    "pos": [slim(r) for r in p[:TOP_PERIOD]],
                    "neg": [slim(r) for r in n[:TOP_PERIOD]]})

# Consensus: most popular movies where critics and users match, sorted by score.
consensus = [slim(r, False) for r in by_pop if abs(r["d"]) <= 1][:TOP_CONSENSUS]
consensus.sort(key=lambda r: r["mc"] + r["im"], reverse=True)


def category_input(groups, row_height):
    categories = groups
    series = [
        {"name": "Metacritic > IMDb", "data": []},
        {"name": "IMDb > Metacritic", "data": []},
        {"name": "Category mean", "data": []},
    ]
    for index, category in enumerate(categories):
        for side, name in enumerate(("pos", "neg")):
            series[side]["data"].extend(
                {"x": m["d"], "y": index, "meta": m} for m in category[name]
            )
        summary = {key: category[key] for key in ("g", "average", "count")}
        series[2]["data"].append({"x": category["average"], "y": index, "meta": summary})
    return {
        "series": series,
        "labels": [g["g"] for g in categories],
        "limit": math.ceil(max(abs(p["x"]) for s in series for p in s["data"])) + 4,
        "height": 60 + len(categories) * row_height,
    }


payload = {
    "tables": tables,
    "yearByYear": {
        "pos": [m for m in year_by_year["ext"] if m["d"] > 0],
        "neg": [m for m in year_by_year["ext"] if m["d"] < 0],
        "ctx": year_by_year["ctx"],
        "limit": math.ceil(max(abs(m["d"]) for m in year_by_year["ext"] + year_by_year["ctx"])) + 3,
    },
    "plotted": {"pos": [m for m in plotted["ext"] if m["d"] > 0],
                "neg": [m for m in plotted["ext"] if m["d"] < 0],
                "ctx": plotted["ctx"]},
    "genres": category_input(genres, 46),
    "decades": category_input(periods, 60),
    "consensus": consensus,
}

movies = []
movie_indexes = {}
movie_rows = {r["id"]: r for r in rows}


def movie_index(movie):
    key = movie["id"]
    if key not in movie_indexes:
        movie_indexes[key] = len(movies)
        movies.append(slim(movie_rows[key]))
    return movie_indexes[key]


def share_movies(value):
    if isinstance(value, list):
        return [share_movies(item) for item in value]
    if isinstance(value, dict):
        if "id" in value:
            return movie_index(value)
        if "meta" in value and "id" in value["meta"]:
            return {**{k: v for k, v in value.items() if k != "meta"},
                    "movie": movie_index(value["meta"])}
        return {key: share_movies(item) for key, item in value.items()}
    return value


payload = share_movies(payload)
for name, data in payload.items():
    size = len(json.dumps(data, separators=(",", ":")).encode())
    assert size <= 10_000, f"{name} input exceeds the 10 KB budget: {size} bytes"
    print(f"{name} input: {size:,} bytes")


def local_poster(movie):
    """Download and shrink a Metacritic poster once; originals are ~2000x3000."""
    if not movie["img"]:
        return None
    path = POSTER_DIR / f"{movie['id']}.webp"
    if not path.exists():
        try:
            request = Request(POSTER_SOURCE + movie["img"], headers={"User-Agent": "Mozilla/5.0"})
            with urlopen(request, timeout=30) as response:
                image = Image.open(BytesIO(response.read())).convert("RGB")
        except Exception as error:
            print(f"poster {movie['id']} unavailable: {error}")
            return None
        image.thumbnail(POSTER_SIZE, Image.LANCZOS)
        image.save(path, "WEBP", quality=80)
    return path.as_posix()


POSTER_DIR.mkdir(exist_ok=True)
with ThreadPoolExecutor(8) as pool:
    for movie, poster in zip(movies, pool.map(local_poster, movies)):
        movie["img"] = poster
payload["movies"] = movies

print(f"{len(ext1)} timeline extremes, {len(ext2)} bubble extremes, "
      f"{len(genres)} genres, {len(periods)} five-year periods, "
      f"{len(consensus)} consensus movies")

encoded = json.dumps(payload, separators=(",", ":"))
data_path = Path("js/data.js")
data_path.parent.mkdir(exist_ok=True)
data_path.write_text(f"window.dashboardData={encoded};\n")
print(f"wrote {data_path} ({data_path.stat().st_size:,} bytes)")
