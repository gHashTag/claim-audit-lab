#!/usr/bin/env python3
"""Report archive-snapshot coverage for primary-source URLs.

CONTRIBUTING.md s 4 requires every primary-source URL cited in a CASE file to
carry an archived snapshot URL (web.archive.org or archive.today). This script
measures how far the register is from that, and emits the commands to close the
gap.

    python3 scripts/check_archive_coverage.py            # report
    python3 scripts/check_archive_coverage.py --commands # emit save commands
    python3 scripts/check_archive_coverage.py --strict   # exit 1 if any gap

--strict is NOT wired into CI yet, because coverage is currently zero and a
gate that fails on every run teaches people to ignore it. Wire it once coverage
is real.

WHY THE FIELD CANNOT BE TRUSTED AS WRITTEN. Four CASE files carry an
`archive_uri` front-matter field. None of the four holds an archive:
two repeat `primary_source_uri` verbatim, two point at a different paper. A
field that is present and populated reads as satisfied to any reviewer skimming
the front matter, and to any script that only checks for non-emptiness. This
checker therefore validates the *host*, not the presence of the field.
"""

import argparse
import pathlib
import re
import sys
import urllib.parse

ARCHIVE_HOSTS = ("web.archive.org", "archive.today", "archive.ph", "archive.is")

FM = {k: re.compile(rf'^{k}:\s*"([^"]*)"', re.M)
      for k in ("primary_source_uri", "archive_uri")}
URL = re.compile(r'https?://[^\s<>)\]"\']+')


def classify(archive, primary):
    if not archive:
        return "absent", "no archive_uri field"
    host = urllib.parse.urlparse(archive).netloc.lower()
    if any(h in host for h in ARCHIVE_HOSTS):
        return "ok", ""
    if archive.rstrip("/") == (primary or "").rstrip("/"):
        return "self", "archive_uri repeats primary_source_uri verbatim"
    return "wrong-host", f"not an archive host ({host})"


def scan():
    rows = []
    for p in sorted(pathlib.Path("cases").glob("CASE-*.md")):
        text = p.read_text(encoding="utf-8")
        primary = (m.group(1) if (m := FM["primary_source_uri"].search(text)) else "")
        archive = (m.group(1) if (m := FM["archive_uri"].search(text)) else "")
        urls = sorted({u.rstrip(".,;") for u in URL.findall(text)})
        archived_inline = [u for u in urls
                           if any(h in urllib.parse.urlparse(u).netloc.lower()
                                  for h in ARCHIVE_HOSTS)]
        status, why = classify(archive, primary)
        rows.append({"file": p.name, "primary": primary, "archive": archive,
                     "status": status, "why": why, "urls": urls,
                     "archived_inline": archived_inline})
    return rows


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--commands", action="store_true",
                    help="emit web.archive.org/save commands for uncovered URLs")
    ap.add_argument("--strict", action="store_true",
                    help="exit 1 if any primary source lacks a real archive")
    args = ap.parse_args()

    rows = scan()
    total_urls = sum(len(r["urls"]) for r in rows)
    covered = sum(len(r["archived_inline"]) for r in rows)
    bad = [r for r in rows if r["status"] in ("self", "wrong-host")]
    ok = [r for r in rows if r["status"] == "ok"]

    print(f"CASE files: {len(rows)}")
    print(f"Distinct URLs cited: {total_urls}")
    print(f"Archive-host URLs found anywhere in the register: {covered}")
    print(f"Front-matter archive_uri: {len(ok)} real, {len(bad)} populated but "
          f"not an archive, {len(rows) - len(ok) - len(bad)} absent")

    if bad:
        print("\nPopulated archive_uri fields that are NOT archives -- these read "
              "as satisfied to a reviewer and to any presence-only check:")
        for r in bad:
            print(f"  {r['file']}")
            print(f"      {r['why']}")
            print(f"      archive_uri: {r['archive']}")

    if args.commands:
        print("\n# Run these to create snapshots, then paste the resulting")
        print("# archive URLs into each case file's Section 11 Sources list.")
        print("# CONTRIBUTING.md s 4. Space them out; the endpoint rate-limits.")
        seen = set()
        for r in rows:
            fresh = [u for u in r["urls"]
                     if u not in seen and not any(h in u for h in ARCHIVE_HOSTS)]
            if not fresh:
                continue
            print(f"\n# {r['file']}")
            for u in fresh:
                seen.add(u)
                print(f"curl -sS -o /dev/null -w '%{{http_code}} {u}\\n' "
                      f"https://web.archive.org/save/{u}")

    if args.strict and (bad or covered == 0):
        print("\nFAIL: archive coverage incomplete (CONTRIBUTING.md s 4).")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
