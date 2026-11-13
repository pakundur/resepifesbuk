"""Recover ingredient lists that ended up inside `steps`.

25 posts have zero ingredients because the whole ingredient block was parsed
as method (usually old Blogger posts with no section markup at all). A recipe
page with no ingredients cannot earn a Recipe rich result and reads as broken.

Strategy: walk the step list from the top. Leading lines that look like
ingredient entries (quantity + noun, or a bare ingredient noun with no verb)
are moved back into `ingredients` until the first genuine imperative step is
reached. Order is preserved.

A line is an INGREDIENT if:
  - it starts with a quantity ("1 kg", "2 cawan", "½", "200g", "secubit")
  - OR it is short (<60 chars), has no cooking verb, and is not a sentence
    (no full stop in the middle)

Once an imperative step is seen, everything after it stays a step.
"""
import json, os, re, sys

ROOT = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(ROOT, "src", "recipes_clean.json")

QTY = re.compile(
    r"^\s*[\-•*·]*\s*(\d+([.,/]\d+)?|[½¼¾⅓⅔]|secubit|sedikit|sikit|segenggam|"
    r"sebatang|sehelai|sebiji|seulas|secekak|sepak|secawan|sesudu|serbuk)\b",
    re.I,
)
VERB = re.compile(
    r"\b(masukkan|panaskan|tumis|kacau|gaul|kukus|rebus|goreng|bakar|tuang|campur|"
    r"satukan|letak|angkat|tapis|toskan|rendam|potong|hiris|kisar|sejukkan|hidang|"
    r"siapkan|bentuk|celup|perap|perasakan|tabur|masak|biarkan|keluarkan|ambil|"
    r"bancuh|uli|canai|giling|tumbuk|didihkan|blend|sediakan|tutup|pukul|ayak)\b",
    re.I,
)
# bare ingredient nouns that stand alone as a line ("Bawang putih", "Garam")
BARE = re.compile(
    r"^\s*[\-•*·]*\s*(bawang|halia|daun|cili|serai|garam|gula|air|minyak|tepung|"
    r"santan|asam|ikan|udang|sotong|ketam|daging|ayam|telur|kentang|ubi|nasi|"
    r"beras|kelapa|keju|mentega|madu|rempah|perasa|sos|kicap|serbuk|lada|"
    r"kayu manis|bunga|buah pelaga|kerisik|tempe|tauhu|taugeh|kobis|sawi|"
    r"kangkung|terung|bendi|petai|jagung|labu|keledek|sagu|agar|pandan)\b",
    re.I,
)


def looks_ingredient(line):
    t = line.strip()
    if not t:
        return False
    if "?" in t:
        return False
    # a step sentence has a verb after the noun, or sentences with full stops
    if VERB.search(t):
        return False
    if QTY.match(t):
        return True
    if len(t) < 60 and BARE.match(t):
        return True
    if len(t) < 45 and not t.endswith("."):
        return True
    return False


def main():
    recs = json.load(open(SRC, encoding="utf-8"))
    fixed = 0
    details = []

    for r in recs:
        if r["ingredients"]:
            continue  # only repair the empty ones
        steps = r["steps"]
        if not steps:
            continue

        # Scan the WHOLE step list: in these posts the ingredient lines are
        # often not at the top (a stray intro line comes first). Take the
        # leading contiguous run of ingredient-like lines starting wherever
        # the first such line appears.
        start = None
        for i, s in enumerate(steps):
            if "h" in s:
                continue
            if looks_ingredient(s.get("t", "")):
                start = i
                break

        ing, rest = [], []
        if start is None:
            rest = list(steps)
        else:
            rest = list(steps[:start])
            i = start
            while i < len(steps):
                s = steps[i]
                if "h" in s:
                    rest.append(s)
                    i += 1
                    break
                if looks_ingredient(s.get("t", "")):
                    ing.append(s["t"].strip())
                    i += 1
                else:
                    break
            rest.extend(steps[i:])

        if len(ing) >= 2:
            r["ingredients"] = ing
            r["steps"] = rest
            r["n_ing"] = len(ing)
            r["n_steps"] = sum(1 for s in rest if "t" in s)
            fixed += 1
            details.append((r["slug"], len(ing), r["n_steps"]))

    print(f"recipes recovered: {fixed}")
    for slug, ni, ns in details[:15]:
        print(f"  {slug[:58]}  ing={ni} steps={ns}")

    remaining = sum(1 for r in recs if not r["ingredients"])
    print(f"\nstill zero-ingredient: {remaining}")

    if "--apply" in sys.argv:
        json.dump(recs, open(SRC, "w", encoding="utf-8"), ensure_ascii=False)
        print(f"applied -> {SRC}")
    else:
        print("(dry run — pass --apply to write)")


if __name__ == "__main__":
    main()
