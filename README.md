# rating-discrepency

Which movies do critics and IMDb users disagree about the most?

Compares Metacritic critic scores with IMDb user ratings, ranks the
discrepancies, and renders an interactive visualization.

Open `index.html` in a browser to see the result:

- two tables with the 50 most extreme movies per side, shown 10 at a time
- a timeline scatter (diff on x, release year on y) highlighting the most
  extreme movie per side per year, with popular movies as context
- a Metascore vs IMDb scatter where bubble size reflects IMDb vote count
- the most extreme movies and average differences by genre and five-year period
- a gallery of popular movies where scores differ by at most one point

Keep `styles.css`, `dashboard.js`, `data.js`, and `posters/` beside `index.html`.
`render.py` precomputes each visualization's selected movies, averages, and
axis limits. Each view's input must stay below 10 KB; movie details are stored
once in a shared lookup. Charts render only when they approach the viewport.
ApexCharts requires an internet connection.

All scores are expressed in percent; the discrepancy is
`Metascore − IMDb rating × 10`. Positive means critics like the movie more
than users, negative the opposite.

## Data sources

- **IMDb**: official [datasets](https://datasets.imdbws.com/)
  (`title.ratings.tsv`, `title.basics.tsv`), not committed — fetch them with
  `./fetch_imdb.sh`.
- **Metacritic**: critic scores fetched from the site's
  backend API into `metacritic.jsonl`.

Movies are joined on the IMDb id embedded in Metacritic image paths, with an
unambiguous title + year fallback. When no eligible exact-year match exists,
an unambiguous eligible match one year earlier or later may be used. The later
year is displayed when sources disagree. Movies with fewer than 10,000 IMDb
votes or fewer than 7 critic reviews are excluded from the rankings. The
dashboard also excludes movies released before 1980 and movies without a year.

## Refreshing the data

To download fresh data and rebuild the rankings and dashboard, run:

```bash
./full_refresh.sh
```

The script requires Bash, `curl`, `gunzip`, Python 3, and Pillow (`python3 -m pip install pillow`). It can be run from
any directory and stops
if a step fails. A failed Metacritic download leaves the previous
`metacritic.jsonl` intact; earlier completed steps may still have updated files.
Review the changed data and generated files before committing them.

The individual steps are:

```bash
./fetch_imdb.sh            # download and decompress the IMDb datasets
python3 fetch_metacritic.py  # scrape Metacritic -> metacritic.jsonl
python3 compare.py           # join + rank -> critics_over_users.csv, users_over_critics.csv
python3 render.py          # generate index.html, dashboard.js, and data.js
```

`render.py` downloads each poster it needs once, shrinks it to fit 236×348 WebP
in `posters/` (Metacritic originals are ~2000×3000, ~1 MB), and reuses cached
files afterwards. It requires Pillow (`pip install pillow`). `compare.py` runs
offline. Thresholds are flags on `compare.py`
(`--min-votes`, `--min-reviews`) and constants at the top of `render.py`
(`MIN_YEAR`, `CONTEXT1`, `TOP2`, `CONTEXT2`).

## Files

| File                                               | Role                                                                                      |
|----------------------------------------------------|-------------------------------------------------------------------------------------------|
| `full_refresh.sh`                                  | run the full refresh pipeline                                                             |
| `fetch_imdb.sh`                                    | download IMDb datasets                                                                    |
| `fetch_metacritic.py`                              | scrape Metacritic scores                                                                  |
| `compare.py`                                       | join datasets, rank discrepancies, write the two CSVs                                     |
| `metacritic.jsonl`                                 | fetched Metacritic movie data                                                             |
| `critics_over_users.csv`, `users_over_critics.csv` | ranked movie data                                                                         |
| `render.py`                                      | precompute compact chart inputs and build the page                                        |
| `template.html`                                    | dashboard markup and ApexCharts rendering code                                            |
| `index.html`                                       | generated dashboard shell                                                                 |
| `styles.css`                                       | dashboard styles                                                                          |
| `dashboard.js`                                     | generated renderer and lazy-loading code                                                  |
| `posters/`                                         | generated, resized poster thumbnails                                                      |
| `data.js`                                          | generated, precomputed inputs and shared movie details; supports direct `file://` viewing |
