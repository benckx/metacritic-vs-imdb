#!/usr/bin/env python3
"""Join Metacritic scores with the IMDb ratings dump and rank discrepancies.

Discrepancy = Metascore - (IMDb rating * 10). Positive means critics like
the movie more than IMDb users; negative means users like it more.
"""
import argparse
import csv
import json
import sys


def load_imdb_ratings(path: str) -> dict:
    ratings = {}
    with open(path) as f:
        reader = csv.reader(f, delimiter="\t")
        next(reader)
        for tconst, rating, votes in reader:
            ratings[tconst] = (float(rating), int(votes))
    return ratings


def load_basics_fallback(path: str, wanted: set, explicit: set) -> tuple:
    """Return fallback matches, genres, and release years for explicit IMDb IDs."""
    index = {}
    genres = {}
    years = {}
    with open(path, newline="") as f:
        reader = csv.reader(f, delimiter="\t", quoting=csv.QUOTE_NONE)
        next(reader)
        for row in reader:
            if row[1] != "movie":
                continue
            if row[8] != "\\N":
                genres[row[0]] = row[8]
            if row[0] in explicit and row[5] != "\\N":
                years[row[0]] = int(row[5])
            keys = {(t.lower(), row[5]) for t in (row[2], row[3])}
            for key in keys & wanted:
                index.setdefault(key, set()).add(row[0])
    return index, genres, years


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--min-votes", type=int, default=10000,
                    help="minimum IMDb vote count (default 10000)")
    ap.add_argument("--min-reviews", type=int, default=7,
                    help="minimum Metacritic critic review count (default 7)")
    ap.add_argument("--top", type=int, default=20)
    args = ap.parse_args()

    movies = [json.loads(line) for line in open("metacritic.jsonl")]
    movies = [m for m in movies if m["metascore"] is not None
              and (m["reviewCount"] or 0) >= args.min_reviews]

    ratings = load_imdb_ratings("title.ratings.tsv")

    # Match exact years first; only use adjacent years for an unambiguous eligible movie.
    explicit = {m["tconst"] for m in movies if m["tconst"]}
    missing = [m for m in movies if not m["tconst"]]
    wanted = {(m["title"].rsplit(" (", 1)[0].lower(), str(int(m["year"]) + offset))
              for m in missing if m["year"] for offset in (-1, 0, 1)}
    index, genres, years = load_basics_fallback("title.basics.tsv", wanted, explicit)
    for m in movies:
        if m["tconst"] in years:
            m["year"] = max(int(m["year"] or 0), years[m["tconst"]])

    def eligible(t):
        return t in ratings and ratings[t][1] >= args.min_votes

    # Do not let an adjacent-year match steal another Metacritic film's exact match.
    exact_reserved = set().union(*(index.get((m["title"].rsplit(" (", 1)[0].lower(),
                                             str(m["year"])), set())
                                   for m in missing if m["year"]))
    for m in missing:
        if not m["year"]:
            continue
        title = m["title"].rsplit(" (", 1)[0].lower()
        year = int(m["year"])
        exact = index.get((title, str(year)), set())
        if len(exact) == 1:
            t = next(iter(exact))
            if eligible(t) and t not in explicit:
                m["tconst"] = t
                continue
        if any(eligible(t) for t in exact):
            continue
        if m["title"].lower() != title:
            continue
        nearby = [(t, other_year) for other_year in (year - 1, year + 1)
                  for t in index.get((title, str(other_year)), set()) if eligible(t)]
        if len(nearby) == 1 and nearby[0][0] not in explicit | exact_reserved:
            m["tconst"] = nearby[0][0]
            m["year"] = max(year, nearby[0][1])

    rows = []
    seen = set()
    for m in movies:
        t = m["tconst"]
        if not t or t in seen or t not in ratings:
            continue
        seen.add(t)
        imdb_rating, votes = ratings[t]
        if votes < args.min_votes:
            continue
        imdb_pct = imdb_rating * 10
        diff = m["metascore"] - imdb_pct
        rows.append((diff, m["title"], m["year"], t, m["metascore"],
                     m["reviewCount"], imdb_pct, votes,
                     genres.get(t, ""), m.get("img") or ""))

    print(f"matched {len(rows)} movies "
          f"(votes>={args.min_votes}, critic reviews>={args.min_reviews})\n")

    def show(label, items):
        print(label)
        print(f"{'diff':>6}  {'MC%':>4}  {'IMDb%':>5}  {'votes':>9}  title")
        for diff, title, year, t, mc, rc, ip, votes, *_ in items:
            print(f"{diff:+6.1f}  {mc:>4}  {ip:>5.0f}  {votes:>9,}  "
                  f"{title} [{t}]")
        print()

    rows.sort(key=lambda r: r[0], reverse=True)
    show(f"=== Critics >> users (top {args.top}) ===", rows[:args.top])
    show(f"=== Users >> critics (top {args.top}) ===",
         list(reversed(rows[-args.top:])))

    header = ["diff_pct", "title", "year", "tconst", "metascore_pct",
              "critic_reviews", "imdb_pct", "imdb_votes", "genres", "img"]

    def dump(path, items):
        with open(path, "w", newline="") as f:
            w = csv.writer(f)
            w.writerow(header)
            w.writerows(items)
        print(f"{len(items)} rows written to {path}", file=sys.stderr)

    dump("critics_over_users.csv", [r for r in rows if r[0] >= 0])
    dump("users_over_critics.csv",
         [r for r in reversed(rows) if r[0] < 0])


if __name__ == "__main__":
    main()
