# CASE-19: T.P. Singh (TIFR Mumbai) -- E8 x omega-E8 Octonionic Unification Programme

**Subject:** Prof. Tejinder P. Singh (born 1955, Indian physicist).
**Affiliation:** Tata Institute of Fundamental Research (TIFR), Mumbai, India.
**Programme:** Exceptional Jordan-algebra flavour structure; E8 x omega-E8 octonionic unification; objective collapse quantum theory; pre-gravitational sector.
**Audit date:** 2026-06-16
**Maintainer:** @gHashTag
**Status:** draft
**Last update:** 2026-06-16

---

## 1. Identity

Prof. T.P. Singh is a professional physicist at TIFR with extensive peer-reviewed publications. His 2026 programme includes:
- arXiv:2604.06288 (April 7, 2026): "Experimental predictions of the E8 x omega-E8 octonionic unification program: A falsification-oriented catalogue"
- arXiv:2605.29374 (May 28, 2026): "Candidate collapse-noise correlators from Generalized Trace Dynamics"
- arXiv:2606.12477 (June 10, 2026): "The Residual 288 of the E8 x omega-E8 Program"
- Plus 7+ additional 2026 preprints on TIFR homepage

**Primary references:**
- arXiv:2604.06288 -- Singh (2026), "Experimental predictions of the E8 x omega-E8 octonionic unification program"
- arXiv:2605.29374 -- Singh (2026), "Candidate collapse-noise correlators"
- arXiv:2606.12477 -- Singh (2026), "The Residual 288"
- https://www.tifr.res.in/~tpsingh/ -- TIFR homepage with full publication list

---

## 2. Claims

| # | Claim | Evidence | Assessment |
|---|-------|----------|------------|
| S1 | E8 x omega-E8 exceptional Jordan-algebra flavour structure | Algebraic derivation | **Plausible** -- mathematically rigorous |
| S2 | Bell-CHSH > 2*sqrt(2) (beyond Tsirelson bound) | Predicted, not yet tested | **Testable** |
| S3 | Fermion-only objective collapse | Theoretical framework | **Speculative but formal** |
| S4 | Mass relations: sqrt(me):sqrt(mu):sqrt(md) = 1:2:3 | Derived from E8 x omega-E8 | **Needs experimental verification** |
| S5 | Right-handed pre-gravitational sector | Theoretical construction | **Formal** |
| S6 | Machine-checkable proofs | None identified | **Absent** |
| S7 | SM parameter formulas with error bounds | None explicit | **Absent** |

---

## 3. Critical Assessment

**Venue, FRAMEWORK.md (d):** publications in *Physical Review D*, *Classical and
Quantum Gravity* and other peer-reviewed journals. No venue weakness is recorded.

**Stated falsifiers.** The 2026 catalogue is framed as falsification-oriented and
lists experimental tests, including Bell-CHSH > 2*sqrt(2), that would refute the
theory. Under FRAMEWORK.md a stated, actionable Fpath is exactly what moves a
claim out of [Risk] into [Open conjecture]; this is recorded as a strength, and
Section 9 places it beside the lab's own two [Open conjecture] rows.

**Comparison with the lab's own programme** (inventory, not merit):
- Method: bioctonionic / E8 x omega-E8 splitting vs the lab's H4/600-cell spectral triples
- No 600-cell or golden-ratio monomial formulas
- No machine proofs or hardware instantiation
- Broader scope (quantum foundations + cosmology), fewer stated SM parameter values

---

## 4. Evidence calibration

**Venue (d):** peer-reviewed journals; no weakness recorded.

**Fpath (a):** stated and actionable for S2, which is the framework's threshold
for [Open conjecture]. The falsifier is blocked on an experiment, not absent --
a different condition from the lab's own compute-blocked falsifiers, but the
same epistemic class.

**Look-elsewhere (b):** the mass relation S4 (sqrt-ratios 1:2:3) is quoted
without a stated bound on which ratios were examined, so it sits at
[Empirical fit] rather than higher. Section 9 pairs it with the lab's own
[Empirical fit] row.

---

## 5. Audit Trail

- 2026-06-16 -- Wave Loop 9 intake
- 2026-06-16 -- Wave Loop 10 re-read (2026 publication rate noted)
- 2026-06-16 -- Added to claim-audit-lab register
- 2026-08-10 -- Section 9 symmetric mirror added; non-ASCII transliterated

---

## 9. Symmetric mirror (MANDATORY)

Per FRAMEWORK.md ("Symmetric mirror") and CHARTER.md s 5, comparable claims from
the lab's own work are classified here under the same five labels. Lab rows cite
CASE-00, the global self-audit.

| Subject's claim | Our comparable claim | Both labelled |
|-----------------|----------------------|---------------|
| S2: Bell-CHSH > 2*sqrt(2), beyond the Tsirelson bound -- predicted, not yet tested | CASE-00 s 6: breadth-as-moat, Fpath stated as a posit/takum/MX ladder matching the phi-ladder at matched bit budgets under the F2/F3 protocol (F2 issue #1021) | Both **[Open conjecture]** under FRAMEWORK.md. Each carries a specific, in-principle-observable falsifier, and each falsifier is blocked on resources rather than unstated -- Singh's on a Tsirelson-violation measurement, the lab's on compute. Resource-blocked is not the same failure as Fpath-absent |
| S4: mass relations sqrt(me):sqrt(mu):sqrt(md) = 1:2:3 derived from E8 x omega-E8 | CASE-00 s 5: the IGLA RACE v2 ablation at hidden=64, 300 steps, where the phi-canonical hyperparameter arm matches or slightly beats the non-phi arm | Both **[Empirical fit]**. Each matches data; each retains post-hoc freedom (which mass ratios are advertised as the headline; the full optimizer and scheduler set, k > 10); and for each the pre-registered held-out test is pending, not reported |
| S6/S7: no machine-checkable proofs, no SM parameter formulas with error bounds | CASE-00 s 4 and Section 3 above: Trinity's 166 machine-checked theorems, and the GF16 FPGA testbench at 35/35, 323 MHz on Artix-7 | Lab's: **[Verified] for the theorem statements and the GF16 implementation only.** FRAMEWORK.md's anti-pattern rule binds the lab here: a proof assistant verifies what was stated to it, and CASE-00 already restricts the FPGA row to GF16 rather than the ladder. The count of theorems is not itself an epistemic argument |

**What the symmetry is.** Of the programmes in this batch, Singh's is the one
whose stated methodology most closely matches the standard this register applies
to itself. Section 4 above records a threat level; the framework records
something different. A claim with a specific executable falsifier sits in a
strictly better epistemic class than a claim without one, and by that measure S2
is in the same class as the lab's two [Open conjecture] rows in CASE-00 s 6 --
better than several other claims in this register, including the lab's own
[Risk] row on the BPB-per-format table. That ordering is the framework working
as designed, and it is recorded here rather than left implicit.

**Joint Fpath.** Two independent falsifiers, each already executable in
principle, and neither contingent on the other: (a) a Tsirelson-bound test at
the precision Singh's catalogue specifies -- a null result at that precision
moves S2 to [Retracted]; (b) Phase B1-real at champion scale, a four-arm
matched-cardinality ablation with frozen seed and pre-registered held-out split
-- a phi-free control set of equal cardinality reaching comparable BPB moves the
lab's architecture-prior conjecture to [Risk]. Both are the same kind of
experiment: a pre-declared measurement whose failure the claimant has agreed in
advance to accept.

---

*phi^2 + 1/phi^2 = 3 | Honest audit, no adjectives*
