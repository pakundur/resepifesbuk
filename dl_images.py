#!/usr/bin/env python3
"""Download all recipe images at max resolution into ./imgdl/, SEO-named."""
import json, os, sys, time, urllib.request, urllib.error
from concurrent.futures import ThreadPoolExecutor, as_completed

BASE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(BASE, 'imgdl')
os.makedirs(OUT, exist_ok=True)
items = json.load(open(os.path.join(BASE, 'img_map.json')))
UA = {"User-Agent": "Mozilla/5.0 (Linux; Android 16) AppleWebKit/537.36"}

def fetch(it):
    dest = os.path.join(OUT, it['key'])
    if os.path.exists(dest) and os.path.getsize(dest) > 1024:
        return (it['key'], 'skip', os.path.getsize(dest))
    for attempt in range(4):
        try:
            req = urllib.request.Request(it['src'], headers=UA)
            with urllib.request.urlopen(req, timeout=60) as r:
                data = r.read()
            if len(data) < 512:
                raise ValueError(f"too small {len(data)}")
            if data[:2] not in (b'\xff\xd8', b'\x89P', b'RI', b'GI'):
                raise ValueError("not an image")
            with open(dest, 'wb') as f:
                f.write(data)
            return (it['key'], 'ok', len(data))
        except Exception as e:
            if attempt == 3:
                return (it['key'], f'FAIL {str(e)[:60]}', 0)
            time.sleep(2 * (attempt + 1))

ok = skip = fail = 0
total = 0
fails = []
with ThreadPoolExecutor(max_workers=8) as ex:
    futs = {ex.submit(fetch, it): it for it in items}
    for i, f in enumerate(as_completed(futs), 1):
        k, st, sz = f.result()
        if st == 'ok':
            ok += 1; total += sz
        elif st == 'skip':
            skip += 1; total += sz
        else:
            fail += 1; fails.append((k, st))
        if i % 50 == 0:
            print(f"  {i}/{len(items)}  ok={ok} skip={skip} fail={fail}  {total/1e6:.1f} MB", flush=True)

print(f"\nDONE ok={ok} skip={skip} fail={fail} total={total/1e6:.2f} MB")
for k, s in fails:
    print("  FAILED:", k, s)
