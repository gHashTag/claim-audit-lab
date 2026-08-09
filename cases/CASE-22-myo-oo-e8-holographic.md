# CASE-22: Myo Oo (+ Mark W. Vick) -- E8 Holographic Geometry / Project MAYA

**Subject:** Myo Oo (affiliation unknown), with Mark W. Vick.
**Affiliation:** Independent / Zenodo / Academia.edu.
**Programme:** "Project MAYA" -- derivation of 11+ physical constants from E8 holographic geometry; single scale Lambda = 51.9 GeV; claims 100% validation across 24 tests.
**Audit date:** 2026-06-16
**Maintainer:** @gHashTag
**Status:** draft
**Last update:** 2026-06-16

---

## 1. Identity

Myo Oo publishes on Zenodo and Academia.edu under the "Project MAYA" framework. Claims include:
- Single scale Lambda = 51.9 GeV
- Derivation of alpha, Higgs mass, Planck mass, strong coupling, lepton masses from E8
- "Shadow sector" (112 vector vs 128 spinor roots) for dark matter
- Links Riemann zeta zeros to lepton masses

**Primary references:**
- https://www.academia.edu/164593041 -- Myo Oo (2026), "The Complete Standard Model and Quantum Gravity from E8 Holographic Geometry"
- Multiple Zenodo deposits (2025-2026)

---

## 2. Claims

| # | Claim | Evidence | Assessment |
|---|-------|----------|------------|
| O1 | 11+ constants from E8 holographic geometry | Asserted | **Unverified** |
| O2 | Single scale Lambda = 51.9 GeV | Asserted | **Speculative** |
| O3 | "100% validation across 24 tests" | Self-assessed | **Not independently verified** |
| O4 | Dark matter from E8 "shadow sector" | Theoretical construction | **Speculative** |
| O5 | Riemann zeta zeros -> lepton masses | Correlation claimed | **Numerological** |
| O6 | Machine-checkable proofs | None | **Absent** |
| O7 | Published software | None identified | **Absent** |

---

## 3. Critical Assessment

**Volume vs. rigour:** Myo Oo has high publication volume across Zenodo and Academia.edu, but lacks peer review, machine proofs, or transparent error budgets. The "100% validation" claim is self-assessed and not independently verified.

**Differentiation from Trinity:**
- Trinity: 166 Coq theorems, explicit tolerances, open-source code
- Myo Oo: Self-published PDFs, no verification infrastructure

---

## 4. Risk Assessment

**Threat level:** MEDIUM-HIGH -- Rapidly expanding "Project MAYA" framework with many self-published papers. Could attract attention through volume alone. However, lack of formal proofs and peer review limits academic credibility.

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
| O3: "100% validation across 24 tests", self-assessed | CASE-00 s 7: the IGLA RACE v2 BPB-per-format table (gf16 2.5725 vs bf16 2.6135 vs fp16 2.5501), circulated by the lab as evidence of phi-ladder competitiveness and demoted to [CLAIM, NEEDS REPRODUCTION] on 2026-06-02 | Both **[Risk]** under (b)/(d): a self-generated validation figure no third party can regenerate from public artefacts. FRAMEWORK.md (b) grants [Verified] only to a harness with a frozen seed, a frozen config, a sha256 of outputs and a public script that exits non-zero on any deviation. Neither figure has one. The lab's demotion came from `git log -S "2.5725"` returning 0 commits at public HEAD `fab7d81` |
| O5: Riemann zeta zeros mapped to lepton masses | CASE-10: the PHI_BIAS coincidence-class survey, which found near-coincidences for all five new GF rungs across six coincidence classes (Fibonacci, Lucas, squares, cubes, powers of 2, triangular) | Subject's: **[Risk]** under (b) -- no bounded search space, so the density of available near-matches is unreported. Lab's: the same scan was run against the lab's own targets and returned **OPEN**, with no value assigned, because no class was uniquely closer than the alternatives. Identical situation, opposite decision -- and the framework requires the lab's decision of both parties |
| O1/O2: 11+ constants and a single scale Lambda = 51.9 GeV from E8 holographic geometry | CASE-00 s 6: phi as architecture prior, Fpath stated as a phi-free control set of equal cardinality reaching comparable BPB and convergence in Phase B1-real | Subject's: **[Risk]** under (a), no Fpath stated. Lab's: **[Open conjecture]**, the same class of claim with a stated, executable falsifier. The gap between the two labels is one sentence of the right kind, and FRAMEWORK.md calls that sentence mandatory |
| O4: dark matter from an E8 "shadow sector" (112 vector vs 128 spinor roots) | CASE-00 s 6: breadth-as-moat -- the GF ladder as better than an equally-tuned posit/takum/MX ladder at matched bit budgets | Subject's: **[Risk]** under (a) and (c). Lab's: **[Open conjecture]**, with a named live control (takum) that the lab pre-specified rather than waited to be shown. Naming your closest competitor before the comparison is what separates the labels here |

**What the symmetry is.** Section 3 above contrasts the subject's publication
volume with Trinity's verification infrastructure. The framework does not weigh
either quantity. It asks one question of both parties -- can a third party
regenerate this number from public artefacts -- and on the headline validation
figure the answer was no for the subject and, on 2026-06-02, no for the lab as
well. The lab's response to its own no is recorded in CASE-00 s 7 and in
PROMOTION-LEDGER.md. That response, not the volume comparison, is the actual
difference between the two programmes.

**Joint Fpath.** For both parties, the same instrument settles it: publish the
validation harness with a frozen seed, a frozen config, a sha256 of outputs and
a public script that exits non-zero on any deviation, and pre-register the
target list before the run. An independent re-run that reproduces the outputs
promotes each claim to [Verified] **for the harness output only**, never for the
geometric or metaphysical reading it was built to support. A re-run that does
not reproduce them moves the claim to [Retracted]. The lab's instance of this is
Phase B1-real, blocked on compute; the subject's is unblocked and has not been
run.

---

*phi^2 + 1/phi^2 = 3 | Honest audit, no adjectives*
