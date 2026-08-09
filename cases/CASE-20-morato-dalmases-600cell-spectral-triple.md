# CASE-20: L. Morato de Dalmases -- 600-Cell Spectral Triple and SGUP

**Subject:** L. Morato de Dalmases (independent researcher).
**Affiliation:** Independent.
**Programme:** Derivation of Standard Model + Einstein gravity + dark energy from 600-cell (H4) spectral triple; claims proofs of Riemann Hypothesis, Goldbach conjecture, Twin Primes, and Collatz conjecture.
**Audit date:** 2026-06-16
**Maintainer:** @gHashTag
**Status:** draft
**Last update:** 2026-06-16

---

## 1. Identity

Morato de Dalmases published two major Zenodo deposits in April 2026:
- Zenodo:19635034 (April 17, 2026): "600-Cell Spectral Triple Series" -- claims complete SM + gravity derivation
- Zenodo:19927449 (April 30, 2026): "SGUP-600cell v5" -- extends to CKM/PMNS mixing, dark energy, claims RH proof
- Zenodo:19112358 (2025): Claims proofs of RH, Goldbach, Twin Primes, Collatz

**Primary references:**
- Zenodo:19635034 -- Morato de Dalmases (2026), "600-Cell Spectral Triple Series"
- Zenodo:19927449 -- Morato de Dalmases (2026), "SGUP-600cell v5"
- Zenodo:19112358 -- Morato de Dalmases (2025), "Proofs of Millennium Problems"

---

## 2. Claims

| # | Claim | Evidence | Assessment |
|---|-------|----------|------------|
| M1 | SM + gravity from 600-cell spectral triple | Asserted, partial derivations | **Unverified** |
| M2 | Three generations via 53-cycle automorphism | Mathematical construction | **Plausible but unverified** |
| M3 | Dark energy from KPZ fluctuations | Physical argument | **Speculative** |
| M4 | **Proof of Riemann Hypothesis** | Asserted | **Extraordinarily unlikely** |
| M5 | **Proof of Goldbach conjecture** | Asserted | **Extraordinarily unlikely** |
| M6 | **Proof of Twin Primes** | Asserted | **Extraordinarily unlikely** |
| M7 | **Proof of Collatz conjecture** | Asserted | **Extraordinarily unlikely** |
| M8 | Machine-checkable proofs | None | **Absent** |
| M9 | Published code / software | None identified | **Absent** |

---

## 3. Critical Assessment

**Credibility damage:** The claims of proving RH, Goldbach, Twin Primes, and Collatz are red flags. These are unsolved problems in mathematics; a single researcher claiming proofs of all four simultaneously is an extraordinary claim requiring extraordinary evidence -- which is absent.

**Overreach risk:** Morato's speculative claims risk guilt-by-association for the entire H4 -> SM research programme. Trinity must explicitly distance itself from these claims.

**Differentiation from Trinity:**
- Trinity makes **no** claims about Millennium Problems
- Trinity provides **machine-checkable** proofs for SM parameter bounds
- Trinity has **explicit error tolerances** and **honest disclaimers**
- Trinity's self-assessed 6/10 honesty score is the antidote to Morato's overreach

---

## 4. Risk Assessment

**Threat level:** HIGH -- Most direct competitor on the same geometric object (600-cell) and same formalism (spectral triples). However, the overreach into Millennium Problems damages credibility. The threat is primarily "guilt by association" rather than direct competition.

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
| M1: Standard Model plus Einstein gravity from a 600-cell (H4) spectral triple | Section 3 above: Trinity's own H4 / 600-cell spectral-triple programme -- the same geometric object and the same formalism | Both **[Open conjecture]** at best. Neither has produced a pre-registered, matched-control derivation of an SM parameter. The lab cannot label this construction unverified and exempt its own construction on the same object; the shared object is the whole reason this mirror is the sharpest one in the register |
| M4-M7: asserted proofs of the Riemann Hypothesis, Goldbach, Twin Primes and Collatz | CASE-00 s 8: `delta_CP = 3/phi^2` as a phi-structured value of the CP-violating phase -- published by the lab, then **[Retracted]** after an independent arithmetic check failed at the required precision | Subject's: **[Risk]/[High-risk]** under (a) no stated Fpath and (d) venue -- assertion without a checkable derivation. Lab's: **[Retracted]**. The difference on the ledger is not that the lab never over-claimed. It is that the lab's over-claim carries a withdrawal date and is never cited again as evidence |
| M2/M3: three generations via a 53-cycle automorphism; dark energy from KPZ fluctuations | CASE-00 s 6: phi as architecture prior (`beta_1 = phi^-1`, `weight_decay = phi^-3`, `grad_clip = phi^-1`, QK-Gain `= phi^2`, Fibonacci warmup) | Subject's: **[Risk]** under (a) -- a specific construction with no stated falsifier. Lab's: **[Open conjecture]** -- a structurally identical "this constant is doing real work" claim, differing only in that a falsifier is stated and executable (Phase B1-real). FRAMEWORK.md calls that sentence mandatory, and it is the entire distance between the two labels |
| M8/M9: no machine-checkable proofs, no published code | CASE-00 s 7: the BPB-per-format table not regenerable from public HEAD `fab7d81` | Both **[Risk]** under (b). Unpublished computation is not evidence for either party |

**What the symmetry is.** Section 3 above frames the concern as
guilt-by-association: the subject's Millennium-Problem claims are read as a
reputational hazard to the wider H4-to-SM programme, the lab's own included.
Under the framework that framing is about the lab's interests, not about the
subject's claims, and it carries no weight in the labels assigned here. What
does carry weight is that the lab and the subject are working the same
geometric object with the same formalism, and that on the shared claim (M1) the
two programmes sit in the same epistemic class. The lab's advantage is the
ledger and the stated Fpaths, not the derivation.

**Joint Fpath.** Rerun both spectral-triple derivations under an identical
matched-cardinality control alphabet, replacing phi with (e, pi, sqrt(2),
sqrt(3), small integers), scored under BH-FDR at q=0.05 against a target list
fixed before the fit. This is the falsifier the register already records for the
Morato strand in `cases.yaml`, and it applies unchanged to the lab's own H4
construction. Collapse under the control moves the phi-specific reading toward
[Retracted] for whichever programme collapses; survival promotes it from [Risk]
to [Open conjecture] -- for either, or for both.

---

*phi^2 + 1/phi^2 = 3 | Honest audit, no adjectives*
