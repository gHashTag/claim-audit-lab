<!-- UNREGISTERED DRAFT. Not listed in cases.yaml, so it is not in the register.
     FRAMEWORK.md: a case file without a Section 9 symmetric mirror is rejected
     from the register until the mirror is added. Held here rather than in cases/
     so that the repository's own gates stop failing on work that is, by the
     framework's own rule, not yet a case. -->

# CASE-17: Timothy McGirl (grapheneaffiliate) -- Geometric Standard Model

**Subject:** Timothy McGirl (independent researcher).
**Affiliation:** Independent; publishes on Zenodo and GitHub as "grapheneaffiliate."
**Programme:** Derivation of 26-58 fundamental constants from E8->H4 icosahedral geometry with zero free parameters.
**Audit date:** 2026-06-16
**Maintainer:** @gHashTag
**Status:** draft
**Last update:** 2026-06-16

---

## 1. Identity

McGirl published "Geometric Standard Model (GSM) v26.0" on Zenodo (December 14, 2025). GitHub repositories include:
- `grapheneaffiliate/e8-phi-constants` -- 58 constants from E8->H4
- `grapheneaffiliate/Geometric-Standard-Model` -- 26 constants from E8 vacuum structure
- `grapheneaffiliate/p-vs-np-phi-complexity` -- P vs NP via phi-witness geometry

**Primary references:**
- Zenodo (Dec 2025) -- McGirl, "Geometric Standard Model (GSM) v26.0"
- https://github.com/grapheneaffiliate/e8-phi-constants
- https://github.com/grapheneaffiliate/Geometric-Standard-Model

---

## 2. Claims

| # | Claim | Evidence | Assessment |
|---|-------|----------|------------|
| Mc1 | 58 constants from E8->H4 | Python solver (`gsm_solver.py`) | **Unverified** |
| Mc2 | Zero free parameters | Asserted | **Unverified** |
| Mc3 | Bell bound S = 4 ? phi ~ 2.382 | Algebraic proof | **Formal but untested** |
| Mc4 | Lean 4 proofs (6 compiled) | [yes] Present | **Partial verification** |
| Mc5 | Brute-force vertex tests (8,100 quadruples) | [yes] Performed | **Empirical check** |
| Mc6 | arXiv presence | [no] None found | **Absent** |
| Mc7 | Peer review | [no] None identified | **Absent** |

---

## 3. Critical Assessment

**Endorsement gap:** McGirl has no arXiv papers under the name "Timothy McGirl." arXiv requires endorsement for hep-th; McGirl appears to lack it. This is a significant publication barrier.

**Lean proofs:** 6 compiled Lean 4 proofs provide more verification than most competitors, but still far fewer than Trinity's 166 Coq theorems.

**Differentiation from Trinity:**
- McGirl: 58 constants, 6 Lean proofs, Python solver
- Trinity: 23 constants, 166 Coq proofs, FPGA hardware, explicit tolerances

---

## 4. Risk Assessment

**Threat level:** LOW -- Effectively stalled. Single Zenodo deposit (Dec 2025), no arXiv presence, no follow-up work indexed. The endorsement barrier means McGirl is unlikely to publish on arXiv in the near term. However, the GitHub repositories show active code development.

---

## 5. Audit Trail

- 2026-06-16 -- Wave Loop 9 competitive analysis
- 2026-06-16 -- Added to claim-audit-lab register

*phi^2 + 1/phi^2 = 3 | Honest audit, no adjectives*
