#!/usr/bin/env python3
"""
Verify every Shopee affiliate short link resolves to a real product AND that
affiliate attribution (utm_medium=affiliates) survives the redirect.

Shopee rate-limits aggressively: burst requests return no location header.
So we space requests, retry, and use a mobile UA (desktop UA gets the SPA shell
instead of the redirect).
"""
import json, re, subprocess, time, sys
from pathlib import Path

UA = ("Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) "
      "AppleWebKit/605.1.15 Mobile/15E148")

DATA = json.loads(Path("affiliate_links.json").read_text())


def resolve(url, tries=3):
    """Return (final_location, product_path, has_aff, http_code)."""
    for i in range(tries):
        r = subprocess.run(
            ["curl", "-sI", "-m", "30", "-A", UA, url],
            capture_output=True, text=True)
        loc = ""
        for line in r.stdout.splitlines():
            if line.lower().startswith("location:"):
                loc = line.split(":", 1)[1].strip()
                break
        if loc:
            prod = re.search(r"shopee\.com\.my/[A-Za-z0-9_.-]+/\d+/\d+", loc)
            aff = "utm_medium=affiliates" in loc
            return loc, (prod.group(0) if prod else None), aff, r.stdout
        time.sleep(4 + i * 3)
    return "", None, False, ""


def main():
    results = []
    total = sum(len(v["links"]) for v in DATA["products"].values())
    n = 0
    for key, prod in DATA["products"].items():
        for idx, link in enumerate(prod["links"], 1):
            n += 1
            loc, product, aff, raw = resolve(link)
            status = "OK" if (product and aff) else ("ERRPAGE" if "error_page" in loc else "NO-REDIRECT")
            tag = f"{key}{idx}"
            if not raw and not loc:
                # capture status code for diagnosis
                pass
            results.append({
                "tag": tag, "keyword": prod["keyword"], "slot": idx,
                "url": link, "status": status,
                "product": product, "affiliate": aff,
            })
            print(f"[{n:2d}/{total}] {status:11s} {tag:14s} {product or loc[:60] or '-'}")
            time.sleep(2)
    Path("affiliate_check.json").write_text(json.dumps(results, indent=1))

    ok = sum(1 for r in results if r["status"] == "OK")
    print()
    print(f"RESULT: {ok}/{total} resolve with affiliate attribution")
    bad = [r for r in results if r["status"] != "OK"]
    if bad:
        print("\nFAILED:")
        for r in bad:
            print(f"  {r['tag']:14s} {r['status']:11s} {r['url']}")
    return 0 if ok == total else 1


if __name__ == "__main__":
    sys.exit(main())
