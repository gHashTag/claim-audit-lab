# CASE-11: Robert W. Gray, Lynnclaire Dennis & Louis H. Kauffman -- The Mereon System and 600-Cell

**Subject:** Robert W. Gray (geometer), Lynnclaire Dennis (systems theorist), Louis H. Kauffman (mathematician, University of Illinois at Chicago).
**Affiliation:** Independent / UIC.
**Programme:** Exact geometric correspondence between the Mereon 120-polyhedron and the 600-cell via H3 subset H4 symmetry; realization of E6, E7, E8 through McKay correspondence.
**Audit date:** 2026-06-16
**Maintainer:** @gHashTag
**Status:** draft
**Last update:** 2026-06-16

---

## 1. Identity

Gray, Dennis and Kauffman published arXiv:2604.00255v1 (March 31, 2026): "The Mereon System, the 600-Cell, and the Exceptional Algebras E6, E7, E8." The paper claims an exact 62/62 vertex match between the Mereon M120p (H3 symmetry) and the 600-cell (H4 symmetry). Kauffman is a well-known knot theorist and mathematician at UIC with extensive peer-reviewed publications.

**Primary references:**
- arXiv:2604.00255v1 -- Gray, Dennis, Kauffman (2026), "The Mereon System, the 600-Cell, and the Exceptional Algebras E6, E7, E8"
- arXiv:2311.01486 -- Moxness (2023), "Explicit E8 <-> H4 isomorphism via golden-ratio-scaled copies of the 600-cell"
- arXiv:2408.06745 -- Berg & Wiedemann (2025), "E8-folding construction of H4-graded groups," *Journal of Algebra*

---

## 2. Claims

| # | Claim | Evidence | Assessment |
|---|-------|----------|------------|
| G1 | Exact vertex correspondence Mereon M120p <-> 600-cell (62/62) | Geometric proof in paper | **Plausible** -- H3 subset H4 is mathematically sound |
| G2 | E8 realized via McKay correspondence on binary icosahedral group 2I | Algebraic proof | **Plausible** -- Standard mathematical result |
| G3 | Trefoil knot <-> Brieskorn E8 singularity linkage | Topology argument | **Plausible** -- Known connection |
| G4 | SM fermion masses derived from geometric correspondence | **Not present** in paper | **Absent** |
| G5 | Numerical formulas with error bounds for SM parameters | **Not present** | **Absent** |
| G6 | Machine-checkable proofs | **Not present** | **Absent** |

---

## 3. Comparison with the lab's own programme

Recorded so the symmetric mirror in Section 9 has a stated basis. The columns
are inventory, not merit: under an unbounded search space a larger count is a
larger [Risk], not a stronger result (FRAMEWORK.md (b)).

| Dimension | Gray et al. | Lab (Trinity) |
|-----------|-------------|--------------|
| Machine proofs | None | 166 Rocq theorems |
| SM parameter formulas | None | 23 phi-monomials |
| Error tolerances | None | Explicit (0.1%-10%) |
| Hardware | None | FPGA sacred opcodes |
| Predictions | None | 4 testable predictions |
| Free inputs | Unknown | **0** (phi, pi, e only) |

---

## 4. Evidence calibration

**Venue, FRAMEWORK.md (d):** an arXiv preprint. No venue weakness is recorded
against the specific geometric claims G1-G3.

**Scope, FRAMEWORK.md (b):** Gray et al. state geometric correspondences and do
not state SM parameter formulas. Under the framework that absence removes
look-elsewhere exposure rather than counting against the programme. The lab's
own phi-monomial formulas carry that exposure; Section 9 labels both.

---

## 5. Audit Trail

- 2026-06-16 -- Wave Loop 9 competitive analysis
- 2026-06-16 -- Added to claim-audit-lab register
- 2026-08-10 -- Section 9 symmetric mirror added; non-ASCII transliterated

---

## 9. Symmetric mirror (MANDATORY)

Per FRAMEWORK.md ("Symmetric mirror") and CHARTER.md s 5, comparable claims from
the lab's own work are classified here under the same five labels. Lab rows cite
CASE-00, the global self-audit.

| Subject's claim | Our comparable claim | Both labelled |
|-----------------|----------------------|---------------|
| G1: Mereon M120p <-> 600-cell vertex correspondence 62/62 via H3 subset H4 | CASE-00 s 4: the closed rule `e = round((N-1)/phi^2)` reproduces the realised exponent widths for GF4..GF256, 9/9 | Both **[Verified]** under FRAMEWORK.md (a): exact-by-construction, re-derivable from definitions in a few lines, no fitted parameter |
| G2: E8 realised via McKay correspondence on the binary icosahedral group 2I | CASE-00 s 4: the Lucas identity `phi^{2n} + phi^{-2n} = L_{2n}`, a Binet-formula corollary explicitly recorded as not original to the lab | Both **[Verified]** as standing mathematical results. Neither is original to the claimant, and neither carries physical content on its own |
| G4/G5: SM fermion masses and numerical SM formulas from the correspondence -- **not claimed** by Gray et al. | Section 3 above: Trinity's 23 phi-monomials for SM parameters at "0 free inputs (phi, pi, e only)" | Subject makes no such claim and therefore incurs no entry. The lab's claim is **[Risk]** under FRAMEWORK.md (b): the space of expressions a (phi, pi, e) monomial alphabet can generate is not bounded and no look-elsewhere correction is reported. CASE-00 s 7 already records the lab's own control result that phi-free grammars of equal cardinality reach comparable compression |

**What the symmetry is.** Gray et al.'s geometric results and the lab's ladder
rule earn [Verified] for the same reason: each is an identity re-derivable from
its own definitions, and each stops at the mathematical object. The asymmetry
runs opposite to the direction Section 3 implies. Section 3 reads the absence of
SM parameter formulas in Gray et al. as a gap; under the framework that absence
is why Gray et al. carry no [Risk] row, while the lab's extension of H4 geometry
into SM parameter values does.

**Joint Fpath.** One pre-registered experiment resolves both at once: a
matched-cardinality control alphabet (phi, pi, e, sqrt(2), sqrt(3), small
integers) applied to (a) any SM-parameter reading later attached to the H3/H4
correspondence by either programme and (b) the lab's 23 phi-monomials, scored
under BH-FDR at q=0.05 against a target list fixed before the fit. If the
phi-specific readings do not beat what phi-free alphabets of equal cardinality
achieve, both fall to [Risk] and the geometric [Verified] rows above are
untouched -- which is exactly the boundary this case draws.

---

*phi^2 + 1/phi^2 = 3 | Honest audit, no adjectives*
