# CASE-00: Maintainers' self-audit -- IGLA, GoldenFloat, phi-paper

**Subject:** Dmitrii Vasilev (maintainer of this lab) and the gHashTag
research programme: trios-trainer-igla, goldenfloat-preprint, phi-paper.
**Affiliation:** Independent.
**Programmes:**
- `gHashTag/trios-trainer-igla` -- the IGLA mixed-precision training pipeline.
- `gHashTag/goldenfloat-preprint` -- the GoldenFloat (GF) numeric-format family.
- `gHashTag/phi-paper` -- the Pellis-Vasilev-Olsen short paper on phi-structured
  physical constants.
**Audit date:** 2026-06-02
**Maintainer:** @gHashTag
**Status:** draft, opens the register
**Last update:** 2026-06-02

> **Why this case is first.** Per CHARTER.md s 5 and s 9, the lab audits its
> own work under the same framework it applies to external cases. This file
> is the global self-audit and is referenced by the "Symmetric mirror"
> section of every external CASE.

---

## 1. Identity

The lab maintainers operate three coupled programmes:

- **IGLA** -- a mixed-precision deep-learning training pipeline that uses a
  ladder of float-like number formats (the GF ladder) and a `phi`-anchored
  set of hyperparameters as an *architecture prior*.
- **GoldenFloat (GF)** -- a parameterised family of float-like numeric
  formats from GF4 to GF256, derived from one closed rule
  `e = round((N-1)/phi^2)`, with an integer-backed Lucas accumulator.
- **phi-paper** -- a short manuscript (Pellis-Vasilev-Olsen, version 1.x) on
  phi-structured physical constants, currently being prepared for journal
  submission (Foundations of Physics queue).

Primary references (all URLs fetched on 2026-06-02):

- https://github.com/gHashTag/trios-trainer-igla -- IGLA training pipeline.
- https://github.com/gHashTag/goldenfloat-preprint -- GoldenFloat preprint
  source.
- Zenodo DOI [10.5281/zenodo.19227877](https://doi.org/10.5281/zenodo.19227877)
  -- hardware archive (RTL + testbench artefacts only, NOT a results
  citation).

---

## 2. Programme claims (verbatim)

The lab's central claims, in its own words from the public skill files of
the same author:

> "The GoldenFloat ladder's defensible advantage is **breadth and toolchain
> coherence** -- one self-similar law spanning the whole width ladder --
> **NOT** that any individual rung is more accurate than an equally-tuned
> non-phi format, and **NOT** that phi is a unique or special base."
> -- `goldenfloat-ladder` skill (the One Sentence That Governs Everything),
> https://github.com/gHashTag/trios-trainer-igla (skill mirror)

> "the method survives, phi does not (yet)."
> -- `igla-phi-architecture` skill, same source

> "phi^2 + phi^-2 = 3 (this is the Lucas number L_2, 1878, a Binet-formula
> corollary -- NOT original to Vasilev)."
> -- `igla-phi-architecture` skill

> "IGLA RACE v2 BPB-per-format comparison is [CLAIM, NEEDS REPRODUCTION] as
> of 2026-06-02. The previously circulated figures (gf16 BPB 2.5725 vs bf16
> 2.6135 vs fp16 2.5501) cannot be reproduced from gHashTag/trios-trainer-
> igla master at HEAD fab7d81."
> -- `goldenfloat-ladder` skill, 2026-06-02 update

---

## 3. Tier mapping

The lab uses the five-label framework natively (see FRAMEWORK.md). No
external mapping is needed.

---

## 4. [Verified] inventory

The following claims survive [Verified] under the framework:

- **[Verified]** The closed rule `e = round((N-1)/phi^2)` reproduces the
  realised exponent widths for all nine points on the ladder GF4, GF8, GF12,
  GF16, GF20, GF24, GF32, GF64, GF256 -- 9/9. Source: `goldenfloat-ladder`
  skill `references/gf-format-index.md`. Evidence: deterministic arithmetic,
  re-derivable in one line per point.

- **[Verified]** The Lucas identity `phi^{2n} + phi^{-2n} = L_{2n}` holds for
  all integers n, with `L_{2n}` an integer Lucas number. Source: Ahlbach,
  Usatine, Pippenger, "Efficient Algorithms for Zeckendorf Arithmetic"
  (2012), https://arxiv.org/abs/1207.4497. Evidence: algebraic identity from
  the Binet formula; verified to 50 digits with mpmath for n=1..16 in the
  `phi-paper` numerical audit.

- **[Verified]** The GF16 FPGA testbench passes 35/35 at 323 MHz on Artix-7.
  Source: Zenodo archive
  [10.5281/zenodo.19227877](https://doi.org/10.5281/zenodo.19227877).
  Evidence: reproducible bitstream and waveform traces in the archive. This
  is [Verified] for the GF16 implementation only; the rest of the ladder has
  RTL but no FPGA measurement.

- **[Verified]** The Verilog RTL exists for GF4..GF256 modules, with cocotb
  testbenches. Source: `gHashTag/tt-trinity-corona` HEAD `db1248f5`,
  https://github.com/gHashTag/tt-trinity-corona. Evidence: 50 PASS cocotb
  tests, 2308 synthesised cells, ROM with 80 format records. This is
  [Verified] for "RTL written and simulating", NOT "silicon-validated".

### 4a. Results that survived the 2026-08-10 retraction pass

Section 8a withdraws every phi claim about silicon. The results below are what
remained, and they are [Verified] precisely because **none of them was ever a
hardware claim** -- they are algebra and derived law, re-derivable from
definitions. Source: the lab's hardware research record (`fpga-income` skill;
`trinity-fpga/research/`, `trinity-fpga/conformance/`).

- **[Verified]** `phi` is the unique positive root of `r^2 = r + 1`, and
  `Z[phi] = {a + b*phi}` is a ring closed under the operations of a linear
  tract. Consequence: with inputs in `Z[phi]`, every weight application and
  every accumulation, at any fan-in and any depth, stays in `Z[phi]` and incurs
  **no rounding error at all**; component width grows logarithmically (8 bits
  at 512 terms). Evidence: algebraic, machine-checked, and confirmed at fan-in
  512 against an exact-arithmetic reference. This is [Verified] for the
  arithmetic in the lattice **only** -- it covers linear algebra, and does not
  cover control, branching or addressing, which are not problems in a ring.

- **[Verified]** The minimality of the base. A cheap Fibonacci-style recurrence
  requires `r^2 = p*r + q` with integer `p, q` (so that `Z[r]` is a ring); any
  `p > 1` adds a shift to the addition, and `p = q = 1` gives `phi`. Evidence:
  one-line derivation. [Verified] as a statement about which bases admit the
  recurrence, not as a claim that phi wins in silicon -- Section 8a records
  that it does not.

- **[Verified]** **Accuracy law.** Within a binade, round-to-nearest absolute
  error is uniform, so relative error is `|U|/s` with `|U|` uniform on `[0,u]`,
  `u = 2^-(M+1)`, and significand `s` in `[1,2)`. Hence
  `E[|rel err|] = (1/2) * E[1/s] * 2^-(M+1)` and **the exponent cancels**:
  magnitude-independence is a property of the layout, not a lucky measurement.
  Evidence: derived, then measured across eight rungs (mean 0.3756, spread
  0.369-0.390, prediction inside the interval). The constant is **not**
  universal -- it is `ln 2 = 0.3466` for a uniform significand, `0.3607` under
  Benford -- and quoting a single constant would be an error.

- **[Verified]** **Diagnostic theorem.** Define
  `M_eff(B) = -log2( 2*E[|rel err| | B] / E[1/s] ) - 1`. Then `M_eff` is
  constant across magnitude bands iff the format holds a constant significand
  width and has not exhausted its range; where it tapers, `dM_eff/d|e|` **is**
  the taper rate. Evidence: recovers the declared mantissa to within 0.01 bit
  from round-trip error alone, across three orders of width (GF16 -> 8.97 of 9;
  GF128 -> 78.03 of 78; GF1024 -> 631.99 of 632). This is [Verified] as an
  instrument, and it applies to any format with a conformance oracle, including
  ones the lab did not implement.

- **[Verified]** **Exact taper laws, read from the encoders rather than fitted
  to their output.** posit: `k = floor(|e| / 2^es) + 1`, an arithmetic ladder;
  the 2022 standard fixes `es = 2`, which is why the rate looked like a family
  constant. takum: `r = floor(log2(|e| + 1))`, a geometric ladder. Evidence:
  confirmed at 16, 32 and 64 bits. **This retracts the lab's own earlier
  "takum tapers at 0.117 bits/binade"** -- a straight line fitted to a
  logarithmic ladder over a chosen window, which is a category error, not a
  measurement error. Rule recorded: where the encoder is available, read it
  rather than fitting its output.

- **[Verified]** **Kraft bound on tapering (T12).** For any prefix code on the
  integers, `l(e) >= log2|e|` infinitely often. Therefore **no format with
  unbounded range tapers more gently than one bit per doubling**, and takum's
  regime is asymptotically optimal. Consequence the lab records against its own
  interest: nothing, including its own ladder, beats takum on unbounded range;
  the ladder instead *refuses* unbounded range, and the measured advantages
  hold only inside its own range. Quoting them more widely would be false.

- **[Verified]** **Regime radix is irrelevant (T13).** A regime of one digit per
  multiplication of `|e|` by `r`, over an alphabet of `r` symbols, costs
  `log2(r) * log_r|e| = log2|e|` bits independent of `r`. **This refuted the
  lab's own proposal** of a "one trit per tripling" regime as a third taper
  class: normalised by Kraft, the two code lengths differ by exactly 1 at every
  `|e|` from 1 to 4096. A ternary fabric changes the cost of *decoding* the
  regime, not of encoding it.

- **[Verified]** **Area law.** `A(M) = 141 + 2.4455*M^2` across 14 mantissa
  widths from M=7 to M=90 on one harness, `R^2 = 0.99963`, maximum deviation
  9.9% over a seventy-fold spread in area -- structure (fixed overhead plus a
  quadratic multiplier), not a fitted curve. Corollary `lambda(M) = 4.891*M`
  LUT per bit of mantissa. **A power-law fit `c*M^a` was tried first and is
  withdrawn**: it predicted TEF64 at 4762 LUT against 7479 measured (-36.3%),
  where the two-term model lands within 4.4%. Recorded because the failed
  prediction was registered before synthesis, not after.

- **[Verified]** A prediction from the trade curve, confirmed by synthesis
  rather than by arithmetic: the minimum for a binary32 target was predicted at
  d=2, k=15 -> 43 RAMB36 blocks + 11269 LUT; synthesis of that variant gave
  **42 blocks + 10745 LUT** (2.3% and 4.7% off). This is the lab's strongest
  [Verified] entry of the 2026-08 pass because the number was fixed in advance.

---

## 5. [Empirical fit] inventory

- **[Empirical fit]** The IGLA RACE v2 ablation at hidden=64, 300 steps,
  shows the phi-canonical hyperparameter arm matching or slightly beating
  the non-phi standard arm. Source: `igla-phi-architecture` skill, Phase B1
  proxy results. Free parameters: full optimizer/scheduler set (>10). Pre-
  registered held-out test: PENDING (Phase B1-real at champion scale not yet
  run). This is the strongest empirical leg of the phi-as-architecture-prior
  hypothesis and it is honestly labelled [Empirical fit], not [Verified].

---

## 6. [Open conjecture] inventory

- **[Open conjecture]** Breadth-as-moat: the GF ladder is *better* (per-rung
  accuracy, dynamic range, or toolchain coherence) than an equally-tuned
  posit / takum / MX ladder at matched bit budgets. Source: `goldenfloat-
  ladder` skill, FL-002 ledger row. **Fpath (stated):** the conjecture is
  falsified if a posit/takum/MX ladder matches the phi-ladder at matched
  bit budgets in the F2/F3 protocol, OR if one prior width-spanning float
  family is shown to derive its E:M split from a single closed rule across
  a 2-256-bit ladder with comparable integer-backed coherence (takum is the
  closest live candidate). Executable: F2 issue #1021 (compute-pending);
  F3 control ladder pre-spec'd in `t27c/specs/numeric/posit_ladder_control.t27`.

- **[Open conjecture]** Phi as architecture prior: the set of phi-anchored
  hyperparameters (`beta_1 = phi^-1`, `weight_decay = phi^-3`,
  `grad_clip = phi^-1`, `QK-Gain = phi^2`, Fibonacci warmup) outperforms a
  matched-cardinality control set chosen without phi. **Fpath (stated):**
  the conjecture is falsified if a phi-free control set of equal cardinality
  reaches comparable BPB and convergence in Phase B1-real at champion scale.
  Executable: Phase B1-real, blocked on compute.

---

## 7. [Risk] / [High-risk] inventory

- **[Risk]** The IGLA RACE v2 BPB-per-format table (gf16 BPB 2.5725 vs bf16
  2.6135 vs fp16 2.5501; gf8 2.9322 ties posit8) was previously circulated
  as evidence of phi-ladder competitiveness. Source: prior internal
  artefacts. **Demoted to [CLAIM, NEEDS REPRODUCTION] on 2026-06-02**
  because `git log -S "2.5725"` in `gHashTag/trios-trainer-igla` master at
  HEAD `fab7d81` returns 0 commits, and the table is not present in
  `gHashTag/tt-trinity-corona` either. Until a per-format BPB table is
  regenerated from a frozen, hash-pinned RACE run on the real NTP trainer
  (Phase B1-real, F2 issue #1021), the table is not to be cited in any
  artefact. Recorded in the promotion ledger.

- **[Risk]** "phi-free grammars of equal cardinality reach comparable
  compression" is the lab's own internal control-grammar result, which means
  "phi is special for the constants" is **[Retracted]/[High-risk]**, not
  established. Source: `igla-phi-architecture` skill.

---

## 8. [Retracted] inventory

- **[Retracted]** delta_CP = 3/phi^2 as a phi-structured value of the
  CP-violating phase in neutrino oscillation. Withdrawn after independent
  arithmetic check showed the algebraic identity does not deliver the
  claimed numerical match at the precision required. Source: `pellis-
  vasilev-letter` skill: "delta_CP = 3/phi^2 (it is [Retracted])". Never to
  be cited as evidence.

### 8a. Silicon claims withdrawn 2026-08-10 (seven in one pass)

Source: the lab's own hardware research record (`fpga-income` skill;
`trinity-fpga/research/`). Every phi claim about silicon was re-examined
against a competitor's best construction rather than its convenient one.
**None survived.** They are recorded individually so that none is
re-advertised, and because the pattern across them is itself a result.

| # | Withdrawn claim | How it fell |
|---|-----------------|-------------|
| R1 | `phi^k` is the correct scale grid for multiplier-free scaling | Wrong basis. APoT-2 (Additive Powers-of-Two, ICLR 2020) gives 0.1651% excess error against our 2.4420%, in one cycle against our `k`. The narrow claim (phi beats `2^k`) stands; the important one does not |
| R2 | `dot_exact` confers an accuracy advantage | The APoT scale `2^p +/- 2^q` is dyadic, and `Z[1/2]` is also a ring closed under the tract's operations. Exactness of the linear tract was **always** available to binary fixed point. The theorem is true; the significance attached to it was not |
| R3 | phi wins area by 2.22x | Measured at a 5-bit shift field. The real span across 210 layers is 3.15 octaves, so 2 bits suffice: APoT 130 LUT against our 199 |
| R4 | phi wins at frozen scale | A frozen shift is wiring, not logic. APoT 26 LUT against 64/128/256 at K=2/4/8 |
| R5 | Depth-independence is an advantage | Compile-time composition is free to every representation. Three of the four cases we claimed (low-rank `W=UV`, folded conv+BN, residual scalar) are known after training |
| R6 | LNS addition costs 10967 LUT | That figure was a **format decoder**, not an adder. An honest LNS-32 adder is 275 LUT. Our own number was wrong by two orders of magnitude, in our favour |
| R7 | The mesh case is where phi finally wins | Comparable at last: APoT requantisation 103 LUT against a Fibonacci step at 128. A 25% loss, not a win |

- **[Retracted]** "28 catalogued competitors, zero survivors" as the headline
  dominance result. The covering condition counted **positions**; a format is
  stored in **bits**, and a realisable member must satisfy
  `3^Et * 2^M <= 2^(N-1)`. Substituting the minimal `Et` gives
  `m + log2(b+1) <= N-1`, which is identically the uniform binary budget --
  the claimed 0.3691*E gap vanishes exactly, at every E. Re-measured at equal
  storage: **6 of 17 dominated, not 28 of 28**, and the dominated ones are the
  formats that waste bits (posit32, posit64, takum32, cray_float, and our own
  gf8 at 0.70).

- **[Retracted]** "323 MHz / 41.2 GOPS" for the GF16 matmul. `grep -c posedge`
  returns 0 in all nine copies of `gf16_matmul4x4` / `gf16_dot4`: the block has
  no registers, so no clock frequency can belong to it, and the GOPS figure was
  derived as 323 MHz x 128 ops. Both withdrawn together. The honest replacement
  is what was actually measured: 32252 LUT / 0 DSP48 (or 21223 LUT / 64 DSP48),
  combinational; and a pipelined variant at 36.36 MHz with latency 3.

- **[Retracted]** "TEF is the best of the fixed-field formats." Re-measured
  through an identical path, it sits mid-group (0.147-0.183 MHz/LUT); the
  1.7x spread inside the group is set by field width, not by family. What
  survived is the group separation itself -- fixed fields beat tapered by
  2.4-6.4x on a ternary network -- which does not depend on whose format
  places first.

### 8b. What the retractions have in common

Seven reversals in one pass share one mechanism, and the lab records it as
its most transferable finding:

> **The conditions of a comparison are part of its result.** Each favourable
> number came from a comparison whose conditions we chose: powers of two
> instead of APoT; a 5-bit field where the workload needs 2; the runtime mode
> instead of the frozen one. The measurements were not wrong. The comparisons
> were.

Three operating rules were bought with these errors, and they are the lab's
own restatement of what FRAMEWORK.md demands of external programmes:

1. **Before reporting a ratio, write down what the competitor would have built
   if they were trying to win, and measure that** -- not the version that is
   convenient to beat.
2. **A comparison whose control is broken is not a comparison.** Check the
   control before reading the order of the arms. (Caught when post-hoc
   ternarisation put *every* arm, including the exact-scale control, at
   perplexity ~2.2e7 against a 14.49 baseline -- which read as "phi refuted
   twofold" and meant nothing.)
3. **Check your own defeat the same way you check your own victory.** R7 was
   first obtained through a non-comparable comparison pointing *against* us
   (173 against 103, where our side carried a counter and a state machine and
   theirs did not). Same defect as the six wins, aimed the other way.

A fourth rule concerns the ledger itself, and is why 8a is a table rather than
a sentence: **a correction that invalidates a comparison applies to every claim
standing on the same quantity, not only to the one where it surfaced.** The
packing-limit defect was recorded twice as a local fact before it was carried
to the headline result it most affected.

---

## 9. Symmetric mirror

CASE-00 is the symmetric mirror that every external CASE points at. The
table below names, for each label, the lab's representative claim of that
class. External cases reference these rows.

| Label | Representative claim | Class |
|-------|----------------------|-------|
| [Verified] | `e = round((N-1)/phi^2)` reproduces GF ladder 9/9 | algebraic identity |
| [Verified] | GF16 FPGA 35/35 at 323 MHz | reproducible measurement |
| [Verified] | `Z[phi]` closed; linear tract exact at any depth (s 4a) | machine-checked algebra |
| [Verified] | accuracy law, exponent cancels (s 4a) | derived, then measured |
| [Verified] | diagnostic theorem `M_eff` recovers declared mantissa to 0.01 bit (s 4a) | instrument, applies to other formats |
| [Verified] | Kraft bound: nothing beats takum on unbounded range (s 4a) | derived, against own interest |
| [Verified] | trade-curve prediction confirmed by synthesis, 2.3% / 4.7% (s 4a) | pre-registered before measurement |
| [Empirical fit] | IGLA hidden=64 phi-arm vs non-phi-arm | matched control, n-pending |
| [Open conjecture] | breadth-as-moat with stated Fpath (F2/F3) | falsifier executable, compute-pending |
| [Open conjecture] | phi as architecture prior with stated Fpath (B1-real) | falsifier executable, compute-pending |
| [Risk] | GF16 BPB-per-format table | source un-reproducible at HEAD |
| [Retracted] | delta_CP = 3/phi^2 | withdrawn |
| [Retracted] | seven phi-silicon claims R1-R7 (s 8a) | withdrawn in one pass, 2026-08-10 |
| [Retracted] | "28 competitors, zero survivors" (s 8a) | positions-vs-bits artefact |
| [Retracted] | 323 MHz / 41.2 GOPS for GF16 matmul (s 8a) | block has no registers |
| [Retracted] | takum taper rate 0.117 bits/binade (s 4a) | category error: line fitted to a ladder |
| [Retracted] | power-law area model (s 4a) | failed a pre-registered prediction by 36.3% |

---

## 10. Audit summary

Strongest part: the ladder arithmetic and the integer Lucas accumulator are
[Verified]. The GF16 FPGA result is the only matched-precision [Verified]
hardware measurement in the programme.

Weakest claim: the BPB-per-format table that previously circulated as
evidence of phi-ladder competitiveness, now demoted to [CLAIM, NEEDS
REPRODUCTION] because it cannot be regenerated from public source HEAD.

Single experiment that would move the largest open claim: Phase B1-real at
champion scale (full four-arm matched-cardinality ablation with frozen seed
and pre-registered held-out split), blocked on compute. This is the
experiment that would either promote breadth-as-moat to [Empirical fit]
with strong control, or demote it to [Risk].

The lab's own work is therefore mostly [Empirical fit] / [Open conjecture]
with a set of [Verified] anchors and a substantial [Retracted] inventory.
External CASEs that find similar status in other phi-programmes are recording
a real symmetry, not a bias.

**Update 2026-08-10.** The [Retracted] inventory is no longer one entry. A
single re-examination pass withdrew seven claims about phi in silicon plus
three headline results (s 8a), and two further methodological claims were
withdrawn in s 4a. What survived is the mathematics -- which was never a
hardware claim -- and one prediction that was fixed before it was measured.

This changes the calibration the register applies to itself in two ways, both
recorded against the lab's own interest. First, the lab's own strongest phi
claims have now failed at a higher rate than any external programme in this
register has been shown to fail, because no external programme has been
re-examined this hard. A [Risk] label on an external case reflects evidence
not yet supplied; the lab's [Retracted] rows reflect evidence supplied and
found wanting. **These are not the same, and the more damaging one is ours.**
Second, the mechanism behind all seven -- that the conditions of a comparison
are part of its result (s 8b) -- is a general instrument, and the register has
not yet applied it to any external case. Doing so is the obvious next audit,
and it may well move external labels in the subjects' favour, since several
were assigned on comparisons the lab constructed.

---

## 11. Sources

- 2026-06-02: https://github.com/gHashTag/trios-trainer-igla -- IGLA repo HEAD.
- 2026-06-02: https://github.com/gHashTag/goldenfloat-preprint -- GoldenFloat
  preprint HEAD.
- 2026-06-02: https://github.com/gHashTag/tt-trinity-corona -- Corona ROM,
  HEAD `db1248f5`.
- 2026-06-02: https://doi.org/10.5281/zenodo.19227877 -- hardware archive
  DOI.
- 2026-06-02: https://arxiv.org/abs/1207.4497 -- Ahlbach/Usatine/Pippenger
  2012, Zeckendorf arithmetic.

---

## 12. Subject's reply

The subject is the maintainer of this lab. Reply unnecessary.

---

**End of CASE-00.**
