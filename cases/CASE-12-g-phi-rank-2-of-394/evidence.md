# CASE-12: Evidence

All numerical results are read from SHA-256-pinned JSON files in the
reproducibility capsule at phi-paper/reproducibility/v23/ (LOCAL ONLY).
No human-typed numbers appear in the manuscript LaTeX; all figures are
generated directly from the frozen capsule outputs.

---

## Enumeration parameters

| Parameter            | Value                                             |
|----------------------|---------------------------------------------------|
| Atom set             | {\\varphi^k : k in {-2, -1, 0, 1, 2}}            |
| Binary operators     | {+, -, *, /}                                      |
| Grammar depth        | <= 2                                              |
| Total expressions    | 40,100                                            |
| Equivalence check    | sympy.simplify (equated to integer 3)             |
| Expressions equal 3  | 501                                               |
| Phi-native count     | 497                                               |
| Essential (filtered) | 394                                               |

---

## Anti-cancellation filter (W1+W8)

The anti-cancellation normalization removes expressions that are trivially
redundant under additive or multiplicative cancellation:

- **W1 filter:** removes expressions where a sub-expression cancels to 0
  under the phi-native evaluation (e.g., \\varphi^k - \\varphi^k).
- **W8 filter:** removes expressions where a sub-expression reduces to 1
  under the phi-native evaluation (e.g., \\varphi^k / \\varphi^k).

Applying W1+W8 reduces 497 phi-native expressions to 394 essential forms.
The filter is heuristic: "essential-ness" is not derived from a formal MDL
prior (see status.md for the Conj caveat).

---

## MDL ranking

MDL proxy: string length of the normalized expression in the BNF encoding
(character count of the canonical form output by the enumerator). Lower
MDL = shorter encoding = higher rank (rank 1 = shortest).

| Rank | Expression                              | MDL (proxy) | Notes                             |
|------|-----------------------------------------|-------------|-----------------------------------|
| 1    | \\varphi^{-2} + \\varphi^2              | 12          | Commutative twin of G_phi         |
| 2    | \\varphi^2 + \\varphi^{-2}  (G_phi)    | 12          | MDL-canonical Lucas-symmetric rep |
| ...  | (remaining 392 essential forms)         | >= 12       | Higher MDL or longer encoding     |

Rank 1 and rank 2 share the same MDL cost (string-length proxy = 12).
They are commutative permutations of each other. G_phi is assigned rank 2
by the enumerator's deterministic left-to-right ordering.

---

## Bootstrap significance

| Statistic              | Value              |
|------------------------|--------------------|
| Bootstrap p-value      | 0.0039 (p < 0.01)  |
| Bootstrap resamples B  | 10,000             |
| Empirical p-value      | 0.0051             |
| Null model             | Uniform draw from 394 essential forms |

The bootstrap resamples uniformly from the 394 essential forms; p is the
fraction of resamples in which a randomly drawn form achieves MDL <= 12
(the G_phi string-length proxy value). Both bootstrap and empirical p
are below 0.01, consistent with Conj 7.6 and Conj 7.7 in the manuscript.

---

## Capsule provenance

Reproducibility capsule at phi-paper/reproducibility/v23/ (LOCAL ONLY):

- run_v23.py       -- main enumerator and filter driver
- results_v23.json -- full enumeration output (501 matches, classified)
- README           -- capsule documentation and reproduction instructions
- changes          -- diff from v2.2 capsule to v2.3 capsule

arXiv ID 2606.05017 is the GoldenFloat preprint; it is NOT the phi-paper.
The phi-paper has no arXiv ID at this time (LOCAL ONLY, Pellis-gated).

---

**End of evidence.md.**
