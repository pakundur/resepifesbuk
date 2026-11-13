#!/usr/bin/env python3
"""Upload downloaded images to R2 bucket 'resepifesbuk' under SEO-friendly keys."""
import json, os, sys, mimetypes
from concurrent.futures import ThreadPoolExecutor, as_completed
import boto3
from botocore.config import Config

BASE = os.path.dirname(os.path.abspath(__file__))
IMGDIR = os.path.join(BASE, 'imgdl')
items = json.load(open(os.path.join(BASE, 'img_map.json')))

env = {}
for line in open(os.path.expanduser('~/.cfenv')):
    line = line.strip()
    if line and not line.startswith('#') and '=' in line:
        k, v = line.split('=', 1)
        env[k.strip().replace('export ', '')] = v.strip().strip('"').strip("'")

s3 = boto3.client('s3',
    endpoint_url=env['R2_ENDPOINT'],
    aws_access_key_id=env['R2_ACCESS_KEY'],
    aws_secret_access_key=env['R2_SECRET_KEY'],
    region_name='auto',
    config=Config(max_pool_connections=16, retries={'max_attempts': 5}))

BUCKET = 'resepifesbuk'
CACHE = 'public, max-age=31536000, immutable'

def up(it):
    src = os.path.join(IMGDIR, it['key'])
    if not os.path.exists(src):
        return (it['key'], 'MISSING', 0)
    ct = mimetypes.guess_type(src)[0] or 'image/jpeg'
    if it['key'].endswith('.jpg'):
        ct = 'image/jpeg'
    sz = os.path.getsize(src)
    try:
        s3.upload_file(src, BUCKET, it['key'], ExtraArgs={
            'ContentType': ct,
            'CacheControl': CACHE,
        })
        return (it['key'], 'ok', sz)
    except Exception as e:
        return (it['key'], f'FAIL {str(e)[:80]}', 0)

ok = miss = fail = 0
total = 0
fails = []
with ThreadPoolExecutor(max_workers=8) as ex:
    futs = [ex.submit(up, it) for it in items]
    for i, f in enumerate(as_completed(futs), 1):
        k, st, sz = f.result()
        if st == 'ok':
            ok += 1; total += sz
        elif st == 'MISSING':
            miss += 1; fails.append((k, 'no local file'))
        else:
            fail += 1; fails.append((k, st))
        if i % 100 == 0:
            print(f"  {i}/{len(items)} ok={ok} miss={miss} fail={fail} {total/1e6:.1f} MB", flush=True)

print(f"\nUPLOAD DONE ok={ok} missing={miss} fail={fail} bytes={total/1e6:.2f} MB")
for k, s in fails[:20]:
    print("  ", k, s)
