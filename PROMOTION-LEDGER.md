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

## 2026-08-10 -- self-audit retraction pass (CASE-00 s 4a / s 8a)

A re-examination of the lab's own hardware programme withdrew every phi claim
about silicon. Recorded here per CHARTER.md s 8, because a label change without
an audit trail is itself a credibility failure. Source: the lab's hardware
research record (`fpga-income` skill; `trinity-fpga/research/`).

| Date | Case | Claim id | From | To | Reason | Commit | Reviewer |
|---|---|---|---|---|---|---|---|
| 2026-08-10 | CASE-00 | R1 `phi^k` correct scale grid | [Empirical fit] | [Retracted] | control-matched (APoT-2 at 0.1651% vs 2.4420%, one cycle vs k) | see PR #8 | @gHashTag |
| 2026-08-10 | CASE-00 | R2 `dot_exact` confers advantage | [Verified] | [Retracted] | control-matched (APoT scale dyadic; `Z[1/2]` also a ring) | see PR #8 | @gHashTag |
| 2026-08-10 | CASE-00 | R3 phi wins area 2.22x | [Empirical fit] | [Retracted] | correction (measured at 5-bit field; workload needs 2) | see PR #8 | @gHashTag |
| 2026-08-10 | CASE-00 | R4 phi wins at frozen scale | [Empirical fit] | [Retracted] | control-matched (frozen shift is wiring; APoT 26 vs 64-256) | see PR #8 | @gHashTag |
| 2026-08-10 | CASE-00 | R5 depth-independence is an advantage | [Open conjecture] | [Retracted] | control-matched (compile-time composition free to all) | see PR #8 | @gHashTag |
| 2026-08-10 | CASE-00 | R6 LNS addition costs 10967 LUT | [Verified] | [Retracted] | correction (that was a decoder; honest adder 275 LUT) | see PR #8 | @gHashTag |
| 2026-08-10 | CASE-00 | R7 mesh case is where phi wins | [Open conjecture] | [Retracted] | control-matched (APoT 103 vs Fibonacci step 128) | see PR #8 | @gHashTag |
| 2026-08-10 | CASE-00 | "28 competitors, zero survivors" | [Verified] | [Retracted] | correction (positions-vs-bits; 6 of 17 at equal storage) | see PR #8 | @gHashTag |
| 2026-08-10 | CASE-00 | 323 MHz / 41.2 GOPS, GF16 matmul | [Verified] | [Retracted] | correction (block has no registers; `grep -c posedge` = 0) | see PR #8 | @gHashTag |
| 2026-08-10 | CASE-00 | "TEF best of fixed-field formats" | [Verified] | [Retracted] | correction (mid-group; spread set by field width) | see PR #8 | @gHashTag |
| 2026-08-10 | CASE-00 | takum taper rate 0.117 bits/binade | [Verified] | [Retracted] | correction (category error: line fitted to a ladder) | see PR #8 | @gHashTag |
| 2026-08-10 | CASE-00 | power-law area model `c*M^a` | [Empirical fit] | [Retracted] | Fpath-executed (pre-registered prediction missed by 36.3%) | see PR #8 | @gHashTag |
| 2026-08-10 | CASE-00 | `Z[phi]` closure, exact linear tract | none | [Verified] | initial-classification (machine-checked algebra) | see PR #8 | @gHashTag |
| 2026-08-10 | CASE-00 | accuracy law, exponent cancels | none | [Verified] | initial-classification (derived, then measured on 8 rungs) | see PR #8 | @gHashTag |
| 2026-08-10 | CASE-00 | diagnostic theorem `M_eff` | none | [Verified] | initial-classification (recovers declared mantissa to 0.01 bit) | see PR #8 | @gHashTag |
| 2026-08-10 | CASE-00 | Kraft bound on tapering (T12) | none | [Verified] | initial-classification (derived; runs against the lab's own claim) | see PR #8 | @gHashTag |
| 2026-08-10 | CASE-00 | regime radix irrelevance (T13) | none | [Verified] | initial-classification (refuted the lab's own proposed third class) | see PR #8 | @gHashTag |
| 2026-08-10 | CASE-00 | area law `141 + 2.4455*M^2` | none | [Verified] | initial-classification (R^2 = 0.99963 over 14 widths) | see PR #8 | @gHashTag |
| 2026-08-10 | CASE-00 | trade-curve minimum, binary32 | none | [Verified] | Fpath-executed (predicted before synthesis, 2.3% / 4.7%) | see PR #8 | @gHashTag |

**Note on the shape of this block.** Twelve demotions and seven promotions
landed on the same date. That is not a normal cadence and should not be read as
one: it is a single re-examination pass that had been deferred, and the
deferral is itself the finding recorded in CASE-00 s 8b. The commit column
carries "see PR #8" rather than a SHA because these rows are added in the same
PR that adds the inventory; a follow-up commit should replace them with the
merge SHA once PR #8 lands.

---

## 2026-08-10 -- subject-identity corrections (CHARTER.md s 2)

Two subject-identity collisions were resolved against primary sources. These
are factual corrections under CONTRIBUTING.md s 2, not label changes, and are
recorded here because they change **who** a case is about -- which the ledger
schema does not otherwise capture, and which matters more than a label change.

| Date | Case | Field | From | To | Reason | Evidence | Reviewer |
|---|---|---|---|---|---|---|---|
| 2026-08-10 | CASE-14 | subject_name | Carles Morato de Dalmases | Luis Morato de Dalmases | correction | zenodo.org/records/20443946 and /19112358, fetched 2026-08-10 | @gHashTag |
| 2026-08-10 | CASE-14 | subject_affiliation | Independent (Spain) | CronNet-Holo Initiative | correction | as above | @gHashTag |
| 2026-08-10 | CASE-15 | subject_name | Cosimo Pellis | Stergios Pellis | correction | SSRN 4003636 (cited by CASE-15 itself) and JHEPGC 2023 DOI 10.4236/jhepgc.2023.91021 = SCIRP paperid 122814, fetched 2026-08-10 | @gHashTag |
| 2026-08-10 | CASE-15 | subject_affiliation | Independent (Italy) | Independent | correction (country withdrawn as unverified) | as above | @gHashTag |
| 2026-08-10 | CASE-20 | source date, Zenodo:19112358 | 2025 | 2026-03-19 | correction | zenodo.org/records/19112358, fetched 2026-08-10 | @gHashTag |

**Consequence not resolved by this pass.** CASE-14/CASE-20 are the same
subject, and CASE-15/CASE-21 are the same subject: four case files audit two
people, each pair carrying its own symmetric mirror. Merging or superseding is
a decision about what the register contains and is left to the maintainer.

**COI escalation.** CASE-15 records its subject as Strand III of the
Vasilev-Pellis-Olsen phi-paper. CASE-21 audits that same person while gated as
an ordinary external case. Under CHARTER.md s 3 and COI.md the co-author
notification rule should extend to CASE-21.

**How this was missed.** Both collisions were introduced when the Wave-Loop
batch was filed into the register without checking subject identity against
entries the register already held. The same root cause produced the CASE-12..16
ID collisions. A subject-identity check belongs in the intake path, not in a
later audit.

---



## 2026-08-10 -- s 8b instrument applied to the register (CASE-00 s 8c)

CASE-00 s 10 committed the lab to turning its own comparison-discipline
instrument on its external cases. The pass was run over every entry invoking
FRAMEWORK.md (c).

| Date | Case | Claim id | From | To | Reason | Commit | Reviewer |
|---|---|---|---|---|---|---|---|
| 2026-08-10 | CASE-18 | A2 stated reason | [Risk] (b)+(c) citing the lab's control as evidence | [Risk] (b)+(c) with the lab's control restated as plausibility only | correction | see PR #8 | @gHashTag |
| 2026-08-10 | CASE-21 | P2 stated reason | [Risk] (c), "the same control bears on P2" | [Risk] (c) with the transfer claim withdrawn | correction | see PR #8 | @gHashTag |

**No label changed.** FRAMEWORK.md (c) triggers on a plausible alternative and
holds until a control is ruled out, so plausibility suffices and both entries
remain [Risk] on the same clause. Only the stated reason changed, separating
what was measured from what was inferred. Recorded because the correction is
modest: a pass reporting a label change would be overselling it.

**Rule established:** a control the lab ran against its own claim establishes
plausibility for a claim of the same class; it is not a match against another
programme's claim and may not be cited as one.

**Auditability.** All 48 [Risk]/[High-risk] entries were enumerated by clause.
CASE-05 is the only label resting on (c) alone -- the only place the defect
could have changed an outcome rather than a reason -- and it was checked
directly: it rests on the subject's own published sweep, not on any lab
comparison. An earlier draft of s 8c asserted that every external [Risk]
carries a second independent clause; the enumeration falsified that, and the
correction is recorded in s 8c rather than silently dropped.

## 2026-08-10 -- COI declaration gap recorded (COI.md)

Not a label change. Recorded here because CHARTER.md s 8 and COI.md both make
COI handling epistemically load-bearing, and because the gap was found while
verifying subject identities earlier the same day.

| Date | Document | Finding | Status | Reviewer |
|---|---|---|---|---|
| 2026-08-10 | COI.md | The phi-paper has three authors (Pellis-Vasilev-Olsen). Only Olsen was declared COI-excluded from being a primary audit subject. Stergios Pellis, co-author and Strand III, is audited as a primary subject in CASE-15 and CASE-21. | **UNRESOLVED** -- three readings recorded in COI.md; choosing between them changes what the register contains and is a maintainer decision | @gHashTag |

**Contributing cause.** CASE-15 recorded the co-author's given name incorrectly
until 2026-08-10, which is part of why the overlap between the phi-paper author
list and the audited-subject list went unnoticed.

## 2026-08-10 -- SUPERSEDED: duplicate cases merged, then unwound

The block below recorded merging CASE-20 into CASE-14 and CASE-21 into
CASE-15. It was **superseded the same day** by the hybrid merge with `main`:
PR #7 had already moved those files to `drafts/` as unregistered drafts, so
they are not duplicate *cases* and there was nothing to merge. CASE-14 and
CASE-15 are restored to their registered form, keeping the verified name
corrections. The row is kept rather than deleted, per the append-only rule.

### Original entry (no longer in effect)

## 2026-08-10 -- duplicate cases merged (register structure)

Following the identity corrections above, the two duplicate pairs were merged
on the maintainer's instruction. Four case files audited two people.

| Date | Merged | Into | Subject | Retired to |
|---|---|---|---|---|
| 2026-08-10 | CASE-20 | CASE-14 | Luis Morato de Dalmases | `archive/CASE-20-morato-dalmases-600cell-spectral-triple.md` |
| 2026-08-10 | CASE-21 | CASE-15 | Stergios Pellis | `archive/CASE-21-pellis-unity-formulas-coupling-constants.md` |

**Which file survived, and why.** In both pairs the surviving file is the
template-conformant one (front matter, sections 0-12) whose inventories were
`[PENDING]` stubs, and the retired file is the one carrying the actual claim
table and inventories. The merge therefore fills real content into a valid
shell rather than discarding either.

**Label movements caused by the merge.** None. Every inventory entry keeps the
label and the FRAMEWORK.md clause it carried in the retired file. Two internal
inconsistencies surfaced by the merge were fixed and are recorded as
corrections:

| Date | Case | Item | From | To | Reason |
|---|---|---|---|---|---|
| 2026-08-10 | CASE-14 | M1 in the symmetric mirror | "[Open conjecture] at best" | [Risk] | correction -- the mirror contradicted its own Section 7; FRAMEWORK.md (a) sends a conjecture with no stated falsifier to [Risk] |
| 2026-08-10 | CASE-15 | SCIRP/JHEPGC venue | "[Risk, provisional] ... weak peer-review reputation", unsourced | withdrawn; no venue weakness recorded against P1-P3 | correction -- the merged-in file established that the specific paper is cited in JGP (2024) and CQG (2025), which is checkable, and (d) calibrates evidence for a claim rather than a publisher's standing |

Register: 23 entries -> **21**. The ids CASE-20 and CASE-21 are not reissued.
Retired files are kept unedited under `archive/` so the merge is auditable.

## 2026-08-10 -- manifest defects inherited from main, fixed

Found while merging `main` into PR #8. Neither is a label change; both are
recorded because the manifest is the register's machine-readable contract.

| Date | File | Defect | Fix |
|---|---|---|---|
| 2026-08-10 | cases.yaml | The entry added by PR #7 was indented at column 1 instead of column 3, so the whole manifest **failed to parse**. Nothing on main detects this. | Re-indented under `cases:` |
| 2026-08-10 | cases.yaml | That entry claimed id **CASE-10**, already held by the PHI_BIAS coincidence survey -- a duplicate id | Renumbered to **CASE-18**; file renamed to match; original id recorded in its `public_status` so the change is one line to revert |

Both are the class the `case-index` CI job catches, and that job exists only on
this branch. Landing it is what prevents a recurrence.

---

**End of ledger.**
