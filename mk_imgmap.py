#!/usr/bin/env python3
"""Build a slug -> original image URL map for R2 migration.

Emits img_map.json:  [{"slug":..., "key":"<seo-name>.<ext>", "src":"<max-res url>", "old":"<current url>"}]
"""
import json, os, re, collections

BASE = os.path.dirname(os.path.abspath(__file__))
recipes = json.load(open(os.path.join(BASE, 'src', 'recipes_clean.json')))

# Blogger size token -> max resolution. s0 = original uploaded resolution.
MAXTOK = 's0'

def to_max(url):
    """Replace the size segment (e.g. s1600, w1200-h900-c, s800) with s0."""
    return re.sub(r'/(s\d+|w\d+(-h\d+)?(-c)?|w\d+-h\d+)/', f'/{MAXTOK}/', url)

def ext_of(url):
    path = url.split('/')[-1].split('?')[0]
    e = os.path.splitext(path)[1].lower()
    if e in ('.jpg', '.jpeg', '.png', '.webp', '.gif'):
        return '.jpg' if e == '.jpeg' else e
    return '.jpg'

out = []
seen_slug = collections.Counter()
for r in recipes:
    slug = r.get('slug')
    img = (r.get('img') or '').strip()
    if not slug or not img:
        continue
    seen_slug[slug] += 1
    key = slug + ext_of(img)
    if seen_slug[slug] > 1:
        key = f"{slug}-{seen_slug[slug]}{ext_of(img)}"
    out.append({
        "slug": slug,
        "key": key,
        "src": to_max(img),
        "old": img,
    })

json.dump(out, open(os.path.join(BASE, 'img_map.json'), 'w'), indent=1)

print("entries:", len(out))
print("unique keys:", len({x['key'] for x in out}))
print("unique src urls:", len({x['src'] for x in out}))
print("unique old urls:", len({x['old'] for x in out}))
dups = [k for k, c in collections.Counter(x['slug'] for x in out).items() if c > 1]
print("duplicate slugs:", len(dups))
for x in out[:3]:
    print(" ", x['key'], "<-", x['src'][-60:])
