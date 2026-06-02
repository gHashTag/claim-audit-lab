# Changelog

All notable changes to this repository are recorded here in reverse
chronological order. Labels follow Keep a Changelog conventions
(`Added` / `Changed` / `Fixed`) where relevant; label changes to
individual CASE files are recorded in `PROMOTION-LEDGER.md`, not here.

## [v0.2-prereg] -- 2026-06-02

Methodology hardening loop. The framework itself is now registered as
`[Open conjecture]` (see `data/labels.json::framework_self_label`) with
an explicit Fpath: a blind inter-rater study (Loop 2, Q3 2026) is the
first formal falsifier. This release is tagged `v0.2-prereg` and
deposited at Zenodo as the freeze-hash anchor for that study.

### Added

- `methodology/README.md` -- methodology scaffold + 10 citations
  (Popper / Lakatos / Mayo / Ioannidis / Gelman-Loken / ASA /
  Gross-Vitells / Open Science Collaboration / Pearl / Laudan) + 10
  pitfalls (C1-C10).
- `CONTRIBUTING.md` -- subject-reply, factual-correction, new-case
  workflows; SLA: reply 14d / correction 7d / proposal 21d.
- `COI.md` -- maintainer-author overlap, Olsen ADJACENT, DARPA CLARA
  disclosed.
- `data/scorecard.json` -- 7-case machine-readable count.
- `data/labels.json` -- machine-readable taxonomy with downgrade
  factors mirroring (in spirit, not in operational rule) the GRADE
  pattern; framework_self_label = `[Open conjecture]`.
- `PROMOTION-LEDGER.md` -- append-only public log of every label
  change; bootstrap 7 rows for v0.2 baseline.
- `scripts/archive-helper.md` -- manual Wayback workflow for link-rot
  mitigation.
- `.github/ISSUE_TEMPLATE/` -- three forms (subject-reply,
  factual-correction, new-case-proposal).
- `.github/PULL_REQUEST_TEMPLATE.md` -- PR checklist.
- `.github/workflows/banned-words.yml` -- two new jobs (`ascii-only`,
  `symmetric-mirror-required`) and a scheduled non-blocking weekly
  `link-check`.
- `.github/workflows/mlc_config.json` -- link-check config.
- README scorecard dashboard with totals row.

### Changed

- `templates/CASE-TEMPLATE.md` -- now carries YAML front-matter
  (`case_id`, `primary_source_uri`, `archive_uri`, `depends_on`,
  `reviewers`, `status`, `overall_class`) and a mandatory Section 0
  signalling-question block (3 questions). Applies to NEW cases only;
  CASE-00..06 are NOT retrofitted (worked example: CASE-05).

### Notes

- v0.2 baseline counts across 7 CASE files: 28 [Verified] + 10
  [Empirical fit] + 11 [Open conjecture with Fpath] + 20 [Risk] + 4
  [High-risk] + 2 [Retracted] = 75 claims.
- Cleanest [Open conjecture] with executable Fpath: CASE-05
  (Kramer-Klimesch golden EEG rhythms).
- CI self-trip caught and fixed mid-loop: PR_TEMPLATE.md tripped the
  banned-words check on the example tokens; rephrased to point to the
  fenced block in `FRAMEWORK.md`. This is exactly the kind of
  self-trip the framework is designed to catch on outside contributors.

### Open weaknesses NOT closed in this release

- **W4 -- link rot.** Archival is manual; scheduled CI link-check only
  warns. Kept manual because Wayback's Save Page Now API is
  rate-limited and flaky CI erodes trust.
- **W11 -- blind-rater reliability.** No inter-rater test has been
  run. This is the single biggest open methodological hole and is the
  first concrete falsifier for `framework_self_label`. Designed as
  the deliverable for Loop 2 (Q3 2026).

## [v0.1] -- 2026-05-30 (unreleased, no tag)

Bootstrap. CASE-00 self-audit and CASE-01..06 (Savchenko, Stakhov,
El Naschie, Petoukhov, Kramer-Klimesch, de Groot). FRAMEWORK,
CHARTER, banned-words CI.

---

**End of CHANGELOG.**
