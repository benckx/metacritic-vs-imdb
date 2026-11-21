#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
root=$PWD

command -v curl >/dev/null
command -v gunzip >/dev/null
python3 -c 'from PIL import Image'

./fetch_imdb.sh

tmp_dir=$(mktemp -d "$root/.refresh.XXXXXX")
trap 'rm -f "$tmp_dir/metacritic.jsonl"; rmdir "$tmp_dir"' EXIT
(cd "$tmp_dir" && python3 "$root/fetch_metacritic.py")
mv "$tmp_dir/metacritic.jsonl" "$root/metacritic.jsonl"

python3 compare.py
python3 render.py
