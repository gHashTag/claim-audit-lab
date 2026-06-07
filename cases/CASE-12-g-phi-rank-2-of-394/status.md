# CASE-12: Status

**Current label:** [Open conjecture] (\\Conj)
**As of:** 2026-06-07
**Predecessor:** CASE-08 (same result, no anti-cancel filter; also \\Conj)

---

## Why [Open conjecture] and not [Verified]

Three structural caveats prevent a [Verified] label, unchanged from CASE-08:

1. **Grammar is bounded.** Depth <= 2 over {\\varphi^k : k in {-2,-1,0,1,2}}
   is a narrow corner of the symbolic-expression space. A grammar extension
   (integer coefficients, depth > 2, radicals, or transcendental atoms) may
   surface a strictly shorter phi-native form reducing to 3. Codified as
   Conj 7.6 in the v2.3 manuscript.

2. **MDL is a string-length proxy.** Not a Rissanen-Grunwald two-part code
   with explicit grammar prior. Replacing the proxy with a real MDL measure
   could shift G_phi rank above 10. Codified as Conj 7.7 in the manuscript.

3. **Equivalence-class detection uses sympy.simplify.** EGG-SR (Jiang 2026,
   arXiv:2511.05849) provides a formal e-graph canonicalizer that may produce
   a different class cardinality. Risk R-v23-C-1 in sec.6.4 of the manuscript.

Additionally, the anti-cancellation filter (W1+W8) that distinguishes CASE-12
from CASE-08 is itself heuristic: "essential-ness" is defined operationally
(expressions surviving the W1+W8 checks) rather than from a formal MDL prior.
This adds a fourth caveat specific to CASE-12.

The strongest honest label is therefore \\Conj at p < 0.01 within the
explicitly specified scope and grammar.

---

## Upgrade path

| Condition                                            | Upgrade to        |
|------------------------------------------------------|-------------------|
| Depth-3 sweep confirms G_phi rank <= 10 (see fpath.md Fpath B) | \\Conj strengthened |
| Independent replication by Grunwald or Hutter target | \\Conj -> \\Verified (conditional) |
| Peer-reviewed replication via ReScience C            | \\Conj -> \\Verified |
| Fpath A executed with no counter-example found       | \\Conj strengthened (within depth-2 scope) |

Upgrade to [Verified] requires at minimum: (a) one of the Grunwald/Hutter
targets closes positively, AND (b) Fpath B (depth-3 sweep) produces no
counter-example. Peer review via ReScience C replication would substitute
for (a).

Downgrade to [Risk] or [Retracted] requires: Fpath A or Fpath B succeeds
(see fpath.md).

---

## Public status

v2.3-draft is LOCAL ONLY. Hard gating: CASE-12 content and the phi-paper
v2.3 draft are not to be published, shared, or cited externally until
Stergios Pellis provides explicit written approval (Pellis Letter v2 sent
2026-06-07). The claim-audit-lab CASE-12 entry is committed to the public
repo as an audit-trail record under the lab's symmetric-audit obligation,
but the underlying manuscript remains private.

---

## Relationship to CASE-08

CASE-08 recorded rank 2/1000 raw (no anti-cancel filter). CASE-12 refines
that to rank 2/394 essential (W1+W8 filter applied). Both cases carry
identical \\Conj labels and identical structural caveats. CASE-08 is not
deprecated by CASE-12; it remains the audit record for the raw-count result.

---

**End of status.md.**
