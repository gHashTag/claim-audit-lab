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
| Maintainer has historical email correspondence with several catalog entries (Stakhov, Pellis, Olsen) | CASE-02 (Stakhov), CASE-09+ (when written) | Correspondence is not cited as evidence; only published primary sources are. If correspondence is used to confirm a subject's stated view, the relevant message is shared with the subject for inclusion in Section 12. |
| Maintainer has pending submissions to Foundations of Physics, arXiv cs.AR, and ARITH 2027 that build on phi-architecture claims | All cases that mention phi-as-architecture-prior | The submissions are disclosed in `task-status-board` and CASE-00; the lab does not modify a verdict to favour a submission. Quiet relabelling is forbidden under CHARTER s 8. |

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

**Last update:** 2026-06-02.
