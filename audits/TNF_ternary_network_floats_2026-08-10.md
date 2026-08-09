# CASE: Ternary Network Floats (TNF) and the golden weight alphabet — 2026-08-10

**Subject:** `gHashTag/trinity-fpga`, `research/arxiv_tnf/tnf_paper.tex`; supporting
measurements in `research/block/` and `fpga/tnet/`; machine-checked component in
`gHashTag/trinity-s3ai`, `derivations/golden_alphabet/`.

**Author taxonomy:** none stated. Per FRAMEWORK, the strongest published wording is
taken and promotion applied only where this framework's requirements are met.

**Note on symmetry:** the subject here is the lab's own programme. The mirror section
therefore labels external claims by the identical standard, so the asymmetry runs in
neither direction.

---

## Claims and labels

### [Verified]

| claim | why this label |
|---|---|
| `φ·φ = φ + 1`; any `r > 1` with `r·r = r + 1` is `φ` | Machine-checked, `coqorg/coq:8.20.1`. `coqc` exit 0, `coqchk` clean, zero `Admitted`, zero `Axiom`. Negative control run: altering the conclusion to `r = φ + 1` fails compilation with exit 1 |
| On integer pairs `(a,b) ≡ a + bφ`, multiplication by `φ` is `(a,b) → (b, a+b)` | Same file, same kernel check |
| The linear path of a `{-φ,0,+φ}` network is exact — no rounding at any fan-in or depth | `dot_exact`, kernel-checked. This is a statement about arithmetic, not a measurement |
| `φ^(k+1) = F_(k+1)·φ + F_k` | `phi_pow_fib`, kernel-checked by induction |
| Coverage condition: the TNF family dominates a width-`N` format iff `m + ⌈log₃(b+1)⌉ ≤ N−1` | Two lines of algebra over the family definition; independently re-derivable |
| No catalogued uniform binary format escapes, 28 checked at 8/16/32/64/128 bits | Follows from the coverage condition plus the uniform budget `m + log₂(b+1) ≤ N−1`; the enumeration is a check, not the argument |
| BNF16 and TNF16 land within 1% in placed silicon | Post-route on XC7A200T, open flow, prediction computed before synthesis |

### [Empirical fit]

| claim | why this label, and on what data |
|---|---|
| Accumulator error grows as `√(pK)` in fan-in | Fitted exponent `+0.476` and `+0.435` against a predicted `+0.5`, on one model's ternarised weights. One model, one layer type |
| Precision law `½·E[1/s]·2^−(M+1)`, holding to 3% across eight rungs | Derived, then measured; the 3% is a fit residual over a finite sample |
| Area law `A(M) = 141 + 2.4455·M²`, R² = 0.99963 | Regression over `M ∈ [7,90]`; replaced an earlier power law that missed TNF64 by 36% |
| Throughput-per-area ordering among range-carrying formats | One harness, one datapath, one device. Decoders taken from an open verification set, not vendor-optimised |
| Within-block span 1.89 binades median / 3.04 at the 99th percentile | One model. The estimator itself was later found wrong for a different purpose — see [Retracted] |

### [Open conjecture]

| claim | falsification path |
|---|---|
| The pair `{GFTernary, TNF}` is a reference format for a ternary datapath | Exhibit a pair that closes the same two sites at lower area or higher accuracy on the same harness. The claim is bounded to datapaths whose weights are codes |
| The radix argument pays only where a position is physically ternary | Build a binary-fabric format with a ternary exponent that beats its binary sibling on a live workload. Three attempts so far went the other way |
| A format that beats MX/NVFP4 on the block axis exists | Named as the standing condition on publication. Not held; see below |

### [Retracted]

Recorded permanently. None is to be cited again.

| claim | date | what happened |
|---|---|---|
| `tnet` comparison at 440 vs 895 LUTs, 5.1× | 2026-08 | TNF received pre-widened fields while competitors unpacked theirs. Corrected to matched-width on packed words: 3.1× at 16 bits, 5.6× at 32 |
| TNF64 area predicted at 4,762 LUT | 2026-08 | Measured 7,479, a 36% miss. Power law replaced by the quadratic area law |
| TNF128 does not route | 2026-08 | It routes at 4,869 LUT, 56 DSP, 103.39 MHz. The failure was under a self-imposed `-nodsp` constraint |
| int4 beats MXFP4 by 27% | 2026-08-09 | The harness gave E2M1 six magnitudes where the OCP spec gives eight. Corrected: MXFP4 21.94 against int4 30.89 |
| TNF beats MXFP4 on the block axis | 2026-08-10 | Measured against us. MXFP4 21.94 vs TNF4 36.72; MXFP6 14.73 vs TNF6 18.03. `3^Eₜ` never divides `2^k`, so packing loses up to 25% of a 4-bit alphabet |
| Width rule predicts BNF8 `E=4` and TNF8 `Eₜ=3` | 2026-08-10 | Winners were `E=3` and `Eₜ=2`, both one step narrower. The rule's form survives; its range **estimator** was wrong, crediting a 0.1-percentile tail that carries almost no energy |
| Levers are nearly multiplicative | 2026-08 | Ratio computed against a losing baseline. Order-dependence measured at 2.78× |
| arXiv:2606.05017 and 2606.09686 cite GF-T | 2026-08 | They do not. Corrected by the author |

Eight further defects of instrument rather than claim are logged in the subject
repository, including a simulator that returned error identically zero at every
fan-in, and a level-table built from position counts that produced a 100× artefact
against the subject's own format.

---

## Symmetric mirror

External claims labelled by the identical standard.

| external claim | label | reasoning |
|---|---|---|
| MXFP4 (OCP): E2M1 with a shared UE8M0 scale is a suitable 4-bit inference format | **[Verified]** for inference on the measured workload | Reproduced here at perplexity 21.94 against an fp32 baseline of 14.49, with the spec's own scale and level count |
| MXFP4/NVFP4 support training | **[Empirical fit]**, not [Verified] | Every published sub-8-bit training result carries block scales *and* a higher-precision master weight. The element alone carries no range |
| posit: tapered precision is worth its decode cost | **[Empirical fit]** on accuracy, **[Retracted]** would be too strong | Accuracy near unity is real. The decode cost measured here is 2.4–6.4× throughput per area, which the original claim does not deny |
| takum: a logarithmic value law is a good general-purpose choice | **[Open conjecture]** | Falsifier: a datapath that stays in the logarithmic domain never pays the `2^f` table. Measured here at 10,967 LUT and 84 RAMB36 for `takum32_decode`, but that penalises a design that converts, not one that does not |
| Ternary27: a radix-3 scale is preferable | **[Retracted]** by measurement | At equal storage (43 bits) it is dominated with five positions to spare. Radix-3 scaling buys range ×1.585 and costs error ×1.682 |
| Ternary computing is more efficient than binary (Setun lineage, 1958–) | **[Verified]** on positions, **[Open conjecture]** on binary fabric | `ρ(r) = r/ln r` puts three 0.46% from optimum and two 6.15% away. Whether that is collectable depends on the fabric; on binary fabric this lab measured against it three times |

---

## Promotion ledger entries proposed

| date | claim | from | to | reason |
|---|---|---|---|---|
| 2026-08-10 | `φ` uniqueness and `Z[φ]` exactness | [Open conjecture] | **[Verified]** | Machine-checked with a negative control |
| 2026-08-10 | TNF on the block axis | [Open conjecture] | **[Retracted]** | Measured against, twice, with a structural reason |
| 2026-08-10 | Width rule's range estimator | [Empirical fit] | **[Retracted]** | Prediction falsified twice in the same run |

---

## Standing condition

The subject programme holds its own publication under a stated condition: the paper
is not submitted until a format is found that beats the incumbent block formats on
their own axis and workload. As of this case that condition is **not met**, and the
measurement on 2026-08-10 went against the subject. The condition is recorded here so
that the ledger, and not the authors alone, carries it.
