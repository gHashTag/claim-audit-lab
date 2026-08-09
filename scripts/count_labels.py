#!/usr/bin/env python3
"""Count five-label claim bullets per CASE file.

Feeds the README scorecard. Run with --validate to check the counter against
the hand-written numbers it is replacing, before trusting any output.

Bullet formats in the register (all four occur, and a counter that handles
only the first silently reports zero for the rest):

    - **[Verified]** ...
    - **[Risk] (a)** ...                      clause inside the bold
    - **[High-risk]** ...                     hyphen in the label
    - **[Open conjecture -- Fpath not located; see Section 7]** ...

The first version of this counter used `[A-Za-z ]+`, which cannot match
"High-risk" and cannot match a label followed by " (a)". It reported 0 where
the truth was 3 and 4. Recorded here because the failure mode is silent: a
label the pattern cannot express reads as an absence, not as an error.
"""

import argparse
import json
import pathlib
import re
import sys

CANON = ["Verified", "Empirical fit", "Open conjecture", "Risk", "High-risk", "Retracted"]
SHORT = {"Verified": "V", "Empirical fit": "EF", "Open conjecture": "OC",
         "Risk": "R", "High-risk": "HR", "Retracted": "Ret"}

# Any bracketed label at the head of a top-level bullet, however it is decorated.
BULLET = re.compile(r"^- \*\*\[([^\]]+)\]", re.M)


def canonical(raw):
    """Map a raw bracket body to one of the five labels, or None."""
    s = raw.strip()
    # strip a trailing clause: "Risk] (a)" arrives as "Risk", but
    # "Open conjecture -- Fpath not located" needs the prefix taken.
    for sep in (" --", " -", ";", ","):
        if sep in s:
            s = s.split(sep)[0].strip()
    s = re.sub(r"\s*\([a-d, +]+\)\s*$", "", s).strip()
    # High-risk must be tested before Risk: "High-risk".startswith is distinct,
    # but a naive substring test would map it to Risk.
    for lab in ("High-risk", "Verified", "Empirical fit", "Open conjecture",
                "Retracted", "Risk"):
        if s.lower() == lab.lower():
            return lab
    return None


def count_file(path):
    text = path.read_text(encoding="utf-8")
    counts = {lab: 0 for lab in CANON}
    unknown = []
    for m in BULLET.finditer(text):
        lab = canonical(m.group(1))
        if lab:
            counts[lab] += 1
        else:
            unknown.append(m.group(1))
    return counts, unknown


def collect():
    out, unknown_all = {}, {}
    for p in sorted(pathlib.Path("cases").glob("CASE-*.md")):
        cid = re.match(r"(CASE-\d+)", p.name).group(1)
        counts, unknown = count_file(p)
        if cid not in out:
            out[cid] = {lab: 0 for lab in CANON}
        for lab in CANON:
            out[cid][lab] += counts[lab]
        if unknown:
            unknown_all.setdefault(cid, []).extend(unknown)
    return out, unknown_all


# The numbers this counter replaces, transcribed from the README scorecard as
# it stood before any of it was regenerated. Used only by --validate.
HANDWRITTEN = {
    "CASE-01": (7, 3, 4, 3, 0, 1), "CASE-02": (6, 1, 2, 4, 1, 0),
    "CASE-03": (3, 0, 0, 2, 3, 0), "CASE-04": (3, 2, 1, 4, 0, 0),
    "CASE-05": (2, 2, 1, 2, 0, 0), "CASE-06": (3, 1, 1, 3, 0, 0),
}


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--validate", action="store_true",
                    help="check against the hand-written numbers; exit 1 on mismatch")
    ap.add_argument("--json", metavar="PATH", help="write counts to PATH")
    args = ap.parse_args()

    counts, unknown = collect()

    if unknown:
        print("Bracketed bullets not mapped to any of the five labels:")
        for cid, labs in unknown.items():
            for lab in labs:
                print(f"  {cid}: [{lab}]")
        print()

    if args.validate:
        bad = []
        for cid, expect in HANDWRITTEN.items():
            got = tuple(counts.get(cid, {}).get(lab, 0) for lab in CANON)
            if got != expect:
                bad.append(f"  {cid}: counted {got}, hand-written {expect}")
        if bad:
            print("Counter disagrees with the hand-written scorecard:")
            print("\n".join(bad))
            print("\nResolve before trusting any regenerated scorecard.")
            return 1
        print(f"OK: counter reproduces all {len(HANDWRITTEN)} hand-written rows "
              "it can be checked against.")
        return 0

    width = max(len(c) for c in counts)
    print(f"{'case':<{width}}  " + "  ".join(f"{SHORT[l]:>4}" for l in CANON))
    for cid in sorted(counts):
        row = counts[cid]
        print(f"{cid:<{width}}  " + "  ".join(f"{row[l]:>4}" for l in CANON))

    if args.json:
        pathlib.Path(args.json).write_text(
            json.dumps({"cases": [{"case": c, **counts[c]} for c in sorted(counts)]},
                       indent=2) + "\n", encoding="utf-8")
        print(f"\nwrote {args.json}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
