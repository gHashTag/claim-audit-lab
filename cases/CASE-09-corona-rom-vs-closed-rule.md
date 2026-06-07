# CASE-09 — Corona ROM CATALOG vs closed-form ladder rule (symmetric self-audit)

**Target programme**: the `gHashTag/tt-trinity-corona` ROM CATALOG (`tools/gen_rom.py`) — specifically the question of whether the eight previously-tabulated GF rungs (GF16, GF24, GF32, GF48, GF64, GF96, GF128, GF256) agree with the closed-form rule `e = round((N-1)/phi^2)` declared in `gHashTag/t27` `FORMAT-SPEC-001.json` v1.2.
**Claim status**: **\Conj** (the closed rule reproduces 9 of 9 returned-silicon / RTL rungs, and is the SSOT-declared normative split; it is the rule under audit, not yet `\Verified` under matched-cardinality control)
**Selection rationale**: Per CHARTER.md §5 and CASE-00, the lab audits its own artefacts under the same framework it applies to external cases. Until Corona PR #3, the ROM CATALOG declared eight rung splits that **disagreed** with the rule that the t27 SSOT and the frozen silicon (gamma `gf16_v2_mul.v` = `1+6+9`, bias 31) both encode. This CASE records that internal inconsistency, the fix applied, and the residual conjectural status of the closed rule itself.

## Specific claim surveyed

From `gHashTag/t27` `conformance/FORMAT-SPEC-001.json` v1.2 (PR #1051):

> "For each total width `N >= 4`, the GoldenFloat split is `e = round((N-1) / phi^2)`, `m = N - 1 - e`, `bias = 2^(e-1) - 1`, with `phi = (1+sqrt(5))/2`."

And from `gHashTag/tt-trinity-corona/tools/gen_rom.py` v1.1 (PR #3): the ROM CATALOG must agree with this rule on every rung it tabulates.

Source state:

- t27 SSOT: `conformance/FORMAT-SPEC-001.json` v1.2 + `specs/numeric/goldenfloat_family.t27` (17 rungs).
- Corona ROM source: `tools/gen_rom.py` CATALOG list, RECORD_COUNT = 80, post-fix.
- Frozen silicon ground truth: `gHashTag/tt-trinity-gamma/src/gf16_v2_mul.v` (`[5:0]` exp, `[8:0]` mant, `BIAS_S = 31`).
- Cross-reference doc: `gHashTag/tt-trinity-corona/docs/goldenfloat_ladder_crossreference.md` v1.1.

## Pre-fix internal inconsistency (now closed)

Before Corona PR #3, the CATALOG declared the following eight rungs whose splits did **not** match the closed rule the same repo's docs and the t27 SSOT both encode:

| N    | CATALOG (pre-fix) | Closed-rule (NORMATIVE)   |
|------|-------------------|---------------------------|
| 16   | 1+5+10            | 1+6+9       (silicon ground truth) |
| 24   | 1+8+15            | 1+9+14                    |
| 32   | 1+11+20           | 1+12+19                   |
| 48   | 1+17+30           | 1+18+29                   |
| 64   | 1+23+40           | 1+24+39                   |
| 96   | 1+35+60           | 1+36+59                   |
| 128  | 1+48+79           | 1+49+78                   |
| 256  | 1+96+159          | 1+97+158                  |

All eight contradicted the rule. The fix in Corona PR #3 brings the CATALOG onto the rule; the regenerated `src/rtl/format_rom.v` changes 16 ROM bytes at addresses `7'd15..7'd30`. Tests pass (`test/test_ssot_layout_crosscheck.py` + post-silicon vectors).

## Why \Conj (not \Verified or \Risk)

The rule reproduces all 9 returned-silicon / finalised-RTL rungs of the GoldenFloat ladder (GF4, GF8, GF12, GF16, GF20, GF24, GF32, GF64, GF256) under the closed form `e = round((N-1)/phi^2)`. The Corona CATALOG now agrees on all eight previously-broken rungs. But three structural caveats prevent a `\Verified` label on the rule itself:

1. **Look-elsewhere control is open.** The preprint Section "Look-Elsewhere Correction" reports that 83 of 80,000 rationals in `[0.1, 0.9]` reproduce the same 9 widths. Bonferroni saturates at 1; the family-wise probability of >= 83 matches is `approx 7.1e-3` — moderate, not striking. The rule is one matching ratio among many, not a unique fit. Recomputing the search with the full 17-rung ladder (or with a tighter pre-registered ratio space) is **open** and is the gating step before promoting `\Conj -> \Verified`.
2. **Six rule-derived rungs have no silicon.** GF6, GF10, GF14, GF48, GF96, GF128 are admitted by the rule and the t27 SSOT but have not been returned in silicon and (with the exception of GF128) have no taped-out RTL. Promotion of those rungs is gated on silicon return.
3. **Two rungs (GF512, GF1024) overflow the Corona ROM record.** `FIELD_TOTAL_BITS / EXP_BITS / MANT_BITS` are `u8` in the 80-bit ROM record; GF512 mantissa = 316 and GF1024 exponent = 391 / mantissa = 632 do not fit. RECORD_COUNT stays at 80; GF512/GF1024 are tracked only at the t27 SSOT and in the Corona `corona_oracle.t27` `GF_LADDER_EXTENDED` struct. This is a deliberate architectural deviation from a naive "RECORD_COUNT 80 -> 82" extension: physical field width forbids it.

Pending all three, the strongest honest label on the closed rule (and on the Corona CATALOG-vs-rule agreement) is **\Conj**.

## Falsification path (\Fpath)

Three independent paths:

1. **\Fpath (structural)** — a returned silicon die under any name encoding a GoldenFloat-labelled width with `(e, m)` split disagreeing with `e = round((N-1)/phi^2)`. Such a die would refute the rule's normative status. As of this CASE the only returned silicon at GoldenFloat-labelled widths is the gamma GF16 codec on Artix-7, which agrees with the rule.
2. **\Fpath (statistical)** — a 17-format pre-registered ratio sweep that narrows the candidate set to a singleton (the rule alone) **or** that fails to narrow appreciably; either outcome closes Conj 7.6-equivalent for the ladder rule. The sweep has not been re-run at 17 widths; the preprint and the ARITH 2027 scaffold both carry an explicit NOTE not to cite a 17-format figure until this case closes.

   **CLOSURE NOTE (Fpath b) -- Track A, look-elsewhere @ 17 widths.**
   Completed by `tools/lookelsewhere_17.py`; output captured in `cases/CASE-09-lookelsewhere-17.txt`.

   Criterion sourced from `gf_preprint_v19.tex` sec:lookelsewhere and app:lookelsewhere:
   - Search space: grid of N_s = 80,000 ratios r in [0.1, 0.9] at step 1e-5.
   - Match condition: `round_half_even((N-1)*r) == e_target` for all widths simultaneously.
   - Rounding: round-half-to-even (IEEE 754 default).
   - 12-format set (from preprint v18 Table tab:ladder, verified v19): N in {4,8,12,16,20,24,32,64,256,128,512,1024}.
   - 17-format set: full v1.3 canonical ladder, all 17 rungs.

   **Results:**
   - count_match_9 (grid, context) = 392; interval [0.37844, 0.38235]. Preprint stated same.
   - count_match_12 (sanity check) = 47; interval [0.38189, 0.38235]. Preprint stated 47. **REPRODUCED.**
   - count_match_17 (primary result) = 47; interval [0.38189, 0.38235]. **No change from 12-format.**
   - p_match_17 = 47/80000 = 5.875e-4.
   - p_17 (Binom(80000, 5.875e-4) tail, normal approx) = 0.529. Bonferroni_17 = 1.
   - count_match_17 / count_match_12 = 47/47 = 1.000.

   **Honest interpretation (verbatim as written into this case):**
   The 17-format sweep is a TRIVIAL NON-RESULT. Adding the 5 remaining rule-derived rungs
   (GF6, GF10, GF14, GF48, GF96) to the 12-format set does not narrow the candidate set:
   count_match_17 = count_match_12 = 47, identical to the 12-format count. The reason
   is structural and predictable: each of the 5 new rungs has a matching interval
   [(e-0.5)/(N-1), (e+0.5)/(N-1)] that strictly contains the existing 12-format
   grid interval [0.38189, 0.38235]. Small-N rungs (GF6, GF10, GF14) have wide
   intervals due to coarse rounding; mid-N rungs (GF48, GF96) also contain the
   12-format interval. Every grid point that passed all 12 prior conditions trivially
   satisfies all 5 new ones. The new widths auto-pass by construction because they are
   generated by the same closed rule; they cannot independently confirm it. This result
   is EXPECTED and does NOT constitute additional evidence for the moat narrative.
   The moat narrative does not gain strength from the 17-width expansion.

   **Additional finding -- p-value ambiguity:** The preprint states p ~ 7.1e-3 for the
   9-format case (K=83, N_s=80,000) but this value cannot be reproduced from the stated
   Binom(N_s, K/N_s) formula -- the normal approximation yields P(X >= 83) ~ 0.52 for
   that parameterisation. The supplementary script `look_elsewhere_calc.py` referenced
   in the preprint is absent from the repository, so the exact computation is not
   auditable. This ambiguity does not affect the count results, which are unambiguous.

   **Fpath(b) status after this closure:** The path is now CLOSED as a non-result.
   The 17-format sweep does not narrow the candidate set to a singleton and does not
   fail to narrow appreciably relative to 12 formats -- it simply preserves the 12-format
   result exactly. The \ Conj label on the ladder rule is unchanged: 47 ratios remain
   in the candidate set, phi^-2 is not uniquely identified by the grid criterion alone,
   and the original p ~ 7.1e-3 assertion carries an unresolved ambiguity in its
   derivation. Promotion from \Conj to \Verified via this statistical path is not
   supported by the 17-width recount.
3. **\Fpath (algebraic)** — a closed expression strictly simpler than `round((N-1)/phi^2)` that reproduces the same 17 splits exactly. Candidates ruled out at 8/9 in the preprint Appendix (e.g. `round((N-1)*3/8)`, `round((N-1)*5/13)`, `floor(N*3/8)`, `round((N-1)/2.6)` all fail GF256). Failure to find such an expression supports the rule's MDL-canonicity within the rational-coefficient class; finding one falsifies it.

Any one of these paths, if executed and resolved, shifts the rung-vs-rule agreement from `\Conj` toward `\Verified` (paths 1, 3) or downgrades it to `\Risk` (negative outcome of path 2).

## Symmetric mirror

Per CASE-00, the lab applies the same framework to its own artefacts. The Corona CATALOG inconsistency is precisely the kind of internal contradiction the lab flags in external programmes (e.g. CASE-02 Stakhov, where harmony-mathematics generator rules and their cited instances do not always self-audit). The fact that the lab found and recorded a contradiction in its own SSOT-vs-ROM consistency before any external review is the symmetric-mirror discipline working as intended.

CASE-08 audits a v2.3 phi-paper claim that the maintainers want to be true. CASE-09 audits a Corona ROM consistency claim that the maintainers wanted to be true and discovered was false at eight rungs. Both `\Conj` (the post-fix state); both with explicit \Fpath; both with frozen reproducibility artefacts (Corona PR #3 commit `71329b5`).

## Reproducibility capsule

Frozen audit trail, all SHA-pinned at the commit-level:

- t27 PR #1051 (commit `15d959b`): FORMAT-SPEC-001.json v1.2, NUMERIC_FORMATS_SSOT.md, goldenfloat_family.t27 17-rung enumeration, formats_catalog.t27 +8 entries, 9 new spec files (gf6/10/14/48/96/128/256/512/1024.t27).
- Corona PR #3 (commit `71329b5`): `tools/gen_rom.py` 8 CATALOG fixes, regenerated `src/rtl/format_rom.v` (16 ROM byte changes at `7'd15..7'd30`), `specs/corona/corona_oracle.t27` `GF_LADDER_EXTENDED`, `docs/goldenfloat_ladder_crossreference.md` v1.1.
- Gamma PR #118 (commit `7eaa819`): `specs/numeric/tri_net_formats.t27` GF128 fix `1+48+79 -> 1+49+78`, GF256 bias correction to `2^96-1`, NEW `GF512Format` / `GF1024Format` spec-only structs.
- Preprint PR #2: `gf_preprint_v19.tex` table extended to 17 rungs (three-block layout: 9 realised / 6 rule-derived / 2 symbolic-bias).
- ARITH 2027 PR #1: scaffold abstract + OUTLINE + README aligned with 17-rung ladder.

Frozen silicon ground truth (not modified by any of these PRs):

- `gHashTag/tt-trinity-gamma/src/gf16_v2_mul.v` — `[5:0]` exp, `[8:0]` mant, `BIAS_S = 31`. Confirms `GF16 = 1+6+9`, `bias = 2^(6-1) - 1 = 31`, which is the closed-rule prediction.

## Status row for cases.yaml

```yaml
- id: CASE-09
  title: "Corona ROM CATALOG vs closed-form ladder rule (symmetric self-audit)"
  target: "tt-trinity-corona tools/gen_rom.py CATALOG agreement with t27 SSOT closed rule e = round((N-1)/phi^2)"
  claim_status: Conj
  fpath: "Any of three: (a) returned silicon at a GoldenFloat-labelled width with (e,m) disagreeing with the rule; (b) 17-format pre-registered ratio sweep that fails to narrow appreciably or that narrows to a singleton; (c) closed expression strictly simpler than round((N-1)/phi^2) reproducing all 17 splits"
  file: cases/CASE-09-corona-rom-vs-closed-rule.md
```

## Cross-references

- t27 SSOT: `gHashTag/t27/conformance/FORMAT-SPEC-001.json` v1.2 (PR #1051).
- Corona fix: `gHashTag/tt-trinity-corona` PR #3, commit `71329b5`.
- Gamma alignment: `gHashTag/tt-trinity-gamma` PR #118, commit `7eaa819`.
- Preprint table: `gHashTag/goldenfloat-preprint` PR #2 (`gf_preprint_v19.tex` Section 2).
- ARITH 2027: `gHashTag/arith2027-goldenfloat` PR #1 (scaffold alignment).
- Frozen silicon: `gHashTag/tt-trinity-gamma/src/gf16_v2_mul.v` (unchanged across these PRs).

## Anchor

`phi^2 + phi^-2 = 3 = L_2` — algebraically `\Verified` (Lucas 1878, Binet). The ladder rule `e = round((N-1)/phi^2)` is `\Conj` within the stated falsification paths. The Corona CATALOG-vs-rule consistency is, post-PR #3, `\Verified` by direct byte-level inspection of the regenerated ROM against the rule.
