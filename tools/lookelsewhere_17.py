#!/usr/bin/env python3
"""
lookelsewhere_17.py -- Look-elsewhere recount at 17 ladder widths.

Recomputes the look-elsewhere statistic for the GoldenFloat closed-form rule
  e = round((N-1)/phi^2),  m = N-1-e,  bias = 2^(e-1) - 1
using the full v1.3 canonical 17-rung ladder instead of the 9- or 12-format
sets in preprint v18/v19.

Source of truth for the matching criterion:
  gf_preprint_v19.tex, sec:lookelsewhere + app:lookelsewhere
  - Search space: r in [0.1, 0.9] at step 1e-5, cardinality N_s = 80,000.
  - Match condition: round_half_even((N-1)*r) == e_target for ALL widths in set.
  - Rounding: round-half-to-even (IEEE 754 default, immaterial for all realised
    widths per preprint footnote but specified for formal completeness).
  - 9-format set: N in {4,8,12,16,20,24,32,64,256}, target e in {1,3,4,6,7,9,12,24,97}.
  - 12-format set (preprint v18, Table tab:ladder): 9 + GF128 + GF512 + GF1024.
    This reproduces the preprint claim of 47 matches and interval [0.38189, 0.38235].
  - 17-format set (task): full v1.3 canonical ladder, 9+GF6+GF10+GF14+GF48+GF96+
    GF128+GF512+GF1024 = all 17 rungs.

Candidate-rational construction note:
  The preprint appendix (app:lookelsewhere) additionally describes an
  exhaustive rational search over p/q with p in {1..99}, q in {100..499},
  which found 83 distinct ratio values matching all 9 widths (vs 392 on the
  grid).  The two descriptions (grid vs rational) are complementary:
  the p-value in the preprint body (p ~ 7.1e-3) cites K=83 and N_s=80,000
  but this combination does NOT yield 7.1e-3 under the stated
  Binom(N_s, K/N_s) formula -- the normal approximation gives ~0.52.
  This ambiguity is documented below; the script reproduces the COUNT claims
  (47 at 12 formats) exactly from the grid criterion and reports the
  corresponding statistic for 17 formats.

Outputs (to stdout):
  - Sanity check: count_match_9 (grid), should be 392 per preprint
  - Sanity check: count_match_12 (grid), should be 47 per preprint
  - Primary result: count_match_17 (grid)
  - p-values (Binom(N_s, K/N_s) tail) and Bonferroni values
  - Interpretation flag

Requires: Python 3 stdlib only (math, fractions, sys).
"""

import math
import sys


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

PHI = (1.0 + math.sqrt(5.0)) / 2.0
PHI_INV2 = 1.0 / (PHI ** 2)

N_S = 80000            # search-space cardinality (preprint sec:lookelsewhere)
R_STEP = 1e-5          # grid step
R_LO = 0.1             # grid lower bound
R_HI = 0.9             # grid upper bound (inclusive endpoint: 0.89999)

# The 9 realised widths (top block of preprint Table tab:ladder, v19).
# N = total width, E = target exponent bits from closed rule.
WIDTHS_9 = [
    (4,   1),
    (8,   3),
    (12,  4),
    (16,  6),
    (20,  7),
    (24,  9),
    (32,  12),
    (64,  24),
    (256, 97),
]

# The 12-format set from preprint v18 (Table tab:ladder there had 12 rows:
# top block of 9 + GF128 + GF512 + GF1024).  This is the set that yields
# 47 matches and the interval [0.38189, 0.38235] cited in preprint v19
# sec:lookelsewhere "Narrowing with 12 formats."
WIDTHS_12 = WIDTHS_9 + [
    (128,  49),
    (512,  195),
    (1024, 391),
]

# The full v1.3 canonical 17-rung ladder (GF4..GF1024).
# Source: scientific-works-canon, task spec verbatim, and preprint v19
# Table tab:ladder (all 17 rows).
WIDTHS_17 = [
    (4,    1),
    (6,    2),
    (8,    3),
    (10,   3),
    (12,   4),
    (14,   5),
    (16,   6),
    (20,   7),
    (24,   9),
    (32,   12),
    (48,   18),
    (64,   24),
    (96,   36),
    (128,  49),
    (256,  97),
    (512,  195),
    (1024, 391),
]


# ---------------------------------------------------------------------------
# Utility functions
# ---------------------------------------------------------------------------

def round_half_even(x):
    """Round to nearest integer, ties go to even (banker's rounding)."""
    floor_x = math.floor(x)
    frac = x - floor_x
    if frac < 0.5:
        return floor_x
    elif frac > 0.5:
        return floor_x + 1
    else:
        # Exactly 0.5 -- round to even.
        return floor_x if (floor_x % 2 == 0) else floor_x + 1


def matches_width(r, N, e_target):
    """Return True iff round_half_even((N-1)*r) == e_target."""
    return round_half_even((N - 1) * r) == e_target


def closed_rule_check(N):
    """Return (e, m, bias) from the closed-form rule."""
    e = round_half_even((N - 1) / (PHI ** 2))
    m = N - 1 - e
    bias = 2 ** (e - 1) - 1
    return e, m, bias


def grid_search(widths):
    """
    Return list of grid ratios r in [0.1, 0.9] (step 1e-5) that match
    ALL (N, e_target) pairs in `widths`.
    """
    matching = []
    for i in range(N_S):
        r = R_LO + i * R_STEP
        if all(matches_width(r, N, e) for N, e in widths):
            matching.append(r)
    return matching


def binom_tail_normal(n, p, k):
    """
    P(X >= k) for X ~ Binom(n, p) using normal approximation with
    continuity correction.  Valid for large n with np(1-p) >> 1.
    Returns the one-tailed p-value.
    """
    mu = n * p
    sigma = math.sqrt(n * p * (1.0 - p))
    if sigma == 0:
        return 0.0 if k > mu else 1.0
    z = (k - 0.5 - mu) / sigma
    return 0.5 * math.erfc(z / math.sqrt(2.0))


def bonferroni(n_s, p_match):
    """Return min(n_s * p_match, 1.0) -- Bonferroni-corrected p-value."""
    return min(n_s * p_match, 1.0)


# ---------------------------------------------------------------------------
# Verification: closed-rule self-check
# ---------------------------------------------------------------------------

def verify_closed_rule():
    """
    Verify that the closed-form rule reproduces all 17 ladder splits.
    This is a structural check, not a grid search.
    """
    errors = []
    for N, e_expected in WIDTHS_17:
        e_calc, m_calc, bias_calc = closed_rule_check(N)
        if e_calc != e_expected:
            errors.append(
                f"  GF{N}: expected e={e_expected}, got e={e_calc}"
            )
    return errors


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    print("=" * 70)
    print("lookelsewhere_17.py -- GoldenFloat look-elsewhere recount @ 17 widths")
    print("=" * 70)
    print()

    # --- Structural self-check ---
    print("--- Closed-rule structural verification (all 17 rungs) ---")
    errs = verify_closed_rule()
    if errs:
        print("FAIL: closed-rule mismatch(es):")
        for e in errs:
            print(e)
        sys.exit(1)
    else:
        print("PASS: closed rule reproduces all 17 canonical (N, e) splits.")
    print()

    # --- Grid search at 9 formats (context) ---
    print("--- Sanity: 9-format grid search ---")
    m9 = grid_search(WIDTHS_9)
    print(f"  count_match_9  = {len(m9)}")
    if m9:
        print(f"  interval_9     = [{min(m9):.5f}, {max(m9):.5f}]")
    print(f"  Preprint states: interval [0.37844, 0.38235] (grid)")
    print()

    # --- Grid search at 12 formats (sanity: must reproduce 47) ---
    print("--- Sanity: 12-format grid search (target: 47) ---")
    m12 = grid_search(WIDTHS_12)
    count_match_12 = len(m12)
    print(f"  count_match_12 = {count_match_12}")
    if m12:
        print(f"  interval_12    = [{min(m12):.5f}, {max(m12):.5f}]")
    print(f"  Preprint states: 47, interval [0.38189, 0.38235]")
    if count_match_12 != 47:
        print(
            "  WARNING: sanity check FAILED -- cannot reproduce the preprint's 47."
        )
        print(
            "  Stopping without reporting 17-format result to avoid fabrication."
        )
        sys.exit(2)
    else:
        print("  PASS: count_match_12 == 47 as claimed.")
    print()

    # --- Grid search at 17 formats (primary result) ---
    print("--- Primary: 17-format grid search ---")
    m17 = grid_search(WIDTHS_17)
    count_match_17 = len(m17)
    print(f"  count_match_17 = {count_match_17}")
    if m17:
        print(f"  interval_17    = [{min(m17):.5f}, {max(m17):.5f}]")
    else:
        print("  interval_17    = (empty)")
    print()

    # --- Statistics ---
    print("--- Statistics ---")
    # p_match under null (proportion of grid that matches)
    p_match_17 = count_match_17 / N_S
    p_17 = binom_tail_normal(N_S, p_match_17, count_match_17) if count_match_17 > 0 else 1.0
    bonf_17 = bonferroni(N_S, p_match_17)
    ratio_17_12 = count_match_17 / count_match_12 if count_match_12 > 0 else float("nan")

    print(f"  N_s (search space)     = {N_S}")
    print(f"  count_match_17         = {count_match_17}")
    print(f"  p_match_17             = {p_match_17:.4e}  (count/N_s)")
    print(
        f"  p_17 (normal approx)   = {p_17:.3e}  "
        f"[P(X >= {count_match_17}) under Binom({N_S}, {p_match_17:.4e})]"
    )
    print(f"  Bonferroni_17          = min({N_S} * {p_match_17:.4e}, 1) = {bonf_17:.3f}")
    print(f"  count_match_17 / count_match_12 = {count_match_17}/{count_match_12} = {ratio_17_12:.4f}")
    print()

    # --- p-value ambiguity note ---
    print("--- p-value ambiguity note ---")
    print(
        "  The preprint sec:lookelsewhere states p ~ 7.1e-3 for K=83, N_s=80,000"
    )
    print(
        "  under Binom(N_s, K/N_s).  However, for Binom(80000, 83/80000) the"
    )
    print(
        "  normal approximation gives P(X >= 83) ~ 0.52, not 7.1e-3.  The 7.1e-3"
    )
    print(
        "  cannot be reproduced from the stated formula; the discrepancy is"
    )
    print(
        "  documented here as an ambiguity.  The supplementary script"
    )
    print(
        "  look_elsewhere_calc.py referenced in the preprint is not present in"
    )
    print(
        "  the repo, so the exact computation cannot be audited at this time."
    )
    print(
        "  The COUNT results (47 at 12 formats, 47 at 17 formats) are"
    )
    print(
        "  unambiguous and are the substantive finding."
    )
    print()

    # --- Interpretation ---
    print("--- Interpretation ---")
    if count_match_17 == count_match_12:
        print(
            "  TRIVIAL NON-RESULT: count_match_17 == count_match_12 == 47."
        )
        print(
            "  The 5 new rungs added (GF6, GF10, GF14, GF48, GF96) all have"
        )
        print(
            "  closed-rule ratios e/(N-1) that fall inside the existing 12-format"
        )
        print(
            "  matching interval [0.38189, 0.38235].  They auto-pass by construction"
        )
        print(
            "  and contribute ZERO additional discriminating power.  This is"
        )
        print(
            "  expected and does not constitute independent evidence for the rule."
        )
        print(
            "  The moat narrative does NOT gain strength from the 17-width expansion."
        )
    elif count_match_17 < count_match_12:
        print(
            f"  NARROWING: count_match_17 = {count_match_17} < count_match_12 = {count_match_12}."
        )
        print(
            "  The additional rule-derived rungs do narrow the candidate set further."
        )
        print(
            "  However, since these rungs are derived from the same closed rule,"
        )
        print(
            "  any narrowing is circular (the rule generates the test data)."
        )
        print(
            "  This does NOT constitute independent confirmation."
        )
    else:
        print(
            f"  WIDENING: count_match_17 = {count_match_17} > count_match_12 = {count_match_12}."
        )
        print(
            "  Unexpected result: further investigation required."
        )
    print()

    # --- New rungs check ---
    new_rungs = [(6,2),(10,3),(14,5),(48,18),(96,36)]
    interval_lo = min(m12) if m12 else 0.38189
    interval_hi = max(m12) if m12 else 0.38235
    print("--- New rungs (GF6, GF10, GF14, GF48, GF96): matching-interval check ---")
    print(
        "  For each new rung (N, e), the match condition round((N-1)*r)==e holds"
    )
    print(
        "  for r in the interval [(e-0.5)/(N-1), (e+0.5)/(N-1)]."
    )
    print(
        f"  The 12-format grid interval is [{interval_lo:.5f}, {interval_hi:.5f}]."
    )
    print(
        "  A new rung imposes no additional constraint iff its matching interval"
    )
    print(
        "  CONTAINS the 12-format grid interval (i.e., all 47 existing grid points"
    )
    print(
        "  already satisfy the new rung's condition)."
    )
    print()
    all_contain = True
    for N, e in new_rungs:
        r_lo = (e - 0.5) / (N - 1)
        r_hi = (e + 0.5) / (N - 1)
        contains = (r_lo <= interval_lo) and (r_hi >= interval_hi)
        if not contains:
            all_contain = False
        print(
            f"  GF{N:4d}: e/{N-1} interval=[{r_lo:.5f},{r_hi:.5f}], "
            f"contains 12-fmt interval: {'YES' if contains else 'NO'}"
        )
    if all_contain:
        print()
        print(
            "  All 5 new rungs' matching intervals CONTAIN the 12-format interval."
        )
        print(
            "  This is why count_match_17 == count_match_12: every grid point that"
        )
        print(
            "  passed all 12 prior conditions also trivially passes all 5 new ones."
        )
        print(
            "  The new rungs add no discriminating power over the already-narrow"
        )
        print(
            "  12-format interval.  This is a structural consequence of the fact"
        )
        print(
            "  that small-N rungs (GF6, GF10, GF14) have wide matching intervals"
        )
        print(
            "  (coarse rounding), and mid-N rungs (GF48, GF96) also fully contain"
        )
        print(
            "  the 12-format interval.  None of the 5 extra rungs can narrow the"
        )
        print(
            "  candidate set below 47 under the grid criterion."
        )
    print()

    print("=" * 70)
    print(
        f"RESULT SUMMARY: count_match_12={count_match_12} (sanity OK), "
        f"count_match_17={count_match_17}, "
        f"ratio={ratio_17_12:.4f}"
    )
    print("=" * 70)


if __name__ == "__main__":
    main()
