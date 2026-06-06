# CASE-07 — Carroll / Kaplan style M_pl coincidence claims

**Target programme**: published proposals that exact small-integer / golden-ratio relations connect the Planck mass M_pl to particle-physics scales (e.g. M_pl / m_e, M_pl · alpha factors, golden-power towers).
**Claim status**: **\Risk**
**Selection rationale**: This is a phi-adjacent class of claims that the v2.1 phi-paper deliberately does NOT make (mu = m_p/m_e was removed per 2026-06-06 Pellis review). Auditing the adjacent claim class is a calibration exercise — if these proposals fail under matched-cardinality controls, our own decision to drop M_pl-related rows is empirically supported.

## Specific claims surveyed

The Carroll/Kaplan-class claim family includes proposals of the form:

1. **M_pl / m_e ≈ phi^N · pi^M · e^K** for small integers (N, M, K).
2. **M_pl coincidences with golden powers** of standard-model coupling ratios.
3. **"Trans-Planckian gap closes" under specific phi-arithmetic identities.**

Representative published examples (catalogued in `phi_theorists_catalog.md`):
- Various preprints proposing M_pl / m_e ≈ small-prefactor · phi^k forms.
- Hierarchy-problem reformulations invoking exact golden-ratio splits.

## Why \Risk (not \Retr or \Verified)

The claims are not categorically refuted in the literature — but they have not been tested against matched-cardinality control alphabets. Without such a test, "find one good fit" carries no statistical weight, by the same look-elsewhere argument we apply to our own G_phi grammar in §6 of the v2.1 phi-paper.

## Falsification path (\Fpath)

A clean falsification path requires three steps, none yet executed in the published M_pl literature:

1. **Pre-register** the target list (which M_pl-derived dimensionless ratios are in scope, with values fixed before fitting).
2. **Specify a control alphabet** matched in cardinality to the proponents' generator alphabet (e.g. if the proposal allows {phi, pi, e, small integers}, the control draws random transcendentals from a matched-cardinality set).
3. **Apply BH-FDR at q = 0.05** across the full pre-registered target list, treating each "successful fit" as a hypothesis test.

If, after these three steps, the M_pl-class fits survive at q < 0.05, the claim class moves to **\Efit**. If not, it moves to **\Retr** for the specific proposal tested (general class remains \Risk pending further tests).

## Audit script

Concrete check applied to our own M_pl candidate (now-excluded from v2.1):
- `mu = m_p / m_e ≈ 1836.15` — earlier draft tested form `2 · pi^5 · phi^{-4}` at 50-digit precision.
- Result: rel. dev. ≈ 2.1e-3, which is WORSE than the BH-FDR threshold one obtains from the catalog-15 selection step.
- **Decision (Pellis 2026-06-06)**: row excluded from v2.1 methods table; reserved for a future physics-oriented manuscript where the look-elsewhere multiplier can be properly bounded.

## What this CASE adds to claim-audit-lab

This is the first CASE that audits a class of claims the principal authors **declined to make in their own manuscript**. The decision-to-exclude is itself an audit datum — it demonstrates that the methodology produces null results even when they would have been favourable to the authors' broader programme.

## Status row for cases.yaml

```yaml
- id: CASE-07
  title: "Carroll/Kaplan M_pl coincidence class"
  target: "M_pl / m_e and M_pl · coupling-ratio phi-arithmetic claims (general class)"
  claim_status: Risk
  fpath: "Pre-registered target list + matched-cardinality control alphabet + BH-FDR at q=0.05"
  file: cases/CASE-07-carroll-kaplan-m-planck.md
```

## Anchor

φ² + φ⁻² = 3
