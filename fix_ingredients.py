"""Repair ingredient lists contaminated with method sentences.

Root cause: the source HTML for ~142 posts interleaves the method inside what
looks like the ingredients block (old Blogger posts have no section markup at
all). parse.py classified by heading, so "Masukkan serbuk rempah sup dan sup
bunjut. Tumis hingga rempah masak" landed in the ingredient list.

Rule: an ingredient line is a NOUN PHRASE, optionally with quantity. A method
sentence is IMPERATIVE (starts with a cooking verb) or contains a full
sentence with a verb + object + qualifier.

This module:
  1. Moves imperative/method lines out of `ingredients`
  2. Appends them to `steps` in their original order
  3. Strips "Cara:" prefixes
  4. Removes duplicate lines created by the move
  5. Leaves genuinely borderline lines alone (e.g. "Garam secukup rasa")

Usage:  python fix_ingredients.py [--apply]
"""
import json, os, re, sys

ROOT = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(ROOT, "src", "recipes_clean.json")

# A line starting with one of these is a method step, not an ingredient.
START_VERB = re.compile(
    # Strip common list bullets first: "-Masukkan", "•masukn", "-- Blend".
    r"^[\s\-–•*·]*(\d+[\.\)]\s*)?(cara\s*:\s*)?"
    r"(masukkan|masukn|masukkn|panaskan|tumis|kacau|gaul|kukus|rebus|goreng|bakar|"
    r"tuang|campur|satukan|letak|angkat|tapis|toskan|rendam|potong|hiris|kisar|"
    r"sejukkan|hidang|siapkan|bentuk|celup|simpulkan|perap|perasakan|tabur|"
    r"gaulkan|campurkan|masak|biarkan|keluarkan|ambik|ambil|bancuh|uli|canai|"
    r"giling|mayang|tumbuk|didihkan|sejat|buangkan|alihkan|blend|kisar|"
    r"sediakan|tutup|sentiasa|apabila|bila|sementara|selepas|kemudian|"
    r"akhir sekali|pastikan|griskan|alaskan|alas)\b",
    re.I,
)

# Long lines with an internal sentence break are almost always method text.
SENTENCEY = re.compile(r"\.\s+[A-Z]")

# Lines that look method-y but are legitimate ingredient entries.
KEEP = re.compile(
    r"^\s*(garam|gula|serbuk|sos|kicap|minyak|air|tepung|santan|bawang|"
    r"cili|daun|halia|lengkuas|serai|asam|ikan|udang|daging|ayam|telur|"
    r"kentang|ubi|nasi|beras|kelapa|keju|mentega|madu|rempah|perasa)\b",
    re.I,
)


def is_method_line(line):
    t = line.strip()
    if not t:
        return False
    # very short lines are almost always real ingredients
    if len(t) < 45:
        return False
    if START_VERB.match(t):
        return True
    # long line with a sentence break and a cooking verb later on
    if SENTENCEY.search(t) and re.search(
        r"\b(masukkan|tumis|kacau|goreng|rebus|kukus|bakar|angkat|toskan|hidang)\b",
        t, re.I,
    ):
        # keep obvious ingredient-noun lines even if long
        if KEEP.match(t) and not START_VERB.match(t):
            return False
        return True
    return False


def clean_line(line):
    t = line.strip()
    t = re.sub(r"^\s*cara\s*:\s*", "", t, flags=re.I)
    return t


def main():
    recs = json.load(open(SRC, encoding="utf-8"))
    moved = 0
    affected = 0
    report = []

    for r in recs:
        keep, move = [], []
        for line in r["ingredients"]:
            if is_method_line(line):
                move.append(clean_line(line))
            else:
                keep.append(line)

        if not move:
            continue

        # append moved method text as steps, de-duplicated and order-preserved
        existing = {s.get("t", "").strip() for s in r["steps"]}
        added = []
        for m in move:
            if m and m not in existing and m not in added:
                added.append(m)

        # a recipe must keep at least 2 ingredients, otherwise the split was wrong
        if len(keep) < 2:
            report.append((r["slug"], "SKIPPED: would leave <2 ingredients"))
            continue

        r["ingredients"] = keep
        for m in added:
            r["steps"].append({"t": m})
        r["n_ing"] = len(keep)
        r["n_steps"] = sum(1 for s in r["steps"] if "t" in s)
        r["parsed"] = True

        moved += len(added)
        affected += 1
        report.append((r["slug"], f"moved {len(added)} lines"))

    print(f"recipes affected: {affected}")
    print(f"method lines moved from ingredients to steps: {moved}")
    for slug, msg in report[:12]:
        print(f"  {slug[:60]}: {msg}")

    if "--apply" in sys.argv:
        json.dump(recs, open(SRC, "w", encoding="utf-8"), ensure_ascii=False)
        print(f"\napplied -> {SRC}")
    else:
        print("\n(dry run — pass --apply to write)")


if __name__ == "__main__":
    main()
