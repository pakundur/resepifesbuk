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

# GA4 Measurement ID. Committed here so the Pages build inherits it without
# dashboard env config. This file is the source of truth.
export GA4_ID="${GA4_ID:-$(cat ga4_id.txt 2>/dev/null || echo '')}"
echo "GA4_ID: $GA4_ID"

if [ ! -f "src/posts_full.json" ]; then
  echo "ERROR: src/posts_full.json not found — the scraped source data is missing."
  echo "       Run scrape.py locally, then commit src/posts_full.json."
  exit 1
fi

# 1. Raw Blogger posts -> structured recipe records
python3 parse.py

# 2. Clean SEO slugs. parse.py regenerates src/recipes_clean.json from the raw
#    Blogger data every build, which restores the year-month slug prefix. This
#    migration is idempotent: it strips the prefix if present and leaves clean
#    slugs untouched, so the committed slug_map.json keeps the 301s stable.
python3 migrate_slugs.py

# 3. Re-key the LLM layers onto the (possibly new) slugs. classify/rewrite/links
#    are generated artifacts keyed by slug, so they must follow the migration.
python3 remap_slug_keys.py

# 4. Generate the static site into dist/
rm -rf dist
python3 build_static.py

# 5. Verify Google compliance and SEO integrity — fail rather than publish
python3 verify_google.py

# 6. Assert all 16 audit requirements before the artifact is considered shippable
python3 verify_all.py

echo "== build complete: $(find dist -name '*.html' | wc -l) pages =="
