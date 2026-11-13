"""Trim rewrite headlines/meta that overshoot SERP limits.

Google truncates titles near 60 chars and descriptions near 158. The LLM
mostly respected the brief, but ~92 headlines landed 61-70 chars. Rather than
re-roll (costly, non-deterministic), trim at a natural boundary:

  1. If there is a colon, keep the part before it when that is still >=30 chars
     (dish name + primary hook usually lives before the colon).
  2. Otherwise cut at the last comma/connector boundary before the limit.
  3. Never cut mid-word, never leave a trailing conjunction.

Also strips em-dashes from inherited source titles used on cards.
"""
import json, os, re

ROOT = os.path.dirname(os.path.abspath(__file__))
RW = os.path.join(ROOT, "src", "rewrite.json")
SRC = os.path.join(ROOT, "src", "recipes_clean.json")

MAX_T = 60
MAX_D = 158


def trim_title(t):
    t = t.strip()
    if len(t) <= MAX_T:
        return t
    # 1. colon split
    if ":" in t:
        head = t.split(":")[0].strip()
        if 30 <= len(head) <= MAX_T:
            return head
    # 2. cut at last separator before the limit
    cut = t[:MAX_T]
    for sep in [", ", " & ", " dan ", " dengan ", " untuk ", " yang "]:
        i = cut.rfind(sep)
        if i >= 30:
            return cut[:i].strip().rstrip(",.")
    # 3. last whole word
    cut = cut.rsplit(" ", 1)[0].strip().rstrip(",.")
    return cut


def main():
    d = json.load(open(RW, encoding="utf-8"))
    changed = 0
    for slug, v in d.items():
        h = v["headline"]
        h = h.replace("—", ",").replace("–", ",")
        h = re.sub(r"\s*,\s*,", ",", h)
        nt = trim_title(h)
        if nt != v["headline"]:
            v["headline"] = nt
            changed += 1
        # description: never allow an em-dash, keep within limit on word boundary
        md = v["meta_desc"].replace("—", ",").replace("–", ",")
        if len(md) > MAX_D:
            md = md[:MAX_D]
            cut = max(md.rfind(". "), md.rfind(", "), md.rfind(" "))
            if cut > 100:
                md = md[:cut]
            md = md.rstrip(", ") + "."
        v["meta_desc"] = md

    json.dump(d, open(RW, "w", encoding="utf-8"), ensure_ascii=False, indent=1)

    lens = [len(v["headline"]) for v in d.values()]
    dl = [len(v["meta_desc"]) for v in d.values()]
    print(f"trimmed {changed} headlines")
    print(f"headline len: min {min(lens)} avg {sum(lens)//len(lens)} max {max(lens)}")
    print(f"meta len:     min {min(dl)} avg {sum(dl)//len(dl)} max {max(dl)}")
    print(f"still >60: {sum(1 for l in lens if l > 60)}")
    print(f"em-dash remaining: {sum(1 for v in d.values() if '—' in v['headline']+v['meta_desc'])}")

    # also de-dash source titles so cards/breadcrumbs never show them
    recs = json.load(open(SRC, encoding="utf-8"))
    n = 0
    for r in recs:
        if any(c in r["title"] for c in "—–"):
            r["title"] = re.sub(r"\s*[—–]\s*", ", ", r["title"]).strip()
            n += 1
    json.dump(recs, open(SRC, "w", encoding="utf-8"), ensure_ascii=False)
    print(f"de-dashed {n} source titles")


if __name__ == "__main__":
    main()
