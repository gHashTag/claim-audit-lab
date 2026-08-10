# CASE-10  --  Vasilev / Ternary Network Floats and the golden weight alphabet

**Target:** `gHashTag/trinity-fpga`, `research/arxiv_tnf/tnf_paper.tex`, with
measurements in `research/block/` and `fpga/tnet/`, and the machine-checked
component in `gHashTag/trinity-s3ai`, `derivations/golden_alphabet/`.

**Author taxonomy:** none stated in the paper. Per FRAMEWORK, the strongest
published wording is taken and promotion applied only where this framework's
requirements are met. The subject repository does maintain a five-value ledger
(`docs/claims.yaml`) whose vocabulary matches this lab's labels one-to-one.

**Date:** 2026-08-10.

## Specific claims surveyed

### `\Verified`

| claim | basis |
|---|---|
| `phi*phi = phi + 1`; any `r > 1` with `r*r = r + 1` is `phi` | Machine-checked on `coqorg/coq:8.20.1`. `coqc` exit 0, `coqchk` reports no type-in-type, no unsafe fixpoints, no assumed positivity; zero `Admitted`, zero `Axiom` |
| On integer pairs `(a,b)` standing for `a + b*phi`, multiplying by `phi` is `(a,b) -> (b, a+b)` | Same file, same kernel check |
| The linear path of a `{-phi, 0, +phi}` network is exact at any fan-in and depth | `dot_exact`, kernel-checked. A statement about arithmetic, not a measurement |
| `phi^(k+1) = F_(k+1)*phi + F_k` | `phi_pow_fib`, kernel-checked by induction |
| Coverage: the family dominates a width-N format iff `m + ceil(log3(b+1)) <= N-1` | Two lines of algebra over the family definition, independently re-derivable |
| No catalogued uniform binary format escapes; 28 checked at 8/16/32/64/128 bits | Follows from coverage plus the uniform budget `m + log2(b+1) <= N-1`. The enumeration is a check, not the argument |
| BNF16 and TNF16 land within 1 percent in placed silicon | Post-route on XC7A200T in an open flow, with the prediction computed before synthesis |

A negative control was run before the kernel's green was trusted: altering
`phi_unique`'s conclusion to `r = phi + 1` makes compilation fail with exit 1.
This lab treats an unexercised checker as unmeasured, so the control is recorded
as part of the basis rather than as a courtesy.

### `\Efit`

| claim | sample it rests on |
|---|---|
| Accumulator error grows as `sqrt(pK)` in fan-in | Fitted exponents `+0.476` and `+0.435` against a predicted `+0.5`. One model, one layer type |
| Precision law `0.5 * E[1/s] * 2^-(M+1)`, holding to 3 percent across eight rungs | Derived, then measured; the 3 percent is a residual over a finite sample |
| Area law `A(M) = 141 + 2.4455*M^2`, R^2 = 0.99963 | Regression over `M` in [7, 90] |
| Throughput-per-area ordering among range-carrying formats | One harness, one datapath, one device; decoders from an open verification set rather than vendor-optimised |
| Within-block span of 1.89 binades median, 3.04 at the 99th percentile | One model. The estimator was later found wrong for a different purpose; see `\Retr` |

### `\Conj`

| claim | `\Fpath` |
|---|---|
| The pair {GFTernary, TNF} is a reference format for a ternary datapath | Exhibit a pair closing the same two sites at lower area or higher accuracy on the same harness. The claim is bounded to datapaths whose weights are codes |
| The radix argument pays only where a position is physically ternary | Build a binary-fabric format with a ternary exponent that beats its binary sibling on a live workload. Three attempts went the other way |
| A format beating MX / NVFP4 on the block axis exists | Stated by the subject as the standing condition on its own publication. Not met; see below |

### `\Retr`

Recorded permanently; none is to be cited again as evidence.

| claim | date | what happened |
|---|---|---|
| `tnet` comparison at 440 vs 895 LUTs, 5.1x | 2026-08 | TNF received pre-widened fields while competitors unpacked theirs. Corrected to matched width on packed words: 3.1x at 16 bits, 5.6x at 32 |
| TNF64 area predicted at 4762 LUT | 2026-08 | Measured 7479, a 36 percent miss. Power law replaced by the quadratic area law |
| TNF128 does not route | 2026-08 | It routes at 4869 LUT, 56 DSP, 103.39 MHz. The failure was under a self-imposed `-nodsp` constraint |
| int4 beats MXFP4 by 27 percent | 2026-08-09 | The harness gave E2M1 six magnitudes where the OCP spec gives eight. Corrected: MXFP4 21.94 against int4 30.89 |
| TNF beats MXFP4 on the block axis | 2026-08-10 | Measured against the subject. MXFP4 21.94 vs TNF4 36.72; MXFP6 14.73 vs TNF6 18.03. `3^Et` never divides `2^k`, so packing loses up to 25 percent of a 4-bit alphabet |
| Width rule predicts BNF8 `E=4` and TNF8 `Et=3` | 2026-08-10 | Winners were `E=3` and `Et=2`, both one step narrower. The rule's form survives; its range estimator was wrong, crediting a 0.1-percentile tail carrying almost no energy |
| Levers are nearly multiplicative | 2026-08 | Ratio computed against a losing baseline. Order-dependence measured at 2.78x |
| arXiv:2606.05017 and 2606.09686 cite GF-T | 2026-08 | They do not. Corrected by the author |

Eight further defects of instrument rather than of claim are logged in the subject
repository, including a simulator returning error identically zero at every fan-in,
and a level table built from position counts that produced a 100x artefact against
the subject's own format.

## Why this CASE is not a `\Risk` case

Two of the eight retractions were entered on the day the measurement contradicted
the subject, and both went against the subject's interest. Under CHARTER section 10
that is the behaviour the register exists to reward rather than to penalise. The
open items are labelled `\Conj` with executable falsification paths, not left
unlabelled.

## What this CASE adds to claim-audit-lab

The first case whose `\Verified` rows rest on a kernel check with a negative
control, rather than on re-derivation by the auditor. It also supplies a mapping
precedent: the subject's own five-value ledger vocabulary
(`verified`, `empirical_fit`, `open_conjecture`, `high_risk_or_falsified`,
`retracted_or_unverified`) maps one-to-one onto this framework's labels, so future
cases against that programme need no translation table.

## 9. Symmetric mirror

The subject here is the lab's own programme, so the mirror runs outward: external
claims are labelled by the identical standard, and the asymmetry runs in neither
direction.

| external claim | label | reasoning |
|---|---|---|
| MXFP4 (OCP): E2M1 with a shared UE8M0 scale is a suitable 4-bit inference format | `\Verified` on the measured workload | Reproduced here at perplexity 21.94 against an fp32 baseline of 14.49, with the spec's own scale and level count. The subject's own measurement supports it |
| MXFP4 / NVFP4 support training | `\Efit`, not `\Verified` | Every published sub-8-bit training result carries block scales and a higher-precision master weight. The element alone carries no range |
| posit: tapered precision is worth its decode cost | `\Efit` | Accuracy near unity is real. The measured decode cost of 2.4x to 6.4x throughput per area does not contradict the original claim, which does not deny it |
| takum: a logarithmic value law is a good general-purpose choice | `\Conj` | `\Fpath`: a datapath staying in the logarithmic domain never pays the `2^f` table. The 10967 LUT and 84 RAMB36 measured for `takum32_decode` penalise a design that converts, not one that does not |
| Ternary27: a radix-3 scale is preferable | `\Retr` by measurement | At equal storage (43 bits) it is dominated with five positions to spare. Radix-3 scaling buys range x1.585 and costs error x1.682 |
| Ternary computing is more efficient than binary (Setun lineage, 1958 onward) | `\Verified` on positions, `\Conj` on binary fabric | `rho(r) = r / ln r` places three 0.46 percent from optimum and two 6.15 percent away. Whether that is collectable depends on the fabric; on binary fabric this subject measured against it three times |

The joint `\Fpath` for the subject's block-axis `\Conj` and for the MXFP4 training
row is the same experiment: a sub-8-bit training run in which the element format is
varied while block scale and master-weight precision are held fixed. Executing it
once would resolve both the subject's standing condition and the external row.

## Status row for cases.yaml

```yaml
- id: CASE-10
  title: "Vasilev Ternary Network Floats and the golden weight alphabet"
  target: "gHashTag/trinity-fpga research/arxiv_tnf; gHashTag/trinity-s3ai derivations/golden_alphabet"
  claim_status: Verified
  fpath: "Sub-8-bit training run varying the element format with block scale and master-weight precision held fixed"
  file: cases/CASE-10-vasilev-tnf-golden-alphabet.md
```

## Anchor

phi^2 + phi^-2 = 3
