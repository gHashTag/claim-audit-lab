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

## 4. [Verified] inventory

Written first: [Verified] credit goes to the subject before any criticism
begins (CHARTER.md s 1).

- **[Verified]** G2. E8 is realised via the McKay correspondence on the binary
  icosahedral group 2I. Source: arXiv:2604.00255v1. Evidence: standing
  mathematical result (McKay 1980), re-derivable from the correspondence
  between finite subgroups of SU(2) and the ADE diagrams. [Verified] as
  mathematics; **not original to the subject**, and recorded as correctly
  applied rather than newly proved.

- **[Verified]** G3. The trefoil knot links to the Brieskorn E8 singularity.
  Source: arXiv:2604.00255v1. Evidence: standing result in singularity theory.
  Same restriction as G2: correctly applied, not newly proved.

- **[Verified]** G1. Exact 62/62 vertex correspondence between the Mereon M120p
  (H3) and the 600-cell (H4). Source: arXiv:2604.00255v1. Evidence: geometric
  derivation given in the source, resting on the standing H3 subset H4
  embedding. **Limit of this label, stated:** the lab has not independently
  re-derived the 62/62 count at audit date, so this is [Verified] on the
  published derivation and not on an independent check. It becomes independent
  when a reader reproduces the vertex count, which is short arithmetic once
  M120p is fixed.

---

## 5. [Empirical fit] inventory

**Empty.** No claim in the located source fits data through a post-hoc
parameter: the programme states no numerical fit. Recorded as a fact about the
programme's scope, not as a gap.

---

## 6. [Open conjecture] inventory

**Empty.** No claim in the located source is advanced as a conjecture with a
stated falsification path.

---

## 7. [Risk] / [High-risk] inventory

**Empty**, and the reason is the substantive finding of this case.

G4-G6 (SM fermion masses, numerical formulas with error bounds,
machine-checkable proofs) are recorded in Section 2 as **not present in the
paper**. A claim that is not made carries no label: the look-elsewhere exposure
of FRAMEWORK.md (b) attaches to claims, not to silence.

**Venue, FRAMEWORK.md (d):** an arXiv preprint. No venue weakness is recorded
against G1-G3, which rest on standing mathematics.

This is why the case carries no [Risk] row while the lab's own comparable
programme does (Section 9). Section 3's inventory table should be read in that
light: the columns where Gray et al. show "None" are the columns that generate
the lab's own [Risk] entries.

---

## 8. [Retracted] inventory

**Empty.** No claim in the located source has been withdrawn by the authors or
by a publisher at audit date.

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

## 10. Audit summary

**(a) Strongest part.** Three [Verified] geometric and algebraic results
(G1-G3), of which two are standing mathematics correctly applied and one is a
vertex-count derivation given in the source.

**(b) Weakest claim.** None carries a [Risk] label. The weakest point is
evidential rather than substantive: G1 is [Verified] on the published
derivation, not on an independent re-derivation by this lab.

**(c) Experiment that would settle the largest open question.** Reproduce the
62/62 vertex count independently from a fixed definition of M120p. This is
arithmetic, not an experiment, and it would move G1 from published-derivation
[Verified] to independently-checked [Verified].

**(d) Symmetric position of the lab's own work.** The lab holds the same class
of [Verified] result (the closed ladder rule, the Lucas identity) and, unlike
this subject, also extends into SM parameter values -- which is exactly where
its own [Risk] rows come from. On this case the lab's programme is the more
exposed of the two.

---

## 11. Audit trail

- 2026-06-16 -- Wave Loop 9 competitive analysis
- 2026-06-16 -- Added to claim-audit-lab register
- 2026-08-10 -- Section 9 symmetric mirror added; non-ASCII transliterated

---

*phi^2 + 1/phi^2 = 3 | Honest audit, no adjectives*
