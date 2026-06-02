# CASE-04: Sergey V. Petoukhov -- Matrix Genetics / Golden Section in the Genetic Code

**Subject:** Sergey V. Petoukhov
**Affiliation:** Mechanical Engineering Research Institute, Russian Academy of Sciences,
Moscow (Laboratory of Biomechanical Systems). Active through at least 2024.
**Programme:** Matrix Genetics -- the claim that the golden section (phi) is mathematically
encoded in the universal genetic code and constitutes a biological universal.
**Audit date:** 2026-06-10
**Maintainer:** @gHashTag
**Status:** draft
**Last update:** 2026-06-10

---

## 1. Identity

Petoukhov is a researcher at the Mechanical Engineering Research Institute of the Russian
Academy of Sciences, where he heads the Laboratory of Biomechanical Systems and has worked
since 1973. He has authored seven books and more than 200 papers on biomechanics, matrix
genetics, and algebraic biology. Source: [petoukhov.com](http://petoukhov.com).

The matrix genetics programme constructs a family of 2^n x 2^n matrices by Kronecker-
powering a 2x2 matrix derived from the hydrogen-bond counts of complementary nucleotide
pairs: cytosine-guanine (C=G, 3 bonds) and adenine-uracil (A=U, 2 bonds). Replacing letters
with their hydrogen-bond numbers gives the base matrix PMULT(1) = [3,2;2,3]. Kronecker-
powering this matrix to the third power produces an 8x8 matrix whose 64 cells represent the
64 genetic triplets. Petoukhov's central mathematical observation is that the matrix square root
of PMULT(1) -- and by extension of all Kronecker powers PMULT(n) -- is a matrix whose entries
are integer powers of phi (the golden section, phi = (1+sqrt(5))/2 = 1.618...). The programme
then claims this algebraic link is evidence that phi is encoded in the universal genetic code as
a biological universal governing self-reproduction.

Primary references for this case (all URLs fetched on 2026-06-10):

- http://petoukhov.com/GENETIC_BINARY_SUBALPHABETS_AND_GOLDEN_SECTION_2001_PETOUKHOV.pdf
  -- Petoukhov (2001), "Genetic Codes I: Binary Sub-Alphabets, Bi-Symmetric Matrices and the
  Golden Section." Earliest statement of the matrix identity and its biological reading.
- https://arxiv.org/abs/0803.0888 -- Petoukhov (2008), "Matrix Genetics, Part 1," arXiv
  preprint. Kronecker-power structure of genetic matrices.
- http://petoukhov.com/wp-content/uploads/2011/05/sciforum-003889-from-PETOUKHOV-.pdf
  -- Petoukhov (2011), "The Genetic Code, the Golden Section and Genetic Music." Conference
  proceedings; contains the explicit verbatim universality claim.
- https://pubmed.ncbi.nlm.nih.gov/37690530/ -- Petoukhov (2023), "The principle 'like begets
  like' in algebra-matrix genetics and code biology," Biosystems 233, 105019 (Elsevier).
- https://dergipark.org.tr/en/pub/cma/article/1539666 -- He & Petoukhov (2024), "Hadamard
  matrices of genetic code and trigonometric functions," Constructive Mathematical Analysis
  7 (Special Issue), 27-36. Scopus- and ESCI-indexed; JIF 1.8, Q1 Mathematics.
- http://petoukhov.com -- Author homepage, affiliation, and publication overview.
- https://pmc.ncbi.nlm.nih.gov/articles/PMC6047800/ -- Liu & Sumpter (2018), "Is the golden
  ratio a universal constant for self-replication?", PLoS ONE 13(7): e0200601. Relevant
  independent critique of phi universality in self-replicating systems.

---

## 2. Programme claims (verbatim)

> "The author has given a principal new definition to a golden section on the basis of the
> matrix specifics of genetic code systems: a golden section phi and its inverse value phi^-1
> are single matrix elements of the bi-symmetric matrix Phi, which is the square root from a
> bi-symmetric matrix PMULT (2x2) with its numeric matrix elements from a set of numbers of
> complementary hydrogen bonds in genetic nitrogenous bases: C=G=3, A=U=2."
> -- Petoukhov (2001), petoukhov.com/GENETIC_BINARY_SUBALPHABETS_AND_GOLDEN_SECTION_2001_PETOUKHOV.pdf

> "If we take the square root from any genomatrix [3,2;2,3](n), the result is a new matrix
> ([3,2;2,3](n))^{1/2} = [phi, phi^{-1}; phi^{-1}, phi](n), all elements of which are equal
> to the golden section phi in different powers."
> -- Petoukhov (2011), petoukhov.com/wp-content/uploads/2011/05/sciforum-003889-from-PETOUKHOV-.pdf

> "The family of the golden genetic matrices ([3,2;2,3](n))^{1/2} = [phi, phi^{-1};
> phi^{-1}, phi](n) ... testifies additionally that the golden section is a mathematical symbol
> of a self-reproduction for many centuries."
> -- Petoukhov (2011), same source

> "The golden section is shown by many authors in genetically inherited physiological systems:
> cardio-vascular system, respiratory system, electric activities of brain, etc."
> -- Petoukhov (2011), same source

> "molecular genetics revealed a principal unity of all biological organisms from the viewpoint
> of basic structures of their genetic code."
> -- Petoukhov (2001), same source as first quote above

> "The new theme of golden section in genetic matrices seems to be very important because
> many physiological systems and processes are connected with it."
> -- Petoukhov (2001), same source

---

## 3. Tier mapping

Petoukhov does not use an explicit epistemic taxonomy comparable to CLAIMS.md-style
three-tier systems. Claims are presented as mathematical derivations or as observed
correspondences in the biological literature, without explicit labels distinguishing
"proved by construction" from "conjectured to hold universally." The framework below
is applied by this lab using the most permissive reading consistent with Petoukhov's
strongest published wording.

| Programme level | Our label |
|-----------------|-----------|
| sqrt([3,2;2,3]) = [phi, phi^-1; phi^-1, phi] (algebraic fact) | [Verified] |
| Kronecker-power extension: sqrt([3,2;2,3]^n) = [phi,phi^-1;phi^-1,phi]^n | [Verified] |
| The 2024 CMA paper's trigonometric-triplet pattern mirrors the genetic code | [Empirical fit] |
| Phi is encoded in the universal genetic code | [Open conjecture] if an Fpath is found; [Risk] if not |
| Phi governs inherited physiological systems as a biological universal | [Risk] |

---

## 4. [Verified] inventory

- **[Verified]** The algebraic identity sqrt([3,2;2,3]) = [phi, phi^{-1}; phi^{-1}, phi]
  (in the normalisation where the matrix square root is taken entry-wise via the
  eigendecomposition of the symmetric 2x2 matrix with eigenvalues 5 and 1, and
  eigenvectors aligned with the golden mean) is exact. Derivation: the eigenvalues of
  [3,2;2,3] are 5 and 1 with eigenvectors (1,1)/sqrt(2) and (1,-1)/sqrt(2);
  the square root has eigenvalues sqrt(5) and 1; transforming back yields entries
  (sqrt(5)+1)/2 = phi and (sqrt(5)-1)/2 = phi^{-1}. This is algebraic arithmetic
  with no free parameters. Source:
  [Petoukhov (2001), petoukhov.com PDF](http://petoukhov.com/GENETIC_BINARY_SUBALPHABETS_AND_GOLDEN_SECTION_2001_PETOUKHOV.pdf).
  Evidence: re-derivable in four lines from definitions; verified numerically.

- **[Verified]** The Kronecker-power extension: because the Kronecker product distributes
  over matrix square roots for symmetric positive-definite matrices, the identity
  sqrt([3,2;2,3]^{(x)n}) = [phi,phi^{-1};phi^{-1},phi]^{(x)n} holds for all positive
  integers n, where (x) denotes the Kronecker product. The resulting 2^n x 2^n matrix
  entries are all integer powers of phi (specifically phi^k for k ranging over a symmetric
  set of integers determined by n). Source: [Petoukhov (2011)](http://petoukhov.com/wp-content/uploads/2011/05/sciforum-003889-from-PETOUKHOV-.pdf),
  confirmed by standard Kronecker-product algebra.
  Evidence: algebraic identity, no free parameters.

- **[Verified]** The 2024 He-Petoukhov paper in Constructive Mathematical Analysis is a
  genuine peer-reviewed publication. The journal is Scopus-indexed, included in Web of
  Science Emerging Sources Citation Index (ESCI), carries a 2025 JIF of 1.8 at Q1
  Mathematics. Source: [ISSN portal 2651-2939](https://portal.issn.org/resource/ISSN/2651-2939);
  [journal indexing record, ojop.org](https://www.ojop.org/constructive-mathematical-analysis/).
  This is [Verified] for the venue; the biological claims in that paper are separately
  classified below.

---

## 5. [Empirical fit] inventory

- **[Empirical fit]** He & Petoukhov (2024) show that when 64 trigonometric triplets
  (formed from the four basic functions sin, tan, cos, cot) are examined under the same
  Kronecker-product algebra as the 64 genetic triplets, they produce a 20-element
  equivalence class that mirrors the 20 canonical amino acids. Source:
  [He & Petoukhov (2024), Constructive Mathematical Analysis](https://dergipark.org.tr/en/pub/cma/article/1539666).
  Free parameters: choice of which four trigonometric functions to use (post-hoc; the
  four chosen are the ones that produce the desired 20-class degeneracy), choice of
  degeneracy rule, choice of Kronecker product structure. Pre-registered held-out test:
  not stated. Control: no comparison is provided showing how many other 4-function sets
  from the trigonometric family would produce a different or identical count.
  This is a genuine mathematical parallel with evocative structure; it qualifies as
  [Empirical fit] on the pattern, not [Verified] for the biological universality claim.

- **[Empirical fit]** Petoukhov (2023) in Biosystems reports that binary sequences of
  hydrogen bonds in genomic single-stranded DNAs exhibit fractal-like probability
  dichotomies across multiple organisms (eukaryotes and prokaryotes), and that the
  probability matrices are representations of 2^n-dimensional hyperbolic numbers.
  Source: [Petoukhov (2023), Biosystems 233, 105019](https://pubmed.ncbi.nlm.nih.gov/37690530/).
  Free parameters: the HBS-method (hierarchy binary stochastics) is the author's own
  method developed specifically for this data; choice of genomic DNAs included; author
  notes he "selectively checked" higher-n equalities but did not check at which n the
  dichotomies cease to hold. Pre-registered held-out test: absent. This is a real
  pattern reported in peer-reviewed form (Elsevier Biosystems); the free-parameter count
  is moderate and the pattern itself is reproducible from public genomic databases.

---

## 6. [Open conjecture] inventory

- **[Open conjecture -- Fpath not located; see Section 7]**
  Phi is encoded in the universal genetic code and is a mathematical symbol of
  self-reproduction for all biological organisms. Source: Petoukhov (2011),
  [petoukhov.com 2011 PDF](http://petoukhov.com/wp-content/uploads/2011/05/sciforum-003889-from-PETOUKHOV-.pdf).
  This lab searched Petoukhov (2001, 2008, 2011, 2023) and He & Petoukhov (2024) for a
  stated falsification path. None was located. Under FRAMEWORK.md, the absence of an
  Fpath moves this from [Open conjecture] to [Risk] (a) (see Section 7). A natural Fpath
  would be: "the phi-matrix identity fails to emerge if a different two-number encoding of
  complementary base pairs is used (e.g., bond strength in kJ/mol instead of integer bond
  count)." If evidence of a stated Fpath from a source not reviewed here is submitted,
  this entry will be promoted to [Open conjecture].

---

## 7. [Risk] / [High-risk] inventory

- **[Risk] (a)** The claim "phi is encoded in the universal genetic code as a biological
  universal" has no stated falsification path in the published sources reviewed.
  Source: Petoukhov (2001, 2011), petoukhov.com PDFs; Petoukhov (2023), Biosystems.
  Reason: FRAMEWORK.md [Risk] criterion (a) -- no Fpath stated. The claim aspires to
  conjecture status but without a one-sentence falsifier it defaults to [Risk].

- **[Risk] (b)** Look-elsewhere correction is absent. The hydrogen-bond count matrix
  [3,2;2,3] is one of infinitely many symmetric 2x2 matrices of positive integers that
  could have been chosen to represent the genetic code. Any matrix of the form [a,b;b,a]
  with a > b > 0 has a square root of the form [(r+s)/2, (r-s)/2; (r-s)/2, (r+s)/2]
  where r = sqrt(a+b) and s = sqrt(a-b). The specific appearance of phi arises because
  the chosen entries 3 and 2 satisfy a+b=5 and a-b=1, giving sqrt(5) and 1, which yield
  phi = (sqrt(5)+1)/2. The matrix [5,3;3,5] (using pentagonal symmetry), [4,1;1,4]
  (using a different bond count convention), or [2,1;1,2] (using {2,1} as the bond count
  pair for G:C and A:T) would produce matrix square roots whose entries are NOT powers of
  phi in the same pattern. The choice of the {3,2} pair is justified biochemically
  (C=G=3 hydrogen bonds, A=U=2) but the coincidence that this pair produces phi -- and
  not some other irrational -- is not shown to survive look-elsewhere correction over the
  space of plausible biochemical encodings. Source for the general class of algebraic
  coincidences: Liu & Sumpter (2018),
  [PLoS ONE 13(7): e0200601](https://pmc.ncbi.nlm.nih.gov/articles/PMC6047800/), who
  show that phi and other algebraic numbers arise frequently in self-replicating systems
  under idealised conditions and conclude that "when the golden ratio ... characterises
  chemical ratios in a system, the most likely explanation is chance."
  Reason: FRAMEWORK.md [Risk] criterion (b).

- **[Risk] (b) + (c)** Free-parameter cluster: the programme requires three simultaneous
  choices not derived from first principles: (1) representation of bases by
  hydrogen-bond INTEGER count rather than bond energy or electronegativity; (2) the
  Kronecker product as the generating algebraic operation; (3) the matrix square root as
  the specific operation applied (rather than matrix log, inverse, or any other power).
  Each choice is individually defensible; their joint selection is not constrained by a
  prior theory independent of the phi-appearance. A non-phi control -- any plausible
  variation of these three choices -- has not been shown to fail to produce an equally
  structured algebraic relationship. Reason: FRAMEWORK.md [Risk] (b) and (c).

- **[Risk] (a)** The extension to claims about physiological systems (cardio-vascular
  rhythms, respiratory rates, brain electrical activity) relies on secondary citations
  gathered post-hoc. Source: Petoukhov (2011), petoukhov.com 2011 PDF. No prediction
  about a specific physiological measurement is derived from the genetic matrix, tested
  on new data, and confirmed. The causal chain from "the matrix square root of PMULT is
  phi-valued" to "therefore cardiac rhythms exhibit phi ratios" is asserted by
  accumulation of separate correlations, not by a mechanistic derivation. No Fpath for
  this step is stated. Reason: FRAMEWORK.md [Risk] (a).

---

## 8. [Retracted] inventory

No retraction by the subject or by any journal in connection with this programme has
been located as of 2026-06-10.

---

## 9. Symmetric mirror (MANDATORY)

| Subject's claim | Our comparable claim | Both labelled |
|-----------------|----------------------|---------------|
| sqrt([3,2;2,3]) = [phi,phi^{-1};phi^{-1},phi] -- exact algebraic identity | phi^2 + phi^{-2} = L_2 = 3 (Lucas identity, Binet formula corollary) | both [Verified] -- algebraic identities re-derivable in a few lines, no free parameters |
| "phi is encoded in the universal genetic code" -- no Fpath located | "phi as architecture prior in IGLA hyperparameters outperforms matched control" -- Fpath stated (Phase B1-real) | Petoukhov's claim [Risk] (a); our claim [Open conjecture] with stated Fpath -- the same epistemic gap (universal interpretation not yet tested) |
| No look-elsewhere correction over choice of bond-count matrix | BPB-per-format table previously circulated without frozen reproducible source | Petoukhov: [Risk] (b) for missing look-elsewhere; our table: [Risk] and demoted to NEEDS REPRODUCTION on 2026-06-02 |

The symmetric structure here is precise. Both programmes contain an exact algebraic
identity at their core (the genetic phi-matrix; the Lucas L_2 = 3 identity underlying
GF16). Both then make a leap from "phi appears in this specific algebraic construction"
to "phi is special in the broader domain" -- Petoukhov toward the genetic code as a
biological universal, the lab toward phi-anchored hyperparameters as architecture prior.
The lab's leap carries a stated Fpath (Phase B1-real, four-arm matched-cardinality
ablation, compute-pending, recorded in CASE-00 s 6). Petoukhov's leap does not carry
a located Fpath in published sources. This is the structural asymmetry: not a difference
in the underlying algebraic observations, which are comparable in quality and both
[Verified], but in the disciplinary accounting of how far the programme extends from
those identities into universal claims.

A single experimental design would stress-test both programmes simultaneously: replace
the {3,2} hydrogen-bond pair in Petoukhov's matrix with {bond-energy in kJ/mol} values
(G:C ~ 21 kJ/mol, A:U ~ 12 kJ/mol, giving a non-integer matrix [21,12;12,21]) and check
whether the square root is still a phi-matrix (it is not, by the general formula above,
since 21+12=33 and sqrt(33) is not a power of phi). Running this control would determine
whether phi's appearance is specific to the integer hydrogen-bond count or a broader
algebraic property of the code's symmetry. Simultaneously, running the lab's Phase B1-real
four-arm ablation would test whether phi-anchored hyperparameters outperform matched
controls. Neither experiment requires the other; both are independent tests of whether
a specific algebraic phi-connection scales to a universal claim.

---

## 10. Audit summary

**(a) Strongest part.** The algebraic core -- sqrt([3,2;2,3]) = [phi,phi^{-1};phi^{-1},phi]
and its Kronecker-power extension -- is [Verified] arithmetic. It is a genuine and
non-obvious observation that the hydrogen-bond count matrix of the genetic alphabet has
a matrix square root expressible entirely in terms of phi. The 2024 He-Petoukhov paper
in Constructive Mathematical Analysis (Scopus, ESCI, Q1, JIF 1.8) is a legitimate
peer-reviewed venue, and the trigonometric-triplet parallel is a genuine [Empirical fit]
meriting independent examination.

**(b) Weakest claim.** The weakest claim is the physiological universality step: that
phi in the genetic matrix explains phi-proportions in cardiac rhythms, respiratory
cycles, and brain electrical activity. This is [Risk] (a) -- no Fpath -- and [Risk] (b)
-- no look-elsewhere correction and no mechanistic derivation linking the matrix identity
to specific physiological measurements.

**(c) Single experiment.** The decisive experiment is a look-elsewhere survey: enumerate
all symmetric 2x2 positive-integer matrices derivable from plausible biochemical
encodings of complementary base pairs (bond count, bond energy, mass, charge) and
determine how many of their matrix square roots are expressible as phi-power matrices.
If only the {3,2} integer-bond-count matrix produces phi (or a very small fraction of
the space does), the identity acquires significance that survives look-elsewhere.
If many matrices in the biochemically plausible space do so, the identity is a property
of the symmetry class rather than of the genetic code specifically.

**(d) Symmetric position of the lab.** The lab's own [Verified] algebraic anchor
(phi^2 + phi^{-2} = 3, the Lucas L_2 identity) is in the same epistemic class as
Petoukhov's matrix identity: exact arithmetic, not in dispute. The lab's leap to
phi-as-architecture-prior is [Open conjecture] with a stated Fpath; Petoukhov's leap
to phi-as-genetic-universal is [Risk] because no Fpath has been located. Both wait on
experiments that have not yet been executed.

---

## 11. Sources

- 2026-06-10: http://petoukhov.com -- Author homepage, affiliation.
- 2026-06-10: http://petoukhov.com/GENETIC_BINARY_SUBALPHABETS_AND_GOLDEN_SECTION_2001_PETOUKHOV.pdf
  -- Petoukhov (2001), "Genetic Codes I."
- 2026-06-10: https://arxiv.org/abs/0803.0888 -- Petoukhov (2008), "Matrix Genetics,
  Part 1," arXiv:0803.0888.
- 2026-06-10: http://petoukhov.com/wp-content/uploads/2011/05/sciforum-003889-from-PETOUKHOV-.pdf
  -- Petoukhov (2011), "The Genetic Code, the Golden Section and Genetic Music."
- 2026-06-10: https://pubmed.ncbi.nlm.nih.gov/37690530/ -- Petoukhov (2023), Biosystems
  233, 105019.
- 2026-06-10: https://dergipark.org.tr/en/pub/cma/article/1539666 -- He & Petoukhov
  (2024), Constructive Mathematical Analysis 7 (Special Issue), 27-36.
- 2026-06-10: https://portal.issn.org/resource/ISSN/2651-2939 -- ISSN record confirming
  Scopus and Web of Science indexing of Constructive Mathematical Analysis.
- 2026-06-10: https://www.ojop.org/constructive-mathematical-analysis/ -- CMA indexing
  summary (TR DIZIN, ESCI, Scopus; JIF 1.8; Q1).
- 2026-06-10: https://pmc.ncbi.nlm.nih.gov/articles/PMC6047800/ -- Liu & Sumpter
  (2018), "Is the golden ratio a universal constant for self-replication?", PLoS ONE
  13(7): e0200601. Critique of phi universality in self-replicating systems.
- 2026-06-10: https://doaj.org/toc/2651-2939 -- DOAJ record for Constructive
  Mathematical Analysis.

Cross-reference: CASE-00 (self-audit) sections 4, 6, 7 for symmetric claims.

---

## 12. Subject's reply

Empty. The subject has not been notified of this CASE file as of 2026-06-10.
Per CHARTER.md s 3, a reply submitted at any time will be included verbatim with a
source link.

---

**End of CASE-04.**
