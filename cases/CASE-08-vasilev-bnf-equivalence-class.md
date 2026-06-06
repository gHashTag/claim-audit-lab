# CASE-08 — Vasilev BNF equivalence-class result (symmetric self-audit)

**Target programme**: the v2.3-draft addition to the Vasilev-Pellis-Olsen short paper (`gHashTag/phi-paper`), specifically the new §6.3 claim that `G_phi = phi^2 + phi^-2` is MDL-rank 2 of 394 essential phi-native forms (bootstrap p = 0.0039) within a bounded BNF grammar with anti-cancellation filter.
**Claim status**: **\Conj** (conditional on grammar + MDL proxy)
**Selection rationale**: Per CHARTER.md §5 and CASE-00, the lab audits its own work under the same framework it applies to external cases. This CASE applies the lab's framework symmetrically to a claim the maintainers **want to be true** about their own programme. If the audit fails, the v2.3 result is downgraded; if it survives, the lab gains a worked example of a phi-adjacent claim that passes the matched-cardinality + bootstrap discipline.

## Specific claim surveyed

From `gHashTag/phi-paper` v2.3-draft, §6.3 "Equivalence-class analysis and MDL-canonical Lucas form (v2.3)":

> "Within depth-≤2 BNF over `{phi^k : k in [-2,2]}` with binary operators `{+,-,*,/}` and the anti-cancellation filter, `G_phi = phi^2 + phi^-2` is the MDL-canonical Lucas-symmetric representative `L_2 = phi^n + (-phi)^-n` at n = 2, with p < 0.01 significance."

Source state:

- Manuscript: `gHashTag/phi-paper` v2.3-draft, **LOCAL ONLY**, pending Stergios Pellis approval (HARD GATING rule). master HEAD remains `cb94106` (v2.2-capsule).
- Frozen audit trail: `reproducibility/v23/` in local clone (NOT pushed):
  - `v23C_full_enumerate.py` (SHA-256 `e0f792f3def5f7ae...`) — 40,100-expression BNF enumerator.
  - `results_v23C_full.json` (SHA-256 `f3dd8e5a29a5a9e3...`) — 501 matches, by classification.
  - `v23C_anticancel_bootstrap.py` (SHA-256 `8f2cdcf3357e87b7...`) — W1+W8 filter + bootstrap driver.
  - `results_v23C_anticancel.json` (SHA-256 `c82075742bae5581...`) — 394 essential, rank = 2.
  - `results_v23C_bootstrap.json` (SHA-256 `75cbf04361bdf0ba...`) — p = 0.0039, B = 10,000.

## Why \Conj (not \Verified or \Risk)

The result is reproducible at the byte level (every figure is read from SHA-pinned JSON; no human-typed numbers in the LaTeX). But three structural caveats prevent a `\Verified` label:

1. **Grammar is bounded.** Depth ≤ 2 over `{phi^k : k in [-2,2]}` is a tiny corner of the symbolic-expression space. A grammar extension (integer coefficients, depth > 2, radicals, transcendental atoms) might surface a strictly shorter phi-native form reducing to 3. The v2.3 manuscript codifies this caveat as **Conj 7.6** (Grammar-extension robustness).
2. **MDL is a string-length proxy.** Not a Rissanen-Grünwald two-part code with explicit grammar prior. Replacing the proxy by a real MDL could shift G_phi rank above 10. Codified as **Conj 7.7** (Rissanen-Grünwald MDL robustness).
3. **Equivalence-class detection uses sympy.simplify.** EGG-SR (Jiang 2026 ICLR, arXiv:2511.05849) provides a formal e-graph for equivalence-class detection that may produce a different class cardinality. Risk R-v23-C-1 acknowledges this in §6.4.

Pending all three resolutions, the strongest honest label is **\Conj at p < 0.01 within the explicitly specified scope**.

## Falsification path (\Fpath)

Three independent paths, each codified in the v2.3 manuscript:

1. **\Fpath (structural)** — a depth-≤2 BNF expression that reduces to 3 via `sympy.simplify`, has MDL < 12, and survives the anti-cancellation filter. Such an expression would lower the rank of G_phi.
2. **\Fpath (coding-scheme)** — a Rissanen-Grünwald two-part code with explicit grammar prior under which G_phi ranks above 10 within the same 394-form essential class.
3. **\Fpath (grammar-extension)** — an extended grammar (integer coefficients, depth > 2, radicals, or transcendental atoms) that produces a form with strictly smaller MDL than G_phi reducing to 3.

Any one of these falsifies the v2.3 §6.3 conclusion. None has been executed.

## Symmetric mirror

Per CASE-00, the lab applies the same framework to its own work. The v2.3 claim above is:

- **Stricter** than the claims audited in CASE-01..CASE-06 (Savchenko, Stakhov, El Naschie, Petoukhov, Kramer-Klimesch, de Groot) — those rely on post-hoc fits to data; the v2.3 claim is an exhaustive enumeration with frozen capsule.
- **Comparable** to CASE-07 (Carroll/Kaplan M_pl) in scope: a phi-anchored coincidence claim about a single algebraic identity. CASE-07 is `\Risk` because its proponents have not run a matched-cardinality control. CASE-08 is `\Conj` because the matched control (the 394-form equivalence class) **has** been run, but the grammar and MDL proxy remain narrow.
- **Weaker** than the central v2.1 phi-paper result (the 37/40 control-grammar result on the Catalog15 aggregate), which is `\Verified` (negative): "no grammar in the test compresses the constants". That result is invariance-grade. The v2.3 §6.3 claim is a sharper, narrower question with conditional `\Conj`.

If CASE-08 were applied symmetrically to e.g. CASE-02 (Stakhov), the equivalent step would be: enumerate every depth-≤2 expression in Stakhov's harmony-mathematics generator alphabet, apply anti-cancellation filter, run bootstrap. The fact that this has not been done in the Stakhov literature is precisely why CASE-02 sits at `\Efit`, not `\Verified`.

## Why this CASE matters for the lab

This is the **first** CASE that audits a phi-anchored claim by the maintainers that may **pass** the lab's framework. CASE-00 (self-audit) handles the global identity; CASE-08 takes one specific concrete claim from the maintainers' own draft manuscript and runs it through the same matched-cardinality + bootstrap discipline applied to external programmes.

Two epistemic functions:

1. **Methodology calibration** — if the lab's framework is too strict to credit even a frozen, byte-reproducible matched-cardinality result, the framework is broken. If the lab's framework credits this claim too easily, the framework is broken in the other direction. CASE-08 is the calibration test.
2. **Public symmetric audit-trail** — the v2.3 manuscript will cite this CASE as a peer-reviewable (in the public-audit sense) record of the equivalence-class result, with the same SHA-256 pin discipline applied to external CASEs.

## Three external validators (next-loop)

To raise CASE-08 from `\Conj` toward `\Verified`, three independent validators have been identified (see `gHashTag/trinity-s3ai/WAVE23_PHI_PAPER_v23_STATUS.md` for full plan):

1. **Aaron Finkelstein** (BNF SR author, arXiv:2410.08137) — closes the "is the methodology sound?" question. Cost: one short letter.
2. **Peter Grünwald** (CWI, ERC AdvGrant 2024 safe testing) — closes Conj 7.7 (real MDL). Cost: one short letter.
3. **ReScience C journal** — peer-reviewed replication with frozen capsule. Cost: GitHub PR submission, 3-6 month review window.

Any one of these closing positively would shift the symmetric mirror in CASE-08 from "we have run the matched control" to "an independent external audit has confirmed our matched control".

## Status row for cases.yaml

```yaml
- id: CASE-08
  title: "Vasilev BNF equivalence-class result (symmetric self-audit, v2.3 phi-paper)"
  target: "v2.3 §6.3 claim: G_phi MDL-rank 2/394 at p=0.0039 within depth-≤2 BNF + anti-cancellation filter"
  claim_status: Conj
  fpath: "Any of three: (a) shorter depth-≤2 phi-native form reducing to 3 surviving the filter; (b) Rissanen-Grünwald MDL shifting rank > 10; (c) EGG-SR canonicalisation producing different equivalence-class cardinality and rank"
  file: cases/CASE-08-vasilev-bnf-equivalence-class.md
```

## Cross-references

- v2.3 manuscript: `gHashTag/phi-paper/pellis_vasilev_letter.tex` §6.3, §6.4, Conj 7.6, Conj 7.7 (LOCAL ONLY pending Pellis approval).
- v2.3 reproducibility capsule: `gHashTag/phi-paper/reproducibility/v23/` (LOCAL ONLY).
- Cross-repo pointer: `gHashTag/trinity-s3ai/WAVE23_PHI_PAPER_v23_STATUS.md` (PUBLIC, on master).
- Letter to Stergios Pellis asking for approval: workspace `outbox/letter_to_stergios_pellis_2026-06-06_v2.md` (4 explicit questions).
- Weak-point inventory: workspace `audit_2026-06-06/weaknesses_inventory_v23_2026-06-06.md` (W1-W10).
- Literature scan: workspace `audit_2026-06-06/literature_scan_v23_2026-06-06.md` (18 publications).

## Anchor

φ² + φ⁻² = 3 = L_2 — algebraically `\Verified`; MDL-canonical in 394-form essential class `\Conj` at p < 0.01 within stated bounds. The bounds are part of the result.
