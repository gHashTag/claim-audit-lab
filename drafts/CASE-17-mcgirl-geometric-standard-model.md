# CASE-17: Timothy McGirl (grapheneaffiliate) -- Geometric Standard Model

**Subject:** Timothy McGirl (independent researcher).
**Affiliation:** Independent; publishes on Zenodo and GitHub as "grapheneaffiliate."
**Programme:** Derivation of 26-58 fundamental constants from E8 -> H4 icosahedral geometry with zero free parameters.
**Audit date:** 2026-06-16
**Maintainer:** @gHashTag
**Status:** draft
**Last update:** 2026-06-16

---

## 1. Identity

McGirl published "Geometric Standard Model (GSM) v26.0" on Zenodo (December 14, 2025). GitHub repositories include:
- `grapheneaffiliate/e8-phi-constants` -- 58 constants from E8 -> H4
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
| Mc1 | 58 constants from E8 -> H4 | Python solver (`gsm_solver.py`) | **Unverified** |
| Mc2 | Zero free parameters | Asserted | **Unverified** |
| Mc3 | Bell bound S = 4 - phi ~= 2.382 | Algebraic proof | **Formal but untested** |
| Mc4 | Lean 4 proofs (6 compiled) | Present | **Partial verification** |
| Mc5 | Brute-force vertex tests (8,100 quadruples) | Performed | **Empirical check** |
| Mc6 | arXiv presence | None found | **Absent** |
| Mc7 | Peer review | None identified | **Absent** |

---

## 3. Critical Assessment

**Venue:** no arXiv record was located under this name at audit date. arXiv
requires endorsement for hep-th. Recorded as a fact about the available
evidence, not about the author.

**Formal verification:** 6 compiled Lean 4 proofs. Under FRAMEWORK.md this is
[Verified] for the statements given to the proof assistant and nothing beyond
them; the same restriction binds the lab's 166 theorems (Section 9).

**Comparison with the lab's own programme** (inventory, not merit):
- McGirl: 58 constants, 6 Lean proofs, Python solver
- Lab (Trinity): 23 constants, 166 Coq proofs, FPGA opcodes, stated tolerances

---

## 4. [Verified] inventory

Written first: [Verified] credit goes to the subject before any criticism
begins (CHARTER.md s 1).

- **[Verified]** Mc3. The Bell bound S = 4 - phi ~= 2.382 follows algebraically.
  Source: Zenodo GSM v26.0. Evidence: algebraic derivation, re-derivable in a
  few lines. [Verified] **for the algebra only**; whether this quantity is a
  physically realised bound is a separate claim carrying a separate label, and
  the subject has not supplied a measurement.

- **[Verified]** Mc4. Six Lean 4 proofs compile. Source:
  `grapheneaffiliate/e8-phi-constants`. Evidence: the compiled proofs.
  [Verified] **for the six statements given to the proof assistant and nothing
  beyond them** -- FRAMEWORK.md's anti-pattern rule. The identical restriction
  binds the lab's own 166 theorems (Section 9).

- **[Verified]** Mc5. A brute-force check over 8,100 vertex quadruples was
  performed. Source: `grapheneaffiliate/Geometric-Standard-Model`. Evidence:
  the enumeration. [Verified] **for the enumeration output only**: an
  exhaustive check of a finite set establishes what it enumerated, not that the
  enumerated set was the right one to search.

---

## 5. [Empirical fit] inventory

**Empty.** The 58-constant result is not presented with a stated fit
procedure, free-parameter count or control, so it does not meet the
[Empirical fit] definition and is recorded at [Risk] in Section 7 instead.

---

## 6. [Open conjecture] inventory

**Empty.** No falsification path is stated for Mc1 or Mc2 in the located
sources. Under FRAMEWORK.md (a) a claim that aspires to be a conjecture but
states no falsifier defaults to [Risk], not [Open conjecture].

---

## 7. [Risk] / [High-risk] inventory

- **[Risk]** Mc1. 58 constants derived from E8 -> H4 geometry. Source: Zenodo
  GSM v26.0, `gsm_solver.py`. Reason: FRAMEWORK.md (b) -- the space of
  expressions the generating alphabet can produce is not bounded, so no
  look-elsewhere correction is reportable. At an unbounded alphabet a larger
  constant count is a larger exposure, not a stronger result.

- **[Risk]** Mc2. Zero free parameters. Source: as above. Reason:
  FRAMEWORK.md (b) and the [Empirical fit] definition -- "zero free parameters"
  counts fitted coefficients and not the choice of alphabet, and an alphabet
  selected after the target values are known is itself a post-hoc parameter.
  **The lab's own 23-constant claim carries this identically** (Section 9).

- **[Risk]** Mc6, Mc7 as they bear on Mc1/Mc2. Reason: FRAMEWORK.md (d) --
  a single Zenodo deposit (Dec 2025), no peer review and no arXiv record
  located at audit date. This calibrates available evidence, not the author,
  and the lab's own phi-paper is likewise not yet accepted.

---

## 8. [Retracted] inventory

**Empty.** No claim has been withdrawn by the subject at audit date.

---

## 9. Symmetric mirror (MANDATORY)

Per FRAMEWORK.md ("Symmetric mirror") and CHARTER.md s 5, comparable claims from
the lab's own work are classified here under the same five labels. Lab rows cite
CASE-00, the global self-audit.

| Subject's claim | Our comparable claim | Both labelled |
|-----------------|----------------------|---------------|
| Mc4: 6 compiled Lean 4 proofs | CASE-00 s 4 and Section 3 above: Trinity's 166 machine-checked theorems, and the GF16 FPGA testbench at 35/35, 323 MHz on Artix-7 | Both **[Verified] for what was actually checked and nothing beyond it.** This is FRAMEWORK.md's anti-pattern rule applied to the lab: a proof assistant verifies the statement it was given, and CASE-00 already restricts the FPGA row to the GF16 implementation rather than the ladder. 6 proofs and 166 theorems differ in count, not in epistemic kind |
| Mc2: 58 constants at "zero free parameters" | Section 3 above: Trinity's 23 constants at "0 free inputs (phi, pi, e only)" | Both **[Risk]** under (b). Neither party has bounded the space of expressions its alphabet can generate, so neither can report a look-elsewhere correction. At matched, unbounded alphabets a larger constant count is a larger [Risk], not a stronger result -- which cuts against reading "23 vs 58" in Section 3 as an argument in either direction |
| Mc5: brute-force vertex tests over 8,100 quadruples | CASE-09: the Corona ROM CATALOG-vs-rule check, and CASE-10's six-class coincidence scan over the GF ladder | Both **[Verified] for the enumeration output only.** An exhaustive check of a finite set establishes what it enumerated. It does not establish that the enumerated set was the right one to search, and in CASE-10 the lab's own exhaustive scan is precisely what forced an OPEN verdict rather than a value |
| Mc3: Bell bound S = 4 - phi ~= 2.382, algebraic | CASE-00 s 4: `phi^2 + phi^-2 = 3`, the Lucas number L_2 and a Binet-formula corollary | Both **[Verified]** under (a), as algebra, for the algebra only. Whether either quantity is a physically realised bound is a separate claim carrying a separate label, and neither programme has moved it |
| Mc6/Mc7: no arXiv presence, no peer review | CASE-00 s 1: phi-paper in the Foundations of Physics queue, not yet accepted; the lab's hardware DOI is an artefact archive, explicitly **not** a results citation | Both **[Risk]** under (d). Venue weakness is a calibration of available evidence, not a judgment of the author, and on this axis the two programmes are currently in the same position |

**What the symmetry is.** This is the closest methodological match in the batch:
both programmes derive constants from E8 -> H4 geometry, both claim zero free
parameters, and both submit part of the work to a proof assistant. Every
verification asset the lab holds, the subject holds a smaller version of, and
every unbounded-search-space problem the subject has, the lab has at 23 constants
instead of 58. Section 4 records the absence of an arXiv record; under the
framework that is a venue fact under (d), which the lab shares, and not a fact
about the claims.

**Joint Fpath.** Pre-register the constant list, the generating alphabet and the
tolerance for each constant **before** running the solver, then apply one
matched-cardinality control alphabet (e, pi, sqrt(2), sqrt(3), small integers at
equal expression cardinality) to both constant sets under BH-FDR at q=0.05. A
set whose phi-native forms do not outrank the control moves to [Risk] regardless
of how many constants it contains or how many proofs accompany it. A set that
survives with its alphabet declared in advance reaches [Empirical fit] with a
matched control, and only a held-out confirmation at the pre-registered
tolerance would reach [Verified]. The same run scores both programmes.

---

## 10. Audit summary

**(a) Strongest part.** Three [Verified] entries (Mc3-Mc5), each restricted to
what was actually checked: the algebra, the six Lean statements, the
enumeration output.

**(b) Weakest claim.** Mc2, zero free parameters over 58 constants -- [Risk]
under (b), with no bound on the generating alphabet.

**(c) Experiment that would settle it.** Pre-register the constant list, the
generating alphabet and the per-constant tolerance before running the solver,
then score against a matched-cardinality control alphabet under BH-FDR q=0.05.

**(d) Symmetric position of the lab's own work.** Identical on both counts: the
lab's 166 theorems carry the same [Verified]-for-the-statement-only
restriction, and its 23 constants at "0 free inputs" carry the same unbounded
alphabet. This is the closest methodological match in the register.

---

## 11. Audit trail

- 2026-06-16 -- Wave Loop 9 competitive analysis
- 2026-06-16 -- Added to claim-audit-lab register
- 2026-08-10 -- Section 9 symmetric mirror added; non-ASCII transliterated

---

*phi^2 + 1/phi^2 = 3 | Honest audit, no adjectives*
