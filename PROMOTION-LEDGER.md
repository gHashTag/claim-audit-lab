# PROMOTION-LEDGER

Public, append-only record of every label change in the case register.
A label change is any movement of a claim between the five labels
([Verified], [Empirical fit], [Open conjecture], [Risk], [High-risk],
[Retracted]) at the case level, or any change to the `overall_class`
field in a CASE file's YAML front-matter.

This ledger exists because **label changes without an audit trail are
themselves a credibility failure**. Every entry must cite the commit
SHA, the reviewer (if external), and the documented reason. Entries
are never deleted; corrections append a new row with reason
"correction".

The format mirrors the FL-001..FL-005 falsification ledger pattern
used in `gHashTag/goldenfloat-preprint` and the IGLA epic.

## Schema

| Column | Meaning |
|---|---|
| Date | ISO date of the commit that landed the change |
| Case | CASE-NN identifier |
| Claim id | Section number or short claim handle inside the case |
| From | Previous label (or `none` if newly added) |
| To | New label |
| Reason | One of: initial-classification / new-evidence / Fpath-executed / control-matched / venue-downgrade / formal-retraction / correction / framework-revision |
| Commit | Short SHA |
| Reviewer | Maintainer handle, or external reviewer name + affiliation |

## Bootstrap rows (2026-06-02)

The seven rows below record the initial classification of each CASE
file as of the v0.2 register. They are the baseline; future changes
append below.

| Date | Case | Claim id | From | To | Reason | Commit | Reviewer |
|---|---|---|---|---|---|---|---|
| 2026-05-30 | CASE-00 | self-audit overall_class | none | mixed | initial-classification (self-audit, 4 [Verified] + 1 [EF] + 2 [Open] + 2 [Risk] + 1 [Retracted]) | b7efbf7 | @gHashTag |
| 2026-05-31 | CASE-01 | Savchenko Pointer Architecture overall | none | mixed | initial-classification (7 [Verified] + 3 [EF] + 4 [Open] + 3 [Risk] + 1 [Retracted]; counted from CASE-01.md) | b7efbf7 | @gHashTag |
| 2026-05-31 | CASE-02 | Stakhov Mathematics-of-Harmony overall | none | mixed | initial-classification (6 [Verified] + 1 [EF] + 2 [Open] + 4 [Risk] + 1 [High-risk]) | b7efbf7 | @gHashTag |
| 2026-05-31 | CASE-03 | El Naschie E-infinity overall | none | high_risk | initial-classification (3 [Verified] + 0 [EF] + 0 [Open] + 2 [Risk] + 3 [High-risk]; 2012 UK High Court Naschie v. Macmillan judgement cited factually, not as label trigger) | b7efbf7 | @gHashTag |
| 2026-05-31 | CASE-04 | Petoukhov genetic-code phi overall | none | mixed | initial-classification (3 [Verified] + 2 [EF] + 1 [Open] + 4 [Risk]) | b7efbf7 | @gHashTag |
| 2026-05-31 | CASE-05 | Kramer-Klimesch positive-control overall | none | mixed | initial-classification, positive-control case (2 [Verified] + 2 [EF] + 1 [Open] + 2 [Risk]) | b7efbf7 | @gHashTag |
| 2026-05-31 | CASE-06 | de Groot phi-attractor positive-control overall | none | mixed | initial-classification, positive-control case (3 [Verified] + 1 [EF] + 1 [Open] + 3 [Risk]) | b7efbf7 | @gHashTag |

## Append-only rule

New entries are added at the bottom in chronological order. Entries
above this line are immutable. Correcting an old row requires a new
row with `Reason = correction` and the corrected values; the original
row stays as it was.

## Cross-references

- Schema and rationale: `methodology/README.md` Section 5
  (claim-status discipline) and Section 6 (link-rot and audit-trail
  failure modes).
- Label definitions: `data/labels.json` (machine-readable taxonomy).
- Case counts at v0.2 baseline: `data/scorecard.json`.

---

**End of ledger.**
