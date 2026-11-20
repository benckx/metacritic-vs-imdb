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


def load_basics_fallback(path: str, wanted: set) -> dict:
    """Map (lowercased title, year) -> tconst for movies, for rows without a tt id.

    Keys matching more than one IMDb movie are dropped as ambiguous.
    """
    index = {}
    with open(path, newline="") as f:
        reader = csv.reader(f, delimiter="\t", quoting=csv.QUOTE_NONE)
        next(reader)
        for row in reader:
            if row[1] != "movie":
                continue
            keys = {(t.lower(), row[5]) for t in (row[2], row[3])}
            for key in keys & wanted:
                index.setdefault(key, set()).add(row[0])
    return {k: v.pop() for k, v in index.items() if len(v) == 1}


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

    # Fallback title+year match for rows without an embedded tt id.
    explicit = {m["tconst"] for m in movies if m["tconst"]}
    missing = [m for m in movies if not m["tconst"]]
    if missing:
        wanted = {(m["title"].rsplit(" (", 1)[0].lower(), str(m["year"]))
                  for m in missing if m["year"]}
        index = load_basics_fallback("title.basics.tsv", wanted)
        for m in missing:
            t = index.get((m["title"].rsplit(" (", 1)[0].lower(),
                           str(m["year"])))
            if t and t not in explicit:
                m["tconst"] = t

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
                     m["reviewCount"], imdb_pct, votes))

    print(f"matched {len(rows)} movies "
          f"(votes>={args.min_votes}, critic reviews>={args.min_reviews})\n")

    def show(label, items):
        print(label)
        print(f"{'diff':>6}  {'MC%':>4}  {'IMDb%':>5}  {'votes':>9}  title")
        for diff, title, year, t, mc, rc, ip, votes in items:
            print(f"{diff:+6.1f}  {mc:>4}  {ip:>5.0f}  {votes:>9,}  "
                  f"{title} [{t}]")
        print()

    rows.sort(key=lambda r: r[0], reverse=True)
    show(f"=== Critics >> users (top {args.top}) ===", rows[:args.top])
    show(f"=== Users >> critics (top {args.top}) ===",
         list(reversed(rows[-args.top:])))

    header = ["diff_pct", "title", "year", "tconst", "metascore_pct",
              "critic_reviews", "imdb_pct", "imdb_votes"]

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
