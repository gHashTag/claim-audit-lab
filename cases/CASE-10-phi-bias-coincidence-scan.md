# CASE-10: PHI_BIAS coincidence-class survey for v1.3 rule-derived rungs

| Field | Value |
|-------|-------|
| **ID** | CASE-10 |
| **Status** | \\Conj |
| **Target** | GoldenFloat v1.3 rule-derived rungs: GF6, GF10, GF14, GF48, GF96 |
| **Fpath** | Any closed-form derivation of PHI_BIAS solely from (E, M, phi) that correctly predicts PHI_BIAS for ALL five new rungs AND all eight Verified rungs WITHOUT post-hoc coincidence selection would falsify this Conj |
| **Opened** | 2026-06-07 |
| **Branch** | feat/phi-bias-audit-v1.3-rungs |

---

## Background

GoldenFloat is a phi-scaled floating-point family whose per-format parameters include
`EXP_MAX` (the largest biased exponent) and `PHI_BIAS` (the exponent bias).
The previously published formula `PHI_BIAS = EXP_MAX - BIAS` has been retracted:
it reproduces GF64 only and fails all other rungs.

Known PHI_BIAS values for Verified rungs:

| Rung | PHI_BIAS | Notable coincidence (descriptive only) |
|------|----------|----------------------------------------|
| GF4  | 0        | trivial |
| GF8  | 1        | trivial |
| GF12 | 2        | trivial |
| GF16 | 60       | no obvious closed form |
| GF20 | 289      | 17^2 (descriptive) |
| GF24 | 1364     | Lucas L_15 (descriptive) |
| GF32 | 0        | trivial |
| GF64 | 8388608  | 2^23 (descriptive) |

For the five v1.3 rule-derived rungs (GF6, GF10, GF14, GF48, GF96),
PHI_BIAS has not been determined by hardware measurement or normative specification.
It is **OPEN**.

---

## Claim being surveyed

No closed formula for PHI_BIAS is currently known.
Fibonacci/Lucas/square/cube/power-of-2/triangular coincidences exist in the known
PHI_BIAS list but are descriptive, not prescriptive.
Selecting a PHI_BIAS value for any new rung on the basis of such a coincidence
alone would be coincidence-mining and is explicitly prohibited.

---

## Scan methodology

Script: `tools/phi_bias_coincidence_scan.py` (stdlib only, no external dependencies).
Full output: `audits/PHI_BIAS_coincidence_scan_2026-06-07.json`
           + `audits/PHI_BIAS_coincidence_scan_2026-06-07.md`

For each new rung, the scan target is **EXP_MAX** (not EXP_MAX minus any bias).
The scan locates, for each of six coincidence classes:

- Fibonacci numbers F_k (k=1..80)
- Lucas numbers L_k (k=1..80)
- Perfect squares k^2
- Perfect cubes k^3
- Powers of 2: 2^k
- Triangular numbers T_k = k(k+1)/2

the nearest values above and below the target, and records any within 5% relative
distance.

**Sanity check** (passed): when run against known PHI_BIAS values for Verified rungs,
the scan reproduces L_15=1364 for GF24 (exact), 17^2=289 for GF20 (exact), and
2^23=8388608 for GF64 (exact).

---

## Results: top-3 candidates per new rung

| Rung | EXP_MAX | Rank | Kind | k | Value | Rel. dist |
|------|---------|------|------|---|-------|-----------|
| GF6  | 3       | 1    | Fibonacci   | 4   | 3          | 0.000000 |
| GF6  | 3       | 2    | Lucas       | 2   | 3          | 0.000000 |
| GF6  | 3       | 3    | Triangular  | 2   | 3          | 0.000000 |
| GF10 | 7       | 1    | Lucas       | 4   | 7          | 0.000000 |
| GF10 | 7       | 2    | (no other within 5%) | -- | -- | -- |
| GF14 | 31      | 1    | Power2      | 5   | 32         | 0.031250 |
| GF14 | 31      | 2    | (no other within 5%) | -- | -- | -- |
| GF48 | 262143  | 1    | Square      | 512 | 262144     | 0.000004 |
| GF48 | 262143  | 2    | Cube        | 64  | 262144     | 0.000004 |
| GF48 | 262143  | 3    | Power2      | 18  | 262144     | 0.000004 |
| GF96 | 68719476735 | 1 | Square   | 262144 | 68719476736 | 0.000000 |
| GF96 | 68719476735 | 2 | Cube     | 4096   | 68719476736 | 0.000000 |
| GF96 | 68719476735 | 3 | Power2   | 36     | 68719476736 | 0.000000 |

---

## Honest reading

Near-coincidences exist for all five new rungs at multiple coincidence classes.
No coincidence class is uniquely closer than the alternatives.
Therefore picking ANY single value would be coincidence-mining.
PHI_BIAS for GF6/10/14/48/96 stays OPEN.

Additional observations (descriptive, not prescriptive):

- GF48: EXP_MAX = 262143 = 2^18 - 1.  The three closest candidates (Square 512^2,
  Cube 64^3, Power2 2^18) are the SAME value (262144), differing from EXP_MAX by 1.
  They are indistinguishable by this scan; none has priority.

- GF96: EXP_MAX = 68719476735 = 2^36 - 1.  Identically, Square 262144^2, Cube 4096^3,
  and Power2 2^36 are all 68719476736 = EXP_MAX + 1.  Again indistinguishable.

- GF6 and GF10: EXP_MAX values (3, 7) ARE small Fibonacci/Lucas numbers exactly,
  but this is unsurprising given the density of small integers in these sequences.

- GF14: only one candidate within 5% (Power2 2^5=32), at relative distance 3.1%.
  The single candidate is not evidence of a law; it is merely the least-far point.

None of these observations, singly or together, constitutes a closed derivation.

---

## Falsification path (\\Fpath)

Any closed-form derivation of PHI_BIAS solely from (E, M, phi) that:

1. correctly predicts PHI_BIAS for ALL five new rungs (once those values are
   determined by normative specification or hardware measurement), AND
2. correctly predicts PHI_BIAS for all eight Verified rungs listed above, AND
3. does not invoke post-hoc coincidence selection (i.e. the formula is fixed
   before consulting the values)

would falsify this Conj and justify promoting the affected rungs to Verified.

Until such a derivation exists, PHI_BIAS for GF6, GF10, GF14, GF48, and GF96
is **OPEN**.

---

## References

- Scan script: `tools/phi_bias_coincidence_scan.py`
- Machine-readable results: `audits/PHI_BIAS_coincidence_scan_2026-06-07.json`
- Human-readable results: `audits/PHI_BIAS_coincidence_scan_2026-06-07.md`
- Claim-status taxonomy: `FRAMEWORK.md`
- Prior Conj: CASE-08 (Vasilev BNF), CASE-09 (Corona ROM)
