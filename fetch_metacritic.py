#!/usr/bin/env python3
"""Fetch all Metacritic movie scores via their backend API into metacritic.jsonl."""
import json
import re
import time
import urllib.request

API = ("https://backend.metacritic.com/finder/metacritic/web"
       "?sortBy=-metaScore&productType=movies&offset={offset}&limit={limit}"
       "&apiKey=1MOZgmNFxvmljaQR1X9KAij9Mo4xAY3u")
LIMIT = 100
TT_RE = re.compile(r"(tt\d+)")


def fetch(offset: int) -> dict:
    req = urllib.request.Request(
        API.format(offset=offset, limit=LIMIT),
        headers={"User-Agent": "Mozilla/5.0 (X11; Linux x86_64)"})
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.load(resp)["data"]


def main():
    out = open("metacritic.jsonl", "w")
    offset = 0
    total = None
    while total is None or offset < total:
        for attempt in range(3):
            try:
                data = fetch(offset)
                break
            except Exception as e:
                print(f"offset {offset} attempt {attempt}: {e}")
                time.sleep(5 * (attempt + 1))
        else:
            raise SystemExit(f"giving up at offset {offset}")
        total = data["totalResults"]
        for item in data["items"]:
            css = item.get("criticScoreSummary") or {}
            img = item.get("image") or {}
            bucket = img.get("bucketPath") or ""
            m = TT_RE.search(bucket or img.get("filename") or "")
            out.write(json.dumps({
                "title": item.get("title"),
                "slug": item.get("slug"),
                "year": item.get("premiereYear"),
                "tconst": m.group(1) if m else None,
                "metascore": css.get("score"),
                "reviewCount": css.get("reviewCount"),
                "img": bucket or None,
            }) + "\n")
        offset += LIMIT
        print(f"{min(offset, total)}/{total}", flush=True)
        time.sleep(0.4)
    out.close()


if __name__ == "__main__":
    main()
