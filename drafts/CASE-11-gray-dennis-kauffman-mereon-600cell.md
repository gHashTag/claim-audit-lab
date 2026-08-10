<!-- UNREGISTERED DRAFT. Not listed in cases.yaml, so it is not in the register.
     FRAMEWORK.md: a case file without a Section 9 symmetric mirror is rejected
     from the register until the mirror is added. Held here rather than in cases/
     so that the repository's own gates stop failing on work that is, by the
     framework's own rule, not yet a case. -->

# CASE-11: Robert W. Gray, Lynnclaire Dennis & Louis H. Kauffman -- The Mereon System and 600-Cell

**Subject:** Robert W. Gray (geometer), Lynnclaire Dennis (systems theorist), Louis H. Kauffman (mathematician, University of Illinois at Chicago).
**Affiliation:** Independent / UIC.
**Programme:** Exact geometric correspondence between the Mereon 120-polyhedron and the 600-cell via H3?H4 symmetry; realization of E6, E7, E8 through McKay correspondence.
**Audit date:** 2026-06-16
**Maintainer:** @gHashTag
**Status:** draft
**Last update:** 2026-06-16

---

## 1. Identity

Gray, Dennis and Kauffman published arXiv:2604.00255v1 (March 31, 2026): "The Mereon System, the 600-Cell, and the Exceptional Algebras E6, E7, E8." The paper claims an exact 62/62 vertex match between the Mereon M120p (H3 symmetry) and the 600-cell (H4 symmetry). Kauffman is a well-known knot theorist and mathematician at UIC with extensive peer-reviewed publications.

**Primary references:**
- arXiv:2604.00255v1 -- Gray, Dennis, Kauffman (2026), "The Mereon System, the 600-Cell, and the Exceptional Algebras E6, E7, E8"
- arXiv:2311.01486 -- Moxness (2023), "Explicit E8 ? H4 isomorphism via golden-ratio-scaled copies of the 600-cell"
- arXiv:2408.06745 -- Berg & Wiedemann (2025), "E8-folding construction of H4-graded groups," *Journal of Algebra*

---

## 2. Claims

| # | Claim | Evidence | Assessment |
|---|-------|----------|------------|
| G1 | Exact vertex correspondence Mereon M120p ? 600-cell (62/62) | Geometric proof in paper | **Plausible** -- H3?H4 is mathematically sound |
| G2 | E8 realized via McKay correspondence on binary icosahedral group 2I | Algebraic proof | **Plausible** -- Standard mathematical result |
| G3 | Trefoil knot ? Brieskorn E8 singularity linkage | Topology argument | **Plausible** -- Known connection |
| G4 | SM fermion masses derived from geometric correspondence | **Not present** in paper | **Absent** |
| G5 | Numerical formulas with error bounds for SM parameters | **Not present** | **Absent** |
| G6 | Machine-checkable proofs | **Not present** | **Absent** |

---

## 3. Differentiation from Trinity S^3AI

| Dimension | Gray et al. | Trinity S^3AI |
|-----------|-------------|--------------|
| Machine proofs | [no] None | [yes] 166 Rocq theorems |
| SM parameter formulas | [no] None | [yes] 23 phi-monomials |
| Error tolerances | [no] None | [yes] Explicit (0.1%-10%) |
| Hardware | [no] None | [yes] FPGA sacred opcodes |
| Predictions | [no] None | [yes] 4 testable predictions |
| Free inputs | Unknown | **0** (phi, pi, e only) |

---

## 4. Risk Assessment

**Threat level:** MEDIUM -- Kauffman's name lends credibility, but the paper is geometric/algebraic without phenomenological claims. No direct competition on SM parameter derivation.

**Precedence:** Gray et al. do not claim SM parameter formulas; they claim geometric correspondences. Trinity's phi-monomial formulas are an independent (and narrower) claim.

---

## 5. Audit Trail

- 2026-06-16 -- Wave Loop 9 competitive analysis
- 2026-06-16 -- Added to claim-audit-lab register

*phi^2 + 1/phi^2 = 3 | Honest audit, no adjectives*
