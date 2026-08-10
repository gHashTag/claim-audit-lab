#!/usr/bin/env python3
"""Check the case registry against the case tree -- format, then key, then sets.

The order is the point. A registry was guarded here by a pair check comparing
the set of registered files against the set of files on disk, in both
directions, and it passed while the registry held two different cases under one
identifier and had not been valid YAML for a day.

Both failures were invisible for the same reason: the checks read a structured
file with regular expressions. A regular expression sees lines. It parses a
broken document exactly as happily as a good one, and it compares sets without
ever looking at the key those sets are joined on.

So this runs three layers, cheapest and most fundamental first, and each layer
is a precondition for the next being meaningful:

  1. FORMAT -- the file parses as YAML. An instrument that cannot fail on a
     malformed file cannot report anything true about a malformed file.
  2. KEY    -- identifiers are unique, within the registry and across the
     drafts that will one day graduate into it. A set comparison is blind to
     its own join key; duplicate identity on a shared medium poisons every
     test downstream, including tests of correct fixes.
  3. SETS   -- every registered case has a file, every file is registered,
     and the declared counts match reality.

A row whose write-up does not exist yet declares `file_status: not-written`,
so an unkept promise is a recorded state rather than a silent gap.
"""
import pathlib, sys, collections, re

try:
    import yaml
except ImportError:
    print("PyYAML required: pip install pyyaml"); sys.exit(2)

ROOT = pathlib.Path(__file__).resolve().parent.parent
fails = []

# ---- 1. FORMAT -------------------------------------------------------------
src = (ROOT / "cases.yaml").read_text()
try:
    doc = yaml.safe_load(src)
except yaml.YAMLError as e:
    print("FAIL: cases.yaml does not parse as YAML\n"); print(f"  {e}"); sys.exit(1)
if not isinstance(doc, dict) or not isinstance(doc.get("cases"), list):
    print("FAIL: cases.yaml has no top-level `cases:` list"); sys.exit(1)
cases = doc["cases"]
print(f"format: parses, {len(cases)} cases")

# ---- 2. KEY ----------------------------------------------------------------
ids = [c.get("id") for c in cases]
for i, n in collections.Counter(ids).items():
    if n > 1:
        fails.append(f"identifier {i} appears {n} times in the registry")

def num(s):
    m = re.match(r"CASE-(\d+)", str(s))
    return int(m.group(1)) if m else None

reg_nums = {num(i) for i in ids if num(i) is not None}
for d in sorted((ROOT / "drafts").glob("CASE-*")):
    n = num(d.name)
    if n in reg_nums:
        fails.append(f"identifier CASE-{n:02d} names a registry case AND {d.name} -- "
                     f"a collision at graduation time")

# ---- 3. SETS ---------------------------------------------------------------
registered = set()
for c in cases:
    f = c.get("file")
    if not f:
        fails.append(f"{c.get('id')}: no `file:` key"); continue
    registered.add(f)
    if not (ROOT / f).exists():
        if c.get("file_status") != "not-written":
            fails.append(f"{c.get('id')}: registered file {f} does not exist "
                         f"(declare `file_status: not-written` if that is the truth)")
    elif c.get("file_status") == "not-written":
        fails.append(f"{c.get('id')}: declared not-written but {f} exists")

# The identifier lives in more than two places: the registry row, the file
# path, the document's own heading, and -- in at least one case -- a copy of
# the registry row embedded in the document. A rename fixes the carriers you
# look at and leaves the rest to drift, so every carrier is compared, not the
# two that happen to form the obvious pair.
for c in cases:
    f = ROOT / str(c.get("file", ""))
    if not f.exists(): continue
    body = f.read_text()
    head = re.search(r"CASE-\d+", body)
    if head and head.group(0) != c["id"]:
        fails.append(f"{c['id']}: the document calls itself {head.group(0)}")
    stale = re.findall(r"CASE-\d+-[A-Za-z0-9_-]+\.md", body)
    for s_ in set(stale):
        if not (ROOT / "cases" / s_).exists() and not (ROOT / "drafts" / s_).exists():
            fails.append(f"{c['id']}: names {s_}, which is in no tree")

for p in sorted((ROOT / "cases").rglob("*.md")):
    rel = str(p.relative_to(ROOT))
    if rel not in registered:
        fails.append(f"{rel} is in cases/ but no registry row names it")

declared = (doc.get("counts") or {}).get("total")
if declared is not None and declared != len(cases):
    fails.append(f"counts.total says {declared}, the list holds {len(cases)}")

if fails:
    print(f"\nFAIL: {len(fails)} registry defect(s)\n")
    for f in fails: print(f"  {f}")
    sys.exit(1)
print(f"key: {len(ids)} identifiers, all unique, no draft collisions")
print(f"sets: every case filed, every file registered, counts agree")
