# Archive helper (doc-only, no auto-CI)

Every URL cited in a CASE file (Sections 1, 2, 4-8, 11) should also exist
as a Wayback Machine snapshot or other immutable archive, so the case
remains auditable when the original source moves or disappears.

This document describes the manual workflow. Archival is **not**
enforced by CI as of v0.2 -- the markdown-link-check workflow only
warns; case authors are responsible for archival. See
`methodology/README.md` Section 6 for the rationale (link-rot is a
documented failure mode of similar audit projects, cf. Retraction
Watch's pre-2020 link-rot bug fixed in their 2020 redesign).

## Required archives

For each CASE file, at minimum archive:

1. The **primary_source_uri** named in the YAML front-matter.
2. Every URL inside Section 2 (Programme claims, verbatim) -- because
   the verbatim quotes lose their evidentiary value if the source
   disappears.
3. Every URL used as evidence inside Sections 4-8 (the five inventories).

Best-effort archive everything in Section 11 (Sources).

## Manual archival workflow

### Option A -- Wayback Machine (preferred)

```bash
# Single URL
curl -X POST "https://web.archive.org/save/<URL>" \
     -H "Accept: application/json"

# Get back a snapshot URL like:
#   https://web.archive.org/web/20260602153300/<URL>
```

Paste the resulting Wayback URL into the `archive_uri:` field of the
YAML front-matter (for the primary source) and into a parenthetical
note next to each non-primary URL inside Sections 2-11.

### Option B -- archive.today

For sources that block the Wayback Machine (some publisher walls,
some social-media platforms), use `https://archive.ph/` instead:

1. Open `https://archive.ph/`
2. Paste the URL into "I want to save this page"
3. Wait for the snapshot to appear
4. Copy the resulting `archive.ph/<hash>` URL into the CASE file

### Option C -- local PDF capture (last resort)

If neither Wayback nor archive.today can capture the page (e.g. PDF
behind authentication), save a local PDF via the browser print dialog
and commit it under `cases/CASE-NN-attachments/` with a SHA-256 hash
recorded inline. Keep attachments under 5 MB each.

## Recommended audit cadence

- **At case admission:** archive the primary_source_uri before
  promoting the file from `draft` to `under-review`.
- **At every claim-status change:** re-archive the source that the
  status change depends on.
- **Quarterly sweep:** the markdown-link-check workflow (see
  `.github/workflows/banned-words.yml`) runs on a schedule and reports
  broken links as a non-blocking issue; CASE maintainers triage and
  re-archive within 14 days (CONTRIBUTING.md SLA for factual
  corrections).

## What we do NOT do (and why)

- We do **not** auto-archive on PR merge. Wayback's Save Page Now API
  is rate-limited and unreliable in CI; flaky CI erodes trust in the
  ledger. Manual + scheduled link-check is the documented compromise.
- We do **not** rely on academic permalinks alone (DOI, arXiv ID).
  Those are stable for the metadata but the publisher landing page
  can still change, and our quotes are from the landing page text.
- We do **not** store local mirrors of copyrighted full-text. We store
  short verbatim quotes (fair use for criticism) plus the Wayback URL.

## Failure mode catalogue (link-rot evidence base)

The most-cited reasons audit registers lose evidentiary value:

1. Source moved without redirect (most common).
2. Source deleted by author after critique appeared.
3. Source paywalled after originally open (publisher policy change).
4. Hosting platform shutdown (Geocities-style; vixra, ResearchGate
   profile deletions, blog platform sunsets).
5. Robots.txt change blocking Wayback retroactively (rare but does
   happen).

For cases 2 and 4 in particular, an archive made **at admission** is
the only evidence that survives. Do not defer archival.

---

**Maintainer note:** if archival ever becomes a CI hard-gate, the
implementation goes in `.github/workflows/banned-words.yml` as a new
job; do not add a separate workflow file.
