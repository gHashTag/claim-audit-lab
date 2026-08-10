#!/usr/bin/env python3
"""Regenerate the README "Index of cases" table from cases.yaml.

cases.yaml is the hand-authored source of truth. The README index is a build
artefact: edit cases.yaml, run this script, commit both.

Usage:
    python3 scripts/gen_readme_index.py            # rewrite README.md in place
    python3 scripts/gen_readme_index.py --check    # exit 1 if README is stale

--check makes no changes and is safe to wire into CI alongside the gates in
.github/workflows/banned-words.yml.

The table is written between the BEGIN/END marker comments in README.md.
Anything outside the markers is left alone, so hand-written prose around the
table survives regeneration.

Fields consumed per case entry:
    id            required   e.g. CASE-07
    title         required   rendered in the Subject column
    domain        required   rendered in the Domain column
    claim_status  required   rendered in the Class column
    file          required   link target for the ID column
    status        optional   rendered in the Status column, defaults to draft

Output is ASCII-only, per CHARTER.md section 6 and the ascii-only CI gate.
"""

import argparse
import pathlib
import sys

try:
    import yaml
except ImportError:
    sys.exit("error: PyYAML is required (pip install pyyaml)")

REPO = pathlib.Path(__file__).resolve().parent.parent
MANIFEST = REPO / "cases.yaml"
README = REPO / "README.md"

BEGIN = "<!-- BEGIN GENERATED case-index (scripts/gen_readme_index.py) -->"
END = "<!-- END GENERATED case-index -->"

REQUIRED = ("id", "title", "domain", "claim_status", "file")
VALID_STATUS = ("Verified", "Efit", "Conj", "Risk", "Retr")


def load_cases():
    """Parse cases.yaml and fail loudly on anything that would render wrong."""
    data = yaml.safe_load(MANIFEST.read_text(encoding="utf-8"))
    cases = data["cases"]
    errors = []

    seen = set()
    for i, case in enumerate(cases):
        cid = case.get("id", f"<entry {i}>")
        for field in REQUIRED:
            if not case.get(field):
                errors.append(f"{cid}: missing required field '{field}'")
        if cid in seen:
            errors.append(f"{cid}: duplicate id")
        seen.add(cid)
        status = case.get("claim_status")
        if status and status not in VALID_STATUS:
            errors.append(
                f"{cid}: claim_status {status!r} not one of {list(VALID_STATUS)}"
            )

    # The counts block is hand-maintained; verify it against the entries rather
    # than silently rendering a table that disagrees with it.
    counts = data.get("counts", {})
    if counts:
        tally = {}
        for case in cases:
            key = case.get("claim_status")
            tally[key] = tally.get(key, 0) + 1
        if counts.get("total") != len(cases):
            errors.append(
                f"counts.total is {counts.get('total')}, but there are "
                f"{len(cases)} entries"
            )
        declared = counts.get("by_status", {})
        if declared != tally:
            errors.append(
                f"counts.by_status is {declared}, computed {tally}"
            )

    if errors:
        sys.exit("cases.yaml is inconsistent:\n  " + "\n  ".join(errors))

    return data, cases


def render(data, cases):
    """Build the marker-delimited block, including the totals line."""
    rows = [
        "| ID       | Subject                                | Domain"
        "                              | Class  | Status |",
        "|----------|----------------------------------------|"
        "-------------------------------------|--------|--------|",
    ]
    for case in cases:
        rows.append(
            "| [{id}]({file}) | {title} | {domain} | {cls} | {status} |".format(
                id=case["id"],
                file=case["file"],
                title=case["title"],
                domain=case["domain"],
                cls=case["claim_status"],
                status=case.get("status", "draft"),
            )
        )

    counts = data.get("counts", {})
    by_status = counts.get("by_status", {})
    totals = ", ".join(f"{k} {v}" for k, v in by_status.items())
    lines = [
        BEGIN,
        "",
        "*Generated from [`cases.yaml`](cases.yaml) by"
        " `scripts/gen_readme_index.py`. Do not edit this table by hand --"
        " edit the manifest and re-run the script.*",
        "",
        *rows,
        "",
        f"**Register totals:** {counts.get('total', len(cases))} cases"
        f" -- {totals}.",
        "",
        END,
    ]
    return "\n".join(lines)


def splice(readme_text, block):
    """Replace the marker-delimited region, leaving surrounding prose intact."""
    start = readme_text.find(BEGIN)
    end = readme_text.find(END)
    if start == -1 or end == -1:
        sys.exit(
            f"error: markers not found in {README.name}.\n"
            f"Add these two lines around the index table:\n"
            f"  {BEGIN}\n  {END}"
        )
    if end < start:
        sys.exit("error: END marker precedes BEGIN marker in README.md")
    return readme_text[:start] + block + readme_text[end + len(END):]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--check",
        action="store_true",
        help="verify README is up to date; exit 1 if not, change nothing",
    )
    args = parser.parse_args()

    data, cases = load_cases()
    current = README.read_text(encoding="utf-8")
    updated = splice(current, render(data, cases))

    non_ascii = sorted({c for c in updated if not (c in "\t\n\r" or 32 <= ord(c) <= 126)})
    if non_ascii:
        sys.exit(
            "error: generated index contains non-ASCII characters "
            f"{[hex(ord(c)) for c in non_ascii]} -- see CHARTER.md section 6"
        )

    if args.check:
        if current != updated:
            sys.exit(
                "README.md index is out of date with cases.yaml.\n"
                "Run: python3 scripts/gen_readme_index.py"
            )
        print(f"OK: README index matches cases.yaml ({len(cases)} cases).")
        return

    if current == updated:
        print(f"OK: README index already current ({len(cases)} cases).")
        return

    README.write_text(updated, encoding="utf-8")
    print(f"Regenerated README index from cases.yaml ({len(cases)} cases).")


if __name__ == "__main__":
    main()
