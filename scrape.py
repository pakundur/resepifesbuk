"""Scrape the full Resepi Fesbuk Blogger corpus into structured JSON.

Blogger JSON feed: 748 posts, 150 per request (max-results cap), paged via
start-index. Keeps images pointing at blogger.googleusercontent.com (user
requirement: images stay in Google).
"""
import json, urllib.request, urllib.error, time, re, html, os

SITE = "https://www.resepifesbuk.com"
FEED = SITE + "/feeds/posts/default"
OUT = os.path.expanduser("~/resepifesbuk/src/posts_full.json")
PAGE = 150

def get(url, tries=4):
    for a in range(tries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 resepifesbuk-static/1.0"})
            with urllib.request.urlopen(req, timeout=90) as r:
                return json.loads(r.read().decode("utf-8", "replace"))
        except urllib.error.HTTPError as e:
            if e.code in (429, 503):
                print(f"    {e.code}, backing off", flush=True)
                time.sleep(20 * (a + 1)); continue
            raise
        except Exception as ex:
            if a == tries - 1:
                raise
            time.sleep(5)
    raise RuntimeError("exhausted")

def txt(node, key="$t"):
    if not node: return ""
    return node.get(key, "") if isinstance(node, dict) else ""

total = None
start = 1
posts = []
while True:
    url = f"{FEED}?alt=json&max-results={PAGE}&start-index={start}"
    d = get(url)
    feed = d.get("feed", {})
    if total is None:
        total = int(feed.get("openSearch$totalResults", {}).get("$t", 0))
        print(f"total posts: {total}", flush=True)
    entries = feed.get("entry", [])
    if not entries:
        break
    for e in entries:
        alt = ""
        for l in e.get("link", []):
            if l.get("rel") == "alternate":
                alt = l.get("href", ""); break
        thumb = txt(e.get("media$thumbnail", {}), "url")
        cats = [c.get("term", "") for c in e.get("category", []) if c.get("term")]
        posts.append({
            "title": html.unescape(txt(e.get("title", {}))),
            "url": alt,
            "published": txt(e.get("published", {})),
            "updated": txt(e.get("updated", {})),
            "cats": cats,
            "thumb": thumb,
            "content": txt(e.get("content", {})),
        })
    print(f"  fetched {len(posts)}/{total}", flush=True)
    if len(posts) >= total:
        break
    start += PAGE
    time.sleep(1.5)

# dedupe by url
seen = set(); uniq = []
for p in posts:
    if p["url"] and p["url"] not in seen:
        seen.add(p["url"]); uniq.append(p)

json.dump(uniq, open(OUT, "w"), ensure_ascii=False)
print(f"DONE: {len(uniq)} unique posts -> {OUT}")
print(f"size: {os.path.getsize(OUT)/1024/1024:.1f} MB")
