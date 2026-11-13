"""Poll the resepifesbuk-git Cloudflare Pages project for build status."""
import json, os, sys, urllib.request

env = os.path.expanduser("~/.cfenv")
for line in open(env):
    line = line.strip()
    if line.startswith("export "):
        line = line[7:]
    if "=" not in line or line.startswith("#"):
        continue
    k, v = line.split("=", 1)
    os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))

acct = os.environ["CF_ACCOUNT"]
tok = os.environ["CF_TOKEN"]
url = f"https://api.cloudflare.com/client/v4/accounts/{acct}/pages/projects/resepifesbuk-git/deployments?per_page=3"

req = urllib.request.Request(url, headers={"Authorization": "Bearer " + tok})
data = json.load(urllib.request.urlopen(req, timeout=60))
for d in data.get("result", [])[:3]:
    st = d["latest_stage"]
    det = st.get("details") or {}
    print(f"{d['id'][:14]}  {st['name']:12s} {st['status']:10s} {d['created_on'][:19]}  {str(det.get('message',''))[:70]}")
    print(f"    url: {d.get('url','')}")
