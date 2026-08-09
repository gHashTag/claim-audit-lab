# CASE-18: Agyemang (AIMS Ghana) -- Eleven Fundamental Constants from E8 Boundary Geometry

**Subject:** Agyemang (affiliation: African Institute for Mathematical Sciences, Ghana).
**Affiliation:** AIMS Ghana.
**Programme:** Derivation of 11 fundamental constants from E8 x E8 heterotic string root lattice (level k=1).
**Audit date:** 2026-06-16
**Maintainer:** @gHashTag
**Status:** draft
**Last update:** 2026-06-16

---

## 1. Identity

Agyemang published on Zenodo:20525049 (June 3, 2026): "Eleven Fundamental Constants from E8 Boundary Geometry." Claims derivation of alpha^-1, three gauge couplings, four gravitational quantities, cosmological constant, and electron mass from a single E8 root lattice with zero free parameters.

**Primary references:**
- Zenodo:20525049 -- Agyemang (2026), "Eleven Fundamental Constants from E8 Boundary Geometry"

---

## 2. Claims

| # | Claim | Evidence | Assessment |
|---|-------|----------|------------|
| A1 | alpha^-1 = 137.035999086 (0.11 sigma precision) | Numeric calculation | **No stated error budget** |
| A2 | 11 constants from E8 x E8 with zero free inputs | Asserted, no derivation shown | **Unverified** |
| A3 | Inputs: dim=248, h*=30, c=8 | Listed as "inputs" but claimed as "zero free" | **Contradiction?** |
| A4 | Machine-checkable proofs | None | **Absent** |
| A5 | Error budget / tolerances | None explicit | **Absent** |
| A6 | Testable predictions | None explicit | **Absent** |

---

## 3. Critical Assessment

**Precision without a stated error budget.** The 0.11 sigma figure for alpha^-1
is quoted without a transparent error budget, so it cannot be independently
recomputed. The "zero free parameters" claim stands against three listed inputs
(dim=248, h*=30, c=8), which enter the derivation as fixed constants.

**Comparison with the lab's own programme** (inventory, not merit -- at
unbounded alphabets a larger constant count is a larger [Risk] under
FRAMEWORK.md (b), not a stronger result):
- Scope: 11 constants vs the lab's 23
- Proofs: none vs 166 Rocq theorems
- Hardware: none vs FPGA opcodes
- Predictions: none stated vs 4 stated

---

## 4. Evidence calibration

**Under FRAMEWORK.md (d), venue:** a single Zenodo deposit (June 3, 2026), no
peer review and no citations located at audit date.

**Under FRAMEWORK.md (b), look-elsewhere:** neither the target constant list nor
the generating alphabet is bounded in advance, so no multiple-testing correction
is reportable for the 0.11 sigma figure. The lab's own 23 phi-monomials carry
the identical gap, and CASE-00 s 7 already records the lab's control result that
phi-free grammars of equal cardinality reach comparable compression.

---

## 5. Audit Trail

- 2026-06-16 -- Wave Loop 9 discovery
- 2026-06-16 -- Added to claim-audit-lab register
- 2026-08-10 -- Section 9 symmetric mirror added; non-ASCII transliterated

---

## 9. Symmetric mirror (MANDATORY)

Per FRAMEWORK.md ("Symmetric mirror") and CHARTER.md s 5, comparable claims from
the lab's own work are classified here under the same five labels. Lab rows cite
CASE-00, the global self-audit.

| Subject's claim | Our comparable claim | Both labelled |
|-----------------|----------------------|---------------|
| A2/A3: 11 constants from E8 x E8 at "zero free inputs", while dim=248, h*=30, c=8 are simultaneously listed as inputs | Section 3 above: Trinity's 23 phi-monomials at "0 free inputs (phi, pi, e only)" | Both **[Risk]** under FRAMEWORK.md (b) and (c). In both cases "zero free parameters" counts fitted coefficients and not the choice of alphabet. Under the [Empirical fit] definition, an alphabet or lattice datum selected after the target values are known is itself a post-hoc parameter, so neither programme's zero is a zero |
| A1: alpha^-1 = 137.035999086 quoted at 0.11 sigma | CASE-08 in the register: G_phi = phi^2 + phi^-2 = 3 at MDL-rank 2/394 among essential depth-leq-2 phi-native forms, bootstrap p=0.0039 | Subject's: **[Risk]** -- a headline number with no stated search space, so no look-elsewhere correction is possible. Lab's: **[Open conjecture]** -- the same class of claim, but with a pre-declared enumeration, an anti-cancellation filter and a stated Fpath. The difference between the labels is the reported denominator, not the phenomenon |
| A4/A5/A6: no machine-checkable proofs, no error budget, no testable predictions | CASE-00 s 7: the IGLA RACE v2 BPB-per-format table, circulated by the lab as evidence of phi-ladder competitiveness and demoted to [CLAIM, NEEDS REPRODUCTION] on 2026-06-02 | Both **[Risk]** under (b)/(d). A figure a third party cannot regenerate from public source is not evidence, whoever published it. The lab's demotion was triggered by `git log -S "2.5725"` returning 0 commits at public HEAD `fab7d81` |

**What the symmetry is.** This case turns on the phrase "zero free parameters",
and the lab makes the same claim in the same words about its own constant set.
The framework has no label for "zero free parameters"; it has a definition of
post-hoc parameter that both programmes trip on identically. Recording that here
is what keeps Section 3's "11 constants vs Trinity's 23" from functioning as an
epistemic argument -- at matched, unbounded alphabets, a larger constant count
is a larger [Risk], not a stronger result.

**Joint Fpath.** Fix the target constant list and the generating alphabet in
public before computing, then run the identical matched-cardinality control
alphabet (phi, pi, e, sqrt(2), sqrt(3), small integers, and for the subject the
E8 lattice invariants dim=248, h*=30, c=8) over both constant sets under BH-FDR
at q=0.05. Whichever set does not survive the control moves to [Risk]; a set
that survives with its alphabet declared in advance moves to [Empirical fit]
with a matched control, and only a subsequent held-out confirmation would reach
[Verified].

---

*phi^2 + 1/phi^2 = 3 | Honest audit, no adjectives*
