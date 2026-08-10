# Conflicts of Interest

This file is the lab's structural-conflict declaration. It exists because
the lab's symmetric-mirror rule (FRAMEWORK.md, CHARTER.md s 5) makes
maintainer COI epistemically load-bearing, not optional.

---

## Maintainer-author overlap

The maintainer of this repository (Dmitrii Vasilev, `@gHashTag`) is also
an author of three of the projects audited in `cases/CASE-00-self-audit.md`:

- `gHashTag/trios-trainer-igla` (IGLA RACE training pipeline)
- `gHashTag/goldenfloat-preprint` (GoldenFloat ladder preprint)
- `gHashTag/phi-paper` (Pellis-Vasilev-Olsen short paper)

This overlap is the central reason CASE-00 exists. The lab's audit of its
own work uses the same framework, the same banned-word discipline, and the
same symmetric-mirror requirement as every external case.

Pitfall C2 (`methodology/README.md`) states the discipline explicitly:
**the same severity criterion that places an audited claim in [Risk]
applies equally to the lab's own claims.**

---

## Specific conflicts

| Conflict | Affected case | How handled |
|---|---|---|
| Maintainer is author of IGLA / GoldenFloat / phi-paper | CASE-00 self-audit | All claims labelled under the same framework; retracted claim ([Retracted] delta_CP = 3 / phi^2) recorded plainly. |
| Maintainer is co-author with Scott Olsen on the Pellis-Vasilev-Olsen short paper | (Olsen is ADJACENT) | Olsen is COI-excluded from being a primary audit subject. His contribution is recorded in CASE-00 and in the symmetric-mirror sections of CASE-02, CASE-03, CASE-04. See `phi_theorists_catalog.md` entry #9. |
| **Maintainer is co-author with Stergios Pellis on the same paper** -- Pellis is Strand III, per CASE-15, with approval recorded via letters 2026-06-07/06-08 | **CASE-15 and CASE-21, which audit him as a primary subject** | **UNRESOLVED, recorded 2026-08-10.** See "The Pellis asymmetry" below. |
| Maintainer has historical email correspondence with several catalog entries (Stakhov, Pellis, Olsen) | CASE-02 (Stakhov), CASE-09+ (when written) | Correspondence is not cited as evidence; only published primary sources are. If correspondence is used to confirm a subject's stated view, the relevant message is shared with the subject for inclusion in Section 12. |
| Maintainer has pending submissions to Foundations of Physics, arXiv cs.AR, and ARITH 2027 that build on phi-architecture claims | All cases that mention phi-as-architecture-prior | The submissions are disclosed in `task-status-board` and CASE-00; the lab does not modify a verdict to favour a submission. Quiet relabelling is forbidden under CHARTER s 8. |

---

## The Pellis asymmetry (unresolved, recorded 2026-08-10)

The short paper at `gHashTag/phi-paper` is named, in this file's own line
above, **Pellis-Vasilev-Olsen**. It has three authors. This declaration
excludes **one** of the two non-maintainer co-authors from being a primary
audit subject.

| Co-author | Declared here | Audited as a primary subject? |
|---|---|---|
| Scott Olsen | COI-excluded, ADJACENT, contribution recorded in CASE-00 | No -- catalog entry only |
| **Stergios Pellis** | mentioned only under "historical email correspondence" | **Yes -- CASE-15 and CASE-21** |

`CONTRIBUTING.md` s 3 states the rule this bears on: *"Proposals naming a
current collaborator of the lab maintainers (currently: Scott Olsen) are
declined as primary audit subjects; their contribution is recorded inside
CASE-00 and the symmetric-mirror sections of related cases."* The parenthetical
names one collaborator. The co-author list names two.

**What is verified.** Pellis's co-authorship is not in doubt and is not an
inference from the paper title: CASE-15 records him as Strand III with approval
received via letters dated 2026-06-07 and 2026-06-08. His identity was
confirmed against primary sources on 2026-08-10 (see `PROMOTION-LEDGER.md`);
CASE-15 had previously recorded the given name incorrectly, which is part of
why the overlap went unnoticed.

**What is not decided here, and why.** Three readings are open, and choosing
between them changes what the register contains, so it is a maintainer
decision and not an automated one:

1. The exclusion is correct and simply under-documented for Pellis -- in which
   case CASE-15 and CASE-21 should be withdrawn as primary audits and folded
   into CASE-00 and the symmetric-mirror sections, as was done for Olsen.
2. Auditing a co-author is the *stronger* symmetric position -- CASE-15 was
   opened deliberately under a "co-author rule" and reads that way -- in which
   case the Olsen exclusion is the anomaly and `CONTRIBUTING.md` s 3 should say
   so explicitly rather than naming one person.
3. The two co-authors differ in some respect that justifies different handling.
   No such difference is documented anywhere in this repository.

**Why this is recorded rather than left for the next revision.** A register
whose premise is symmetric treatment, excluding one co-author from audit while
auditing the other twice, is the single most damaging finding an external
reviewer could make about it -- and it would be correct. Recording it before it
is found is the same discipline the lab applies to its own retracted claims.
Until it is resolved, both readings are visible to any reader of this file.

---

## What the lab does NOT claim about its own work

To avoid the asymmetric-standards pitfall (C2):

- **Not [Verified]:** that phi is a better architecture prior than non-phi
  controls. (This is [Open conjecture] with the Fpath stated in
  `igla-phi-architecture` skill.)
- **Not [Verified]:** that the GoldenFloat ladder beats posit/MX/takum at
  matched bit budgets. (This is [Open conjecture]; F2/F3 ablation is the
  Fpath.)
- **Not [Verified]:** that the F2 mediation framework is the only or best
  causal-mediation toolkit for ML. (CMAverse / DoWhy cover overlapping
  ground; F2's differentiator is reproducibility-discipline, not breadth.)
- **Not [Verified]:** that the lab's own 5-label taxonomy is correct in
  the limit. (See pitfall C10. The taxonomy itself is [Open conjecture].)

The lab's own [Retracted] items are also disclosed: `delta_CP = 3 / phi^2`
was withdrawn in 2026; this is recorded permanently in CASE-00 Section 8.

---

## Funding disclosure

As of 2026-06-02, the maintainer's work on the three audited projects is
self-funded, with the following partial external relationships:

- **DARPA CLARA** (Computational Learning and Reasoning) -- award decision
  pending; if awarded, the lab will record contract start in CASE-00 and
  in the relevant skill files. The CLARA award is a competitively-awarded
  government contract for the IGLA work; it is *not* a prize or grant for
  the GoldenFloat ladder or the phi-paper.
- **No other institutional funding** for the lab itself
  (`claim-audit-lab`).
- **No commercial sponsorship** of any kind.

If funding changes, this file is updated within 7 days and the change is
recorded in `PROMOTION-LEDGER.md`.

---

## What the COI rules forbid

- Maintainer SHALL NOT be the sole reviewer of a CASE file that touches a
  project the maintainer authored. CASE-00 is the exception by
  construction (it is the self-audit); external review is welcomed via
  the Subject Reply / Factual Correction flow in `CONTRIBUTING.md`.
- Maintainer SHALL NOT silently relabel a self-audit claim to favour an
  external submission. Label changes require `PROMOTION-LEDGER.md`
  entries (CHARTER s 8).
- Maintainer SHALL NOT exclude a candidate from `phi_theorists_catalog.md`
  on the basis of personal preference. Inclusion is determined by the
  intake filter in `CONTRIBUTING.md` s 3.

---

## How to challenge a COI handling

If a reader believes the lab has handled a COI badly, the inbound flow is
the **Factual correction** issue template (`.github/ISSUE_TEMPLATE/factual-correction.yml`).
Suggested wording: "CASE-NN section X cites Y; my reading is that this
section underweights / overweights [evidence] because of the maintainer's
COI on [project]".

The lab responds within 7 days per the CONTRIBUTING.md SLA.

---

**Last update:** 2026-08-10 (Pellis co-authorship recorded as an unresolved
COI; see "The Pellis asymmetry"). Previous: 2026-06-02.
