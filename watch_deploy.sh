#!/usr/bin/env bash
# Poll the newest Cloudflare Pages deployment until it finishes.
set -u
[ -f "$HOME/.cfenv" ] && . "$HOME/.cfenv"
: "${CF_ACCOUNT:?CF_ACCOUNT missing}"
: "${CF_TOKEN:?CF_TOKEN missing}"

API="https://api.cloudflare.com/client/v4/accounts/${CF_ACCOUNT}/pages/projects/resepifesbuk-git/deployments?per_page=1"

for i in $(seq 1 30); do
  OUT=$(curl -s -H "Authorization: Bearer ${CF_TOKEN}" "$API")
  LINE=$(printf '%s' "$OUT" | python3 -c '
import json,sys
try:
    d=json.load(sys.stdin)
    r=d["result"][0]
    print(r["short_id"], r["latest_stage"]["name"], r["latest_stage"]["status"],
          r["deployment_trigger"]["metadata"].get("commit_hash","")[:8])
except Exception as e:
    print("pending", e)
')
  echo "[$i] $LINE"
  case "$LINE" in
    *" success"*) echo "DEPLOY OK"; exit 0 ;;
    *" failure"*) echo "DEPLOY FAILED"; exit 1 ;;
  esac
  sleep 15
done
echo "TIMEOUT"
exit 1
