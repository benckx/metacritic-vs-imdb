#!/usr/bin/env bash
# Download the IMDb datasets used by compare.py and decompress them.
set -euo pipefail
cd "$(dirname "$0")"

for name in title.ratings title.basics; do
  echo "downloading $name.tsv.gz ..."
  curl -fSL -o "$name.tsv.gz" "https://datasets.imdbws.com/$name.tsv.gz"
  gunzip -f "$name.tsv.gz"
  echo "-> $name.tsv"
done
