---
case_id: CASE-12
subject_name: "Vasilev II (computational sweep) + Pellis III (MDL-optimality framing)"
subject_affiliation: "phi-paper collaboration (LOCAL ONLY, Pellis-gated)"
programme: "v2.3 BNF equivalence-class rank result for G_phi = \\varphi^2 + \\varphi^{-2}"
primary_source_uri: "gHashTag/phi-paper (LOCAL ONLY)"
archive_uri: "phi-paper/reproducibility/v23/"
audit_date: 2026-06-07
last_update: 2026-06-07
maintainer: "@gHashTag"
reviewers: []
depends_on: [CASE-08]
status: draft
overall_class: "[Open conjecture]"
---

# CASE-12: v2.3 BNF Equivalence-Class Rank 2/394 for G_phi

**Subject:** Vasilev II (computational sweep) + Pellis III (theoretical framing
of MDL-optimality vs uniqueness)
**Programme:** v2.3-draft phi-paper, sec.6.3 and sec.6.4; Conj 7.6 and Conj 7.7
**Audit date:** 2026-06-07
**Maintainer:** @gHashTag
**Status:** draft (HARD GATING: not public until Pellis approval)
**Predecessor:** CASE-08 (rank 2/1000 raw, no anti-cancel filter)

---

## Summary

CASE-12 records the v2.3 reframing of the BNF equivalence-class result
introduced in CASE-08. The predecessor established raw rank 2/1000; this case
records the anti-cancel-filtered result: rank 2 of 394 essential phi-native
forms. The claim status is **[Open conjecture]** (\\Conj) for the same
structural reasons as CASE-08, plus the reframing caveat documented below.

## Claim (one-paragraph)

See `claim.md`.

## Numerical evidence

See `evidence.md`.

## Falsification path

See `fpath.md`.

## Current status

See `status.md`.

## Sources and reproducibility

See `sources.md`.

---

## 0. Signalling question

**Q0.1** -- What single executable experiment moves the largest claim out of
[Open conjecture]?

> Extend BNF depth to 3 using the same anti-cancellation filter, MDL proxy,
> and sympy.simplify harness; if G_phi = \\varphi^2 + \\varphi^{-2} retains
> rank <= 10 across depth-3 grammar with the essential filter, the conjecture
> gains strong support. If G_phi drops below rank 10, the v2.3 claim is
> falsified under the grammar-extension Fpath.

**Q0.2** -- Symmetric mirror commitment.

> CASE-08 is the direct predecessor and symmetric mirror. CASE-12 differs only
> in applying the anti-cancellation filter (494 -> 394 essential forms).
> The lab's own work (v2.3 phi-paper) is audited here under the same
> framework applied to all external programmes.

**Q0.3** -- Why is this case being added now?

> [x] Programme overlaps a [Verified]/[Open] claim of ours and a symmetric
>     audit is owed. The v2.3 manuscript reframes the CASE-08 rank result
>     (raw 2/1000 -> essential 2/394 after anti-cancel filter); that reframing
>     requires a new CASE entry to preserve audit-trail fidelity.

---

## 9. Symmetric mirror (MANDATORY)

| Subject's claim | Our comparable claim | Both labelled |
|-----------------|----------------------|---------------|
| G_phi ranks 2/394 essential phi-native forms (depth<=2, anti-cancel) | CASE-08: G_phi ranks 2/394 in the same harness (same result, predecessor entry) | [Open conjecture] |
| Rank 1 is commutative twin \\varphi^{-2} + \\varphi^2 | Commutative equivalence is [Verified] by construction | [Verified] algebraic identity; [Open conjecture] for MDL-rank interpretation |

CASE-12 audits the same programme as CASE-08 after the anti-cancellation
filter reduces the essential class from the raw count to 394. The joint
Fpath for both cases is identical: demonstrate a strictly shorter phi-native
form (lower MDL cost under the same encoding) that algebraically equals 3
and is not a commutative permutation of G_phi. Resolving this Fpath would
simultaneously close CASE-08 and CASE-12 in either direction.

---

## 10. Audit summary

The strongest part of the programme is the algebraic identity
\\varphi^2 + \\varphi^{-2} = 3 (Lucas L_2 = 3), which is [Verified]
by construction. The v2.3 rank-2/394 claim is [Open conjecture] because
the grammar is bounded (depth <= 2), the MDL is a string-length proxy, and
the equivalence-class detection relies on sympy.simplify rather than a
formal e-graph rewriter. The weakest point is the heuristic
anti-cancellation filter: it is well-defined and reproducible at the byte
level (frozen capsule), but its "essential-ness" criterion is not
derived from a formal MDL prior. The single experiment that would move the
largest claim toward [Verified] is a depth-3 BNF sweep confirming rank <= 10
for G_phi with independent replication (Grunwald or Hutter target). The
lab's symmetric position is identical to CASE-08: the maintainers want this
result to be true and have applied the same matched-cardinality discipline
they demand of external programmes.

---

**End of CASE-12 README.**
