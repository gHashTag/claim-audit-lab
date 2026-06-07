# CASE-12: Claim

**Status:** [Open conjecture] (\\Conj) -- empirical; grammar and MDL proxy
are heuristic. See `status.md` for upgrade conditions.

---

## Primary claim (verbatim from v2.3 context)

Within a depth-<=2 BNF enumeration over the phi-native atom set
{\\varphi^k : k in {-2, -1, 0, 1, 2}} with binary operators {+, -, *, /}
and an anti-cancellation normalization filter, G_phi = \\varphi^2 + \\varphi^{-2}
achieves MDL rank 2 of 394 essential phi-native forms. The 40,100-expression
enumeration yields 501 expressions algebraically equal to 3 (via
sympy.simplify); of these, 497 are phi-native and 394 are essential after
anti-cancellation filtering. G_phi ranks 2nd by MDL string-length proxy.
Rank 1 is the commutative twin \\varphi^{-2} + \\varphi^2 (same expression,
operands swapped). Bootstrap significance: p = 0.0039 (B = 10,000 resamples);
empirical p = 0.0051.

---

## Reframing relative to CASE-08

CASE-08 reported raw rank 2/1000 without the anti-cancellation filter.
CASE-12 refines that result: after applying the W1+W8 anti-cancellation
filter (see `evidence.md`), the essential class contains 394 forms. G_phi
retains rank 2 in the filtered class. The claim is therefore NOT
"G_phi is the unique simplest form" but rather "G_phi is MDL-optimal in
the equivalence class of approximately 100 commutatively-equivalent forms,
within the stated grammar and MDL encoding."

---

## Source

phi-paper v2.3-draft, sec.6.3 ("Equivalence-class analysis and
MDL-canonical Lucas form (v2.3)") and sec.6.4 ("Anti-cancellation filter
and essential-class definition"). LOCAL ONLY pending Pellis approval.
Reproducibility capsule: phi-paper/reproducibility/v23/ (run_v23.py,
results_v23.json, README, changes). See `sources.md` for full reference list.

---

**End of claim.md.**
