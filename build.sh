#!/usr/bin/env bash
# Cloudflare Pages build script.
# Regenerates the static site from committed recipe data.
# Pure Python 3 — no Node/npm dependency for the generator itself.
set -euo pipefail

# Always build from the repository root, regardless of where the CI runner starts.
cd "$(dirname "$0")"

echo "== Resepi Fesbuk static build =="
echo "pwd: $(pwd)"
python3 --version

if [ ! -f "src/posts_full.json" ]; then
  echo "ERROR: src/posts_full.json not found — the scraped source data is missing."
  echo "       Run scrape.py locally, then commit src/posts_full.json."
  exit 1
fi

# 1. Raw Blogger posts -> structured recipe records
python3 parse.py

# 2. Generate the static site into dist/
rm -rf dist
python3 build_static.py

# 3. Verify SEO integrity — fail rather than publish broken pages
python3 verify_static.py

echo "== build complete: $(find dist -name '*.html' | wc -l) pages =="
