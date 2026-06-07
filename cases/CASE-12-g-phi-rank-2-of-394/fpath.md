# CASE-12: Falsification Path (\\Fpath)

The v2.3 rank-2/394 result is an [Open conjecture]. Two concrete experiments
can falsify it. Either experiment, if it succeeds, requires downgrading the
v2.3 sec.6.3 claim in the phi-paper manuscript.

---

## Fpath A: Demonstrate a strictly shorter phi-native form

**Experiment:** Within the same depth-<=2 BNF grammar over
{\\varphi^k : k in {-2, -1, 0, 1, 2}} with operators {+, -, *, /} and
the W1+W8 anti-cancellation filter, find a phi-native expression E such that:

1. sympy.simplify(E) == 3 (algebraically equal to 3),
2. The MDL string-length proxy of E is strictly less than 12 (the MDL cost
   of G_phi = \\varphi^2 + \\varphi^{-2}),
3. E is NOT a commutative permutation of G_phi (i.e., E is not
   \\varphi^{-2} + \\varphi^2 with operands swapped).

**Expected outcome if falsified:** G_phi drops below rank 2 in the essential
class; the v2.3 sec.6.3 conclusion ("G_phi is MDL-optimal in the equivalence
class of ~100 commutatively-equivalent forms") is refuted within the stated
grammar.

**How to run:** The enumeration harness is frozen in the reproducibility
capsule (run_v23.py). Any reader with the capsule can re-run the full
40,100-expression sweep and inspect the rank table. If the capsule output
already contains such a form, the conjecture is already falsified; the
maintainers assert it does not.

**Executable:** Yes, by any reader with access to the capsule (currently
LOCAL ONLY pending Pellis approval; will be public upon phi-paper release).

---

## Fpath B: Extend BNF depth to 3 and show G_phi drops below rank 10

**Experiment:** Extend the BNF grammar to depth <= 3 (same atom set, same
operators, same W1+W8 anti-cancellation filter, same MDL proxy). Run the
full enumeration. If G_phi = \\varphi^2 + \\varphi^{-2} achieves rank > 10
in the depth-3 essential class, the v2.3 claim is falsified under the
grammar-extension criterion (Conj 7.6 in the manuscript).

**Expected outcome if falsified:** A depth-3 expression with MDL < 12 and
algebraic value 3, not a commutative permutation of G_phi, is discovered.
This would be a concrete counter-example satisfying both the MDL-cost
condition and the grammar-extension scope.

**Expected outcome if not falsified:** G_phi retains rank <= 10 at depth 3,
providing strong (but not conclusive) support for the conjecture. Upgrade
toward [Verified] would additionally require independent replication
(Grunwald or Hutter target; see status.md).

**Computational cost:** Depth-3 enumeration over the same atom set and
operators is estimated at O(10^6) expressions; feasible on a single machine
in hours. No proprietary tools required.

**Executable:** Yes, immediately, by any reader with Python 3.x and sympy
installed. The enumerator logic is documented in run_v23.py (capsule).

---

## What does NOT falsify the claim

- Demonstrating that \\varphi^{-2} + \\varphi^2 (rank 1) has a smaller MDL
  than G_phi: these two are commutative twins with equal MDL; rank 1 is
  assigned by deterministic left-to-right ordering only.
- Demonstrating that the MDL proxy is a poor information-theoretic measure:
  this is already acknowledged as Conj 7.7 (Rissanen-Grunwald robustness)
  and does not by itself falsify the rank-2/394 result within the proxy.
- Criticising the choice of atom set or grammar without providing a
  concrete counter-example: the claim is explicitly scoped to the stated
  grammar and explicitly labelled [Open conjecture].

---

**End of fpath.md.**
