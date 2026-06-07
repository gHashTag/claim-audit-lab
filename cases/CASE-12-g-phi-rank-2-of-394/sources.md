# CASE-12: Sources

All sources are listed in chronological order. Fetch dates are recorded
where a URL was directly accessed; for LOCAL ONLY sources the access date
is the date of the local working-copy review.

---

## Primary manuscript sources (LOCAL ONLY, Pellis-gated)

- 2026-06-07 (local review): gHashTag/phi-paper v2.3-draft,
  pellis_vasilev_letter.tex sec.6.3 -- "Equivalence-class analysis and
  MDL-canonical Lucas form (v2.3)": defines the 40,100-expression BNF
  enumeration and the rank-2/394 result.

- 2026-06-07 (local review): gHashTag/phi-paper v2.3-draft,
  pellis_vasilev_letter.tex sec.6.4 -- "Anti-cancellation filter and
  essential-class definition": defines the W1+W8 filter reducing 497
  phi-native forms to 394 essential forms.

- 2026-06-07 (local review): gHashTag/phi-paper v2.3-draft,
  pellis_vasilev_letter.tex Conj 7.6 -- "Grammar-extension robustness
  conjecture": states that the rank-2/394 result may not survive extension
  to depth > 2 or larger atom sets. Falsification path: Fpath B (see
  fpath.md).

- 2026-06-07 (local review): gHashTag/phi-paper v2.3-draft,
  pellis_vasilev_letter.tex Conj 7.7 -- "Rissanen-Grunwald MDL robustness
  conjecture": states that replacement of the string-length proxy by a
  proper two-part MDL code may shift G_phi rank above 10.

---

## Reproducibility capsule (LOCAL ONLY, Pellis-gated)

- 2026-06-07 (local review): phi-paper/reproducibility/v23/run_v23.py --
  main enumerator and W1+W8 filter driver; generates all numerical results
  in CASE-12.

- 2026-06-07 (local review): phi-paper/reproducibility/v23/results_v23.json --
  full enumeration output: 501 expressions equal to 3, 497 phi-native,
  394 essential, rank table.

- 2026-06-07 (local review): phi-paper/reproducibility/v23/README --
  capsule documentation and reproduction instructions.

- 2026-06-07 (local review): phi-paper/reproducibility/v23/changes --
  diff from v2.2 capsule to v2.3 capsule documenting the addition of the
  W1+W8 anti-cancellation filter.

---

## Correspondence

- 2026-06-07: Pellis Letter v2 SENT -- formal request to Stergios Pellis
  for approval to publish the v2.3 draft and the CASE-12 audit results.
  Hard gating: no public release until written approval received.

---

## Predecessor case

- gHashTag/claim-audit-lab, cases/CASE-08-vasilev-bnf-equivalence-class.md
  -- predecessor audit recording raw rank 2/1000 without the anti-cancel
  filter. CASE-12 refines but does not supersede CASE-08.
  URL: https://github.com/gHashTag/claim-audit-lab/blob/main/cases/CASE-08-vasilev-bnf-equivalence-class.md

---

## External references (publicly accessible)

- arXiv:2511.05849 (Jiang 2026, ICLR) -- EGG-SR formal e-graph for
  equivalence-class detection; relevant to Risk R-v23-C-1 (sympy.simplify
  vs. e-graph cardinality). URL: https://arxiv.org/abs/2511.05849

NOTE: arXiv ID 2606.05017 is the GoldenFloat preprint; it is NOT the
phi-paper and must not be cited as a source for CASE-12 results.
The phi-paper has no arXiv ID at this time.

---

**End of sources.md.**
