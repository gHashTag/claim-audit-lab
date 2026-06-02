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

---

## 9. Symmetric mirror

CASE-00 is the symmetric mirror that every external CASE points at. The
table below names, for each label, the lab's representative claim of that
class. External cases reference these rows.

| Label | Representative claim | Class |
|-------|----------------------|-------|
| [Verified] | `e = round((N-1)/phi^2)` reproduces GF ladder 9/9 | algebraic identity |
| [Verified] | GF16 FPGA 35/35 at 323 MHz | reproducible measurement |
| [Empirical fit] | IGLA hidden=64 phi-arm vs non-phi-arm | matched control, n-pending |
| [Open conjecture] | breadth-as-moat with stated Fpath (F2/F3) | falsifier executable, compute-pending |
| [Open conjecture] | phi as architecture prior with stated Fpath (B1-real) | falsifier executable, compute-pending |
| [Risk] | GF16 BPB-per-format table | source un-reproducible at HEAD |
| [Retracted] | delta_CP = 3/phi^2 | withdrawn |

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
with a few [Verified] anchors and one honest [Retracted]. External CASEs
that find similar status in other phi-programmes are recording a real
symmetry, not a bias.

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
