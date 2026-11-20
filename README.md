# rating-discrepency

Which movies do critics and IMDb users disagree about the most?

Compares Metacritic critic scores with IMDb user ratings, ranks the
discrepancies, and renders an interactive visualization.

Open `index.html` in a browser to see the result:

- two tables with the 20 most extreme movies per side
- a timeline scatter (diff on x, release year on y) highlighting the most
  extreme movie per side per year, with popular movies as context
- a Metascore vs IMDb scatter where bubble size reflects IMDb vote count

All scores are expressed in percent; the discrepancy is
`Metascore − IMDb rating × 10`. Positive means critics like the movie more
than users, negative the opposite.

## Data sources

- **IMDb**: official [datasets](https://datasets.imdbws.com/)
  (`title.ratings.tsv`, `title.basics.tsv`), not committed — fetch them with
  `./fetch_imdb.sh`.
- **Metacritic**: critic scores for ~17,500 movies fetched from the site's
  backend API into `metacritic.jsonl`.

Movies are joined on the IMDb id embedded in Metacritic image paths, with an
unambiguous title + year fallback. Movies released before 1980, with fewer
than 10,000 IMDb votes, or with fewer than 7 critic reviews are excluded.

## Pipeline

```bash
./fetch_imdb.sh            # download and decompress the IMDb datasets
python3 fetch_metacritic.py  # scrape Metacritic -> metacritic.jsonl
python3 compare.py           # join + rank -> critics_over_users.csv, users_over_critics.csv
python3 make_viz.py          # embed data into template.html -> index.html
```

Only the first two steps hit the network; `compare.py` and `make_viz.py` are
instant and offline. Thresholds are flags on `compare.py`
(`--min-votes`, `--min-reviews`) and constants at the top of `make_viz.py`
(`MIN_YEAR`, `CONTEXT`, `TOP2`, `CONTEXT2`).

## Files

| File | Role |
|---|---|
| `fetch_imdb.sh` | download IMDb datasets |
| `fetch_metacritic.py` | scrape Metacritic scores |
| `compare.py` | join datasets, rank discrepancies, write the two CSVs |
| `make_viz.py` | build `index.html` from `template.html` |
| `template.html` | chart markup and rendering code (vanilla SVG, no dependencies) |
| `index.html` | generated, self-contained visualization |
