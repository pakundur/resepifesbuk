#!/usr/bin/env bash
# Cloudflare Pages build script.
# Regenerates the static site from the committed recipe data.
# No npm, no Node — pure Python 3 so the build is fast and dependency-free.
set -euo pipefail

echo "== Resepi Fesbuk static build =="
python3 --version

# 1. Parse raw Blogger posts -> clean recipe records
if [ -f "src/posts_full.json" ]; then
  python3 parse.py
else
  echo "src/posts_full.json missing — using committed src/recipes_clean.json"
fi

# 2. Generate the static site into dist/
rm -rf dist
python3 build_static.py

# 3. Verify SEO integrity — fail the build rather than publish broken pages
python3 verify_static.py

echo "== build complete: $(find dist -name '*.html' | wc -l) pages =="
