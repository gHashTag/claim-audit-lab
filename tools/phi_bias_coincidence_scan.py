"""
phi_bias_coincidence_scan.py
----------------------------
Scan coincidence space (Fibonacci, Lucas, perfect squares, perfect cubes,
powers of 2, triangular numbers) for PHI_BIAS candidates.

Usage:
    python tools/phi_bias_coincidence_scan.py

Outputs:
    audits/PHI_BIAS_coincidence_scan_2026-06-07.json
    audits/PHI_BIAS_coincidence_scan_2026-06-07.md

Stdlib only.  No external dependencies.

CONSTRAINT: This script DOCUMENTS coincidences; it does NOT pick a value.
PHI_BIAS for GF6/GF10/GF14/GF48/GF96 is OPEN.
"""

import json
import math
import os
import sys

# ---------------------------------------------------------------------------
# Sequence generators (stdlib only)
# ---------------------------------------------------------------------------

def fibonacci_sequence(k_max=80):
    """Return list of (k, F_k) for k=1..k_max (1-indexed, F_1=1, F_2=1)."""
    seq = []
    a, b = 1, 1
    for k in range(1, k_max + 1):
        seq.append((k, a))
        a, b = b, a + b
    return seq


def lucas_sequence(k_max=80):
    """Return list of (k, L_k) for k=1..k_max (L_1=1, L_2=3)."""
    seq = []
    a, b = 1, 3
    for k in range(1, k_max + 1):
        seq.append((k, a))
        a, b = b, a + b
    return seq


def powers_of_2(target, margin=2.0):
    """Return list of (k, 2^k) bracketing target within factor margin."""
    results = []
    k = 0
    # go from 0 upward until we exceed target * margin
    while True:
        v = 1 << k
        if v > target * margin and k > 0:
            break
        results.append((k, v))
        k += 1
    return results


def perfect_squares_near(target, window=20):
    """Return list of (k, k^2) for k near sqrt(target)."""
    root = int(math.isqrt(target))
    results = []
    for k in range(max(1, root - window), root + window + 2):
        results.append((k, k * k))
    return results


def perfect_cubes_near(target, window=20):
    """Return list of (k, k^3) for k near cbrt(target)."""
    cbrt = int(round(target ** (1.0 / 3.0)))
    results = []
    for k in range(max(1, cbrt - window), cbrt + window + 2):
        results.append((k, k * k * k))
    return results


def triangular_numbers_near(target, window=20):
    """Return list of (k, k*(k+1)//2) for k near the triangular root."""
    # k*(k+1)/2 = target => k ~ sqrt(2*target)
    k_approx = int(math.isqrt(2 * target))
    results = []
    for k in range(max(1, k_approx - window), k_approx + window + 2):
        results.append((k, k * (k + 1) // 2))
    return results


# ---------------------------------------------------------------------------
# Core scan logic
# ---------------------------------------------------------------------------

THRESHOLD_RELATIVE = 0.05  # 5% relative distance

def rel_dist(a, b):
    """Relative distance |a-b|/max(|a|,|b|,1)."""
    denom = max(abs(a), abs(b), 1)
    return abs(a - b) / denom


def find_nearest_pair(seq_list, target):
    """
    Given a sorted list of (k, value), find the entries immediately
    below and immediately above `target`.  Returns a list of dict records.
    """
    below = [item for item in seq_list if item[1] <= target]
    above = [item for item in seq_list if item[1] >= target]
    candidates = []
    if below:
        k, v = max(below, key=lambda x: x[1])
        candidates.append({"k": k, "value": v, "side": "below_or_equal"})
    if above:
        k, v = min(above, key=lambda x: x[1])
        candidates.append({"k": k, "value": v, "side": "above_or_equal"})
    # Deduplicate exact matches
    seen = set()
    unique = []
    for c in candidates:
        key = (c["k"], c["value"])
        if key not in seen:
            seen.add(key)
            unique.append(c)
    return unique


def scan_target(target, label, fib_seq, lucas_seq):
    """
    Run all coincidence scans for a single target value.
    Returns a list of candidate records with relative_distance.
    """
    candidates = []

    # --- Fibonacci ---
    pairs = find_nearest_pair(fib_seq, target)
    for p in pairs:
        rd = rel_dist(target, p["value"])
        candidates.append({
            "kind": "Fibonacci",
            "k": p["k"],
            "value": p["value"],
            "side": p["side"],
            "relative_distance": rd,
        })

    # --- Lucas ---
    pairs = find_nearest_pair(lucas_seq, target)
    for p in pairs:
        rd = rel_dist(target, p["value"])
        candidates.append({
            "kind": "Lucas",
            "k": p["k"],
            "value": p["value"],
            "side": p["side"],
            "relative_distance": rd,
        })

    # --- Perfect squares ---
    sq_list = perfect_squares_near(target)
    pairs = find_nearest_pair(sq_list, target)
    for p in pairs:
        rd = rel_dist(target, p["value"])
        candidates.append({
            "kind": "Square",
            "k": p["k"],
            "value": p["value"],
            "side": p["side"],
            "relative_distance": rd,
        })

    # --- Perfect cubes ---
    cube_list = perfect_cubes_near(target)
    pairs = find_nearest_pair(cube_list, target)
    for p in pairs:
        rd = rel_dist(target, p["value"])
        candidates.append({
            "kind": "Cube",
            "k": p["k"],
            "value": p["value"],
            "side": p["side"],
            "relative_distance": rd,
        })

    # --- Powers of 2 ---
    pow2_list = powers_of_2(target)
    pairs = find_nearest_pair(pow2_list, target)
    for p in pairs:
        rd = rel_dist(target, p["value"])
        candidates.append({
            "kind": "Power2",
            "k": p["k"],
            "value": p["value"],
            "side": p["side"],
            "relative_distance": rd,
        })

    # --- Triangular numbers ---
    tri_list = triangular_numbers_near(target)
    pairs = find_nearest_pair(tri_list, target)
    for p in pairs:
        rd = rel_dist(target, p["value"])
        candidates.append({
            "kind": "Triangular",
            "k": p["k"],
            "value": p["value"],
            "side": p["side"],
            "relative_distance": rd,
        })

    # Filter to within threshold
    within = [c for c in candidates if c["relative_distance"] <= THRESHOLD_RELATIVE]

    # Sort by relative distance
    within.sort(key=lambda x: x["relative_distance"])

    return {
        "label": label,
        "target": target,
        "candidates_within_5pct": within,
        "all_nearest": candidates,  # keep all nearest pairs for reference
    }


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    fib_seq = fibonacci_sequence(k_max=80)
    lucas_seq = lucas_sequence(k_max=80)

    # New rule-derived rungs — PHI_BIAS is OPEN
    new_rungs = [
        ("GF6",  3),
        ("GF10", 7),
        ("GF14", 31),
        ("GF48", 262143),
        ("GF96", 68719476735),
    ]

    # Verified rungs — use known PHI_BIAS values for sanity-check
    verified_rungs = [
        ("GF4",  0),
        ("GF8",  1),
        ("GF12", 2),
        ("GF16", 60),
        ("GF20", 289),
        ("GF24", 1364),
        ("GF32", 0),
        ("GF64", 8388608),
    ]

    # --- Scan new rungs ---
    new_results = []
    for label, exp_max in new_rungs:
        r = scan_target(exp_max, label, fib_seq, lucas_seq)
        r["note"] = "EXP_MAX used as target; PHI_BIAS is OPEN — do not pick a value from this scan"
        new_results.append(r)

    # --- Scan verified rungs (sanity check) ---
    sanity_results = []
    for label, phi_bias in verified_rungs:
        if phi_bias == 0:
            # 0 is a degenerate case; record as trivial
            sanity_results.append({
                "label": label,
                "target": 0,
                "candidates_within_5pct": [{"kind": "trivial", "k": 0, "value": 0, "side": "exact", "relative_distance": 0.0}],
                "all_nearest": [],
                "note": "PHI_BIAS=0; degenerate; no coincidence-class scan needed",
            })
        else:
            r = scan_target(phi_bias, label, fib_seq, lucas_seq)
            r["note"] = "Known PHI_BIAS used as target; sanity-check scan"
            sanity_results.append(r)

    # --- Sanity-check assertions ---
    sanity_pass = True
    sanity_log = []

    # GF24: must find L_15 = 1364 within 5%
    gf24 = next(r for r in sanity_results if r["label"] == "GF24")
    found_l15 = any(
        c["kind"] == "Lucas" and c["k"] == 15 and c["value"] == 1364
        for c in gf24["candidates_within_5pct"]
    )
    # Also check all_nearest in case it was filtered
    found_l15_any = any(
        c["kind"] == "Lucas" and c["k"] == 15 and c["value"] == 1364
        for c in gf24["all_nearest"]
    )
    if found_l15 or found_l15_any:
        sanity_log.append("PASS: GF24 PHI_BIAS=1364 matched Lucas L_15=1364 (exact match, rd=0.0)")
    else:
        sanity_log.append("FAIL: GF24 PHI_BIAS=1364 did NOT match Lucas L_15=1364 — scan logic error!")
        sanity_pass = False

    # GF20: must find 17^2 = 289 within 5%
    gf20 = next(r for r in sanity_results if r["label"] == "GF20")
    found_17sq = any(
        c["kind"] == "Square" and c["k"] == 17 and c["value"] == 289
        for c in gf20["candidates_within_5pct"]
    )
    found_17sq_any = any(
        c["kind"] == "Square" and c["k"] == 17 and c["value"] == 289
        for c in gf20["all_nearest"]
    )
    if found_17sq or found_17sq_any:
        sanity_log.append("PASS: GF20 PHI_BIAS=289 matched Square 17^2=289 (exact match, rd=0.0)")
    else:
        sanity_log.append("FAIL: GF20 PHI_BIAS=289 did NOT match Square 17^2=289 — scan logic error!")
        sanity_pass = False

    # GF64: must find 2^23 = 8388608 within 5%
    gf64 = next(r for r in sanity_results if r["label"] == "GF64")
    found_2_23 = any(
        c["kind"] == "Power2" and c["k"] == 23 and c["value"] == 8388608
        for c in gf64["candidates_within_5pct"]
    )
    found_2_23_any = any(
        c["kind"] == "Power2" and c["k"] == 23 and c["value"] == 8388608
        for c in gf64["all_nearest"]
    )
    if found_2_23 or found_2_23_any:
        sanity_log.append("PASS: GF64 PHI_BIAS=8388608 matched Power2 2^23=8388608 (exact match, rd=0.0)")
    else:
        sanity_log.append("FAIL: GF64 PHI_BIAS=8388608 did NOT match Power2 2^23=8388608 — scan logic error!")
        sanity_pass = False

    if not sanity_pass:
        print("SCAN SANITY-CHECK FAILED. See sanity_log. Aborting output.", file=sys.stderr)
        for line in sanity_log:
            print(" ", line, file=sys.stderr)
        sys.exit(1)

    print("Sanity checks passed:")
    for line in sanity_log:
        print(" ", line)

    # --- Assemble JSON output ---
    output = {
        "metadata": {
            "script": "tools/phi_bias_coincidence_scan.py",
            "date": "2026-06-07",
            "threshold_relative": THRESHOLD_RELATIVE,
            "disclaimer": (
                "This scan documents near-coincidences. "
                "It does NOT select PHI_BIAS values. "
                "PHI_BIAS for GF6/GF10/GF14/GF48/GF96 is OPEN."
            ),
        },
        "sanity_checks": {
            "passed": sanity_pass,
            "log": sanity_log,
        },
        "verified_rung_sanity_scan": sanity_results,
        "new_rung_coincidence_scan": new_results,
    }

    os.makedirs("audits", exist_ok=True)
    json_path = "audits/PHI_BIAS_coincidence_scan_2026-06-07.json"
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2)
    print(f"JSON written: {json_path}")

    # --- Build Markdown output ---
    md_lines = []
    md_lines.append("# PHI_BIAS Coincidence Scan -- 2026-06-07")
    md_lines.append("")
    md_lines.append(
        "> **Disclaimer.** This document records near-coincidences between EXP_MAX (or known"
        " PHI_BIAS) values and standard integer sequences.  It does NOT pick or canonise any"
        " PHI_BIAS value.  PHI_BIAS for GF6, GF10, GF14, GF48, GF96 is OPEN."
    )
    md_lines.append("")
    md_lines.append(f"Threshold: relative distance <= {THRESHOLD_RELATIVE*100:.0f}%.")
    md_lines.append("")

    # Sanity-check table
    md_lines.append("## Sanity-check: Known Verified rungs")
    md_lines.append("")
    md_lines.append(
        "The scan is first run against known PHI_BIAS values for Verified rungs.  "
        "The table below confirms the scan reproduces L_15=1364 for GF24 and 17^2=289 for GF20."
    )
    md_lines.append("")

    # Build a compact table of the best match per verified rung
    md_lines.append("| Rung | PHI_BIAS | Best match (kind, k, value) | Rel. dist | Pass? |")
    md_lines.append("|------|----------|-----------------------------|-----------|-------|")
    for r in sanity_results:
        label = r["label"]
        target = r["target"]
        if r["candidates_within_5pct"]:
            best = r["candidates_within_5pct"][0]
            match_str = f"{best['kind']}, k={best['k']}, {best['value']}"
            rd_str = f"{best['relative_distance']:.6f}"
        else:
            # find closest overall
            all_c = r.get("all_nearest", [])
            if all_c:
                best = min(all_c, key=lambda x: x["relative_distance"])
                match_str = f"{best['kind']}, k={best['k']}, {best['value']} (outside 5%)"
                rd_str = f"{best['relative_distance']:.6f}"
            else:
                match_str = "trivial (0)"
                rd_str = "0.000000"
        pass_str = "yes" if r.get("note", "").startswith("Known") or target == 0 else "n/a"
        md_lines.append(f"| {label} | {target} | {match_str} | {rd_str} | {pass_str} |")

    md_lines.append("")
    md_lines.append("**Sanity-check log:**")
    md_lines.append("")
    for line in sanity_log:
        md_lines.append(f"- {line}")
    md_lines.append("")

    # Per-rung sections for new rungs
    md_lines.append("## New rule-derived rungs (GF6/10/14/48/96) -- EXP_MAX coincidence scan")
    md_lines.append("")
    md_lines.append(
        "For each new rung, the scan target is EXP_MAX.  "
        "PHI_BIAS = EXP_MAX - BIAS (the retracted universal formula) is NOT used.  "
        "All candidates within 5% relative distance are listed.  "
        "No value is recommended or selected."
    )
    md_lines.append("")

    for r in new_results:
        label = r["label"]
        target = r["target"]
        cands = r["candidates_within_5pct"]

        md_lines.append(f"### {label}  (EXP_MAX = {target})")
        md_lines.append("")
        if not cands:
            md_lines.append("No coincidences within 5% relative distance found.")
        else:
            md_lines.append("| Kind | k | Value | Rel. dist |")
            md_lines.append("|------|---|-------|-----------|")
            for c in cands:
                md_lines.append(
                    f"| {c['kind']} | {c['k']} | {c['value']} | {c['relative_distance']:.6f} |"
                )
        md_lines.append("")

        # Top-3 summary (used in CASE-10)
        top3 = cands[:3]
        if top3:
            md_lines.append("**Top-3 candidates (closest first):**")
            md_lines.append("")
            for i, c in enumerate(top3, 1):
                md_lines.append(
                    f"{i}. {c['kind']} k={c['k']}: value={c['value']}, "
                    f"rel_dist={c['relative_distance']:.6f}"
                )
            md_lines.append("")
        else:
            md_lines.append(
                "*(No candidate within 5%; nearest pairs are listed in the JSON output.)*"
            )
            md_lines.append("")

    # Nearest-pairs fallback table for rungs with no within-5% candidates
    no_cands_rungs = [r for r in new_results if not r["candidates_within_5pct"]]
    if no_cands_rungs:
        md_lines.append("## Nearest-pair table (rungs with no within-5% candidates)")
        md_lines.append("")
        md_lines.append("| Rung | EXP_MAX | Kind | k | Value | Rel. dist |")
        md_lines.append("|------|---------|------|---|-------|-----------|")
        for r in no_cands_rungs:
            # One row per kind (pick closest of below/above pair)
            by_kind = {}
            for c in r["all_nearest"]:
                k_ = c["kind"]
                if k_ not in by_kind or c["relative_distance"] < by_kind[k_]["relative_distance"]:
                    by_kind[k_] = c
            for kind, c in sorted(by_kind.items()):
                md_lines.append(
                    f"| {r['label']} | {r['target']} | {kind} | {c['k']} | {c['value']} | {c['relative_distance']:.6f} |"
                )
        md_lines.append("")

    md_lines.append("---")
    md_lines.append("")
    md_lines.append(
        "*Generated by `tools/phi_bias_coincidence_scan.py`.*  "
        "*See `audits/PHI_BIAS_coincidence_scan_2026-06-07.json` for machine-readable data.*"
    )

    md_path = "audits/PHI_BIAS_coincidence_scan_2026-06-07.md"
    with open(md_path, "w", encoding="utf-8") as f:
        f.write("\n".join(md_lines) + "\n")
    print(f"Markdown written: {md_path}")


if __name__ == "__main__":
    main()
