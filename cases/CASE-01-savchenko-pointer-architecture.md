# CASE-01: Mikhail Savchenko -- Pointer Architecture v9.0

**Subject:** Mikhail Savchenko (publishing as @mikefluff).
**Affiliation:** CEO/Founder, INITE (inite.ai). Researcher at
neuralcosmology.com.
**Programme:** Pointer Architecture v9.0 (consciousness-as-substrate
framework, with a SPARC galaxy rotation-curve fit as the main empirical
testbed). Reference implementation in the Sixth language.
**Audit date:** 2026-06-02
**Maintainer:** @gHashTag
**Status:** draft
**Last update:** 2026-06-02

> **Note.** The lab maintainer received a 32-point critical audit from
> Savchenko on 2026-05-10 of the maintainer's own work. This CASE file
> applies the same five-label framework to Savchenko's own published
> programme. The case is opened in good faith, with full source attribution,
> and includes a right-of-reply section per CHARTER.md s 3.

---

## 1. Identity

Savchenko is the author of two GitHub-hosted scientific projects (in
addition to many forks of blockchain / Web3 tooling unrelated to this
case):

- `mikefluff/pointer-architecture` -- Python pipeline fitting a
  log-enhanced-NFW dark matter halo profile ("Pointer", k=6) plus
  comparisons to NFW (k=4) and Burkert (k=4) on 175 SPARC galaxies.
  Published April 2026.
- `mikefluff/sixth` -- a Forth-like concatenative language (49 object-level
  primitives + 33 meta-level), the "reference implementation for the
  Pointer Architecture v9.0 preprint". Published April-May 2026, with an
  explicit three-tier claim taxonomy added 2026-05-20.

The associated public reading is at https://neuralcosmology.com/en .

Primary references for this case (all URLs fetched on 2026-06-02):

- https://github.com/mikefluff/pointer-architecture -- SPARC pipeline.
- https://github.com/mikefluff/sixth -- Sixth substrate language.
- https://github.com/mikefluff/sixth/blob/HEAD/CLAIMS.md -- three-tier
  taxonomy.
- https://github.com/mikefluff/sixth/blob/HEAD/METHODOLOGY.md -- nine
  methodology rules including pre-registration.
- https://github.com/mikefluff/sixth/blob/HEAD/RESULTS.md -- negative
  results and retraction accounting.
- https://github.com/mikefluff/pointer-architecture/blob/HEAD/final_report.md
  -- headline chi^2/AIC/BIC table.
- https://github.com/mikefluff/pointer-architecture/blob/HEAD/phase3_report.md
  -- constrained k=4 Pointer vs NFW vs Burkert.
- https://neuralcosmology.com/en/essays/falsifiers-in-research-and-regulated-ai
  -- subject's essay on falsifiers (2026-05-19).
- https://neuralcosmology.com/en/science/pointer-architecture -- preprint
  page with stated falsifiers.

---

## 2. Programme claims (verbatim)

The central claims, in the subject's own words:

> "External-reviewer feedback (2026-05-20) flagged that the Sixth project
> risks conflating three very different epistemic categories: proved-by-
> running-the-code, demonstrated-by-construction, and philosophical
> conjecture under empirical falsifier. This document is the explicit
> three-tier map."
> -- `mikefluff/sixth/CLAIMS.md`, 2026-05-20.

> "The programme is scientific in the strict sense: every claim comes with
> a falsifier."
> -- https://neuralcosmology.com/en/science/pointer-architecture .

> "Comparisons are at parity rather than stacked, because Pointer
> Architecture fits the three models at matched parameter count."
> -- same source.

> "The interpretation that 'this is what cosmogenesis looks like' is a
> philosophical reading. The construction is reproducible regardless of the
> reading."
> -- `mikefluff/sixth/LANGUAGE.md`.

> "A falsifier that nobody can act on is decorative."
> -- "From SPARC to PII -- falsifiers in research and in regulated AI",
> 2026-05-19, https://neuralcosmology.com/en/essays/falsifiers-in-research-and-regulated-ai .

> "The cheapest moment to specify a falsifier is before you have the result
> you want. By the time you have the result, the result starts to lobby for
> itself."
> -- same essay.

> "The most important sentence in any technical document is the one that
> says 'and here is how this would be wrong.'"
> -- same essay.

---

## 3. Tier mapping

Savchenko uses an explicit three-tier taxonomy in `sixth/CLAIMS.md`:

| Subject's label (Savchenko) | Our label |
|-----------------------------|-----------|
| Tier 1 (proved-by-running-the-code) | [Verified] for the harness only |
| Tier 2 (demonstrated-by-construction) | [Empirical fit] on synthetic / fit data |
| Tier 3 (philosophical conjecture under empirical falsifier with Fpath) | [Open conjecture] with stated Fpath |

The mapping is clean. The subject's discipline of separating Tier 1 from
Tier 3 is the same move our framework requires; the labels are different
in name, identical in function.

---

## 4. [Verified] inventory

Claims from the subject's work that survive [Verified] under our framework:

- **[Verified]** The 82-primitive Sixth language exists (49 object-level +
  33 meta-level). Source:
  https://github.com/mikefluff/sixth/blob/HEAD/CLAIMS.md . Evidence:
  primitive counts checkable by grep over `sixth/primitives/*.rkt` and
  `sixth/meta/*.rkt`.

- **[Verified]** 142 demonstrations pass deterministically with `pass=2070
  fail=0`. The `make verify` target runs `raco test tests/examples-test.rkt`
  and exits non-zero on failure. Source: README.md, same repo. Evidence:
  reproducible harness with frozen test list.

- **[Verified]** Phi_PA stdlib word computes the value defined by Definition
  def:phi-pa. Demo 43 asserts Phi_PA on three canonical observers and the
  values are exactly 0 / 50000 / 130000. Source: CLAIMS.md Tier-1 item 3.
  Evidence: deterministic computation; the harness asserts the integers.
  **This is [Verified] as a computation. It is NOT [Verified] as a
  consciousness measurement.** See [Open conjecture] inventory below.

- **[Verified]** Pilot C (demo 41) constructs a 13-node 48-edge substrate
  from one MARK at t=0. The demo runs and outputs those counts under the
  regression gate. Source: README.md.

- **[Verified]** The honest negative: L2 (substrate-discovered primitives)
  = 0. `ls stdlib/promoted/` does not exist; `grep -rn 'cand_[0-9]'
  stdlib/` returns zero matches; `attestations/ledger.txt` shows zero
  promote-stable events for any cand_NNN. Source: CLAIMS.md CLAIM-3.
  Evidence: the subject's own check command. This is one of the cleanest
  [Verified] claims in the programme and is honestly recorded as a
  negative.

- **[Verified]** RESULTS.md Track 2.1 negative finding: Phi_PA is exactly
  linear in scope, no phase transition, no critical exponent. RESULTS.md
  Track 1.3: HEDGE3 provides no complexity-class separation over binary
  encoding. Source:
  https://github.com/mikefluff/sixth/blob/HEAD/RESULTS.md . Evidence:
  demos 105 and 106. The subject records these negative results first,
  without defensive hedging.

- **[Verified]** Methodology discipline. METHODOLOGY.md Rule 1 requires a
  PREDICTIONS-N.md file with theoretical basis, H0/H1, and falsification
  rules committed BEFORE the demo source, with git timestamps as evidence
  of chronology. Source:
  https://github.com/mikefluff/sixth/blob/HEAD/METHODOLOGY.md . Evidence:
  the file exists, the timestamps are public, the rule is testable.

---

## 5. [Empirical fit] inventory

- **[Empirical fit]** Pointer halo model fits 171 SPARC galaxies with
  k=6 free parameters per galaxy (Y_disk, Y_bul, log_rho0, log_r_mem,
  alpha, log_r_core). Headline numbers from `final_report.md`:

  | Model    | median chi^2 | frac chi^2<3 | median AIC | AIC best |
  |----------|--------------|--------------|------------|----------|
  | pointer (k=6)  | 0.801 | 81%   | 18.20 | 13/171  |
  | nfw (k=4)      | 1.167 | 77%   | 21.60 | 55/171  |
  | burkert (k=4)  | 0.598 | 87%   | 14.19 | 103/171 |

  Source: https://github.com/mikefluff/pointer-architecture/blob/HEAD/final_report.md .
  Free parameters: k=6 (Pointer) vs k=4 (NFW, Burkert). Control: NFW and
  Burkert are present. Pre-registered held-out test: PENDING (THINGS /
  LITTLE THINGS replication explicitly stated by subject as the decisive
  experiment, not yet executed).

- **[Empirical fit]** Constrained Pointer at k=4 (Phase 3, tying alpha to
  log(N_orbits) and r_core to R_disk via population relations derived from
  a subset of the same dataset): median chi^2 = 0.621, median AIC = 14.891.
  AIC best at k=4: Pointer=60, NFW=54, Burkert=57. Source:
  https://github.com/mikefluff/pointer-architecture/blob/HEAD/phase3_report.md .
  At matched k, the three models are statistically indistinguishable on
  AIC. The subject states this self-critically: "pointer wins AIC on 13/171
  with k=6. The constrained variant matches Burkert and NFW in parameter
  count."

- **[Empirical fit]** PHI_PA discriminates the three canonical observers
  (0 / 50000 / 130000) in demo 43. The observers were constructed
  specifically to exhibit the predicted discrimination; this is an
  [Empirical fit] on synthetic data, by construction.

---

## 6. [Open conjecture] inventory

- **[Open conjecture]** Pointer halos encode a cumulative memory of disk
  orbital history (the central physical hypothesis). **Fpath (stated by
  subject):** "If the rho sign flips on an independent age-controlled
  resample from LITTLE THINGS or THINGS, the result is noise." (Source:
  preprint page.) Executable: dataset exists; replication not yet run.

- **[Open conjecture]** Phi_PA measures consciousness. **Fpath (stated by
  subject):** CLAIMS.md Tier 3.1: "Falsified if F5 fires (no substrate-
  encoding map yields the predicted direction on P1-P5 after companion-
  preprint work)." Executable: requires the companion preprints (real
  Pythia computation for PSH2, real EEG analysis for PSH3/PSH4, myrmecology
  collaboration for PSH5). None of the companion experiments are yet
  executed.

- **[Open conjecture]** "Substrate-internally-driven cosmogenesis" (Pilot D
  interpretation). **Fpath (stated by subject):** CLAIMS.md Tier 3.3:
  "promotion to formal isomorphism is forward trigger F2" -- the
  quantum-gravity / holographic-dark-energy mapping. Subject's own framing
  is precise: "This is a structural correspondence, not a derivation."
  Executable: F2 is described as future work.

- **[Open conjecture]** Substrate-monist identity thesis: "Phenomenal
  consciousness IS the substrate-state of a node with Phi_PA > 0." Fpath:
  F5. Executable: same as Phi_PA-as-consciousness above.

---

## 7. [Risk] / [High-risk] inventory

- **[Risk]** CV asymmetry. From `analysis.py` lines 524-527: "CV only for
  pointer (the one with most params -> highest overfit risk). Skipping CV
  for NFW/Burkert saves ~60% of total runtime." The 3-fold CV is run only
  for Pointer; test/train chi^2 ratio = 3.01 (overfitting signal) is
  honestly reported, but a SYMMETRIC overfitting comparison against NFW and
  Burkert is impossible from the released code. Reason: FRAMEWORK.md s
  [Risk] criterion (b) -- look-elsewhere / matched-control missing -- and
  (c) -- a plausible control matches: Burkert (k=4) wins AIC on 103/171 at
  unmatched k. Source: https://github.com/mikefluff/pointer-architecture/blob/HEAD/analysis.py .

- **[Risk]** Composite age proxy (the 6-proxy PC1 used in Phase 2) is
  constructed post-hoc from the same SPARC data used to fit the models.
  The word "pre-registered" does not appear in the pointer-architecture
  repo; there is no PREDICTIONS-N.md equivalent. The strongest individual
  signal (`log_N_orbits`, r=+0.432, p_perm<0.001) shares variables with
  `r_mem/Rdisk` (both derive from `Rdisk` via `_bounds_for_model`), a
  shared-variable risk not fully addressed by permutation testing. Reason:
  FRAMEWORK.md s [Risk] (b). Subject acknowledges this in
  `phase2_report.md`: "A pre-registered replication on THINGS / LITTLE
  THINGS with the frozen mass-free composite and r_ratio-only test remains
  the decisive experiment."

- **[Risk]** Look-elsewhere on Pilot D cosmogenesis. The question "how many
  other stack VMs (Spencer-Brown calculus of distinctions, any Forth-like
  with a pair of generators) would produce a structurally similar growing
  graph from a similar initial condition?" is not addressed in the released
  code. Reason: FRAMEWORK.md s [Risk] (b).

---

## 8. [Retracted] inventory

- **[Retracted]** Four prior internal claims across cycles 1-8 (including a
  self-retraction in cycle 7) are recorded in
  https://github.com/mikefluff/sixth/blob/HEAD/RESULTS.md . The lab does
  not list them here individually; the existence of explicit retraction
  accounting is itself a positive datum and is credited as such. The
  retracted claims do not re-circulate.

---

## 9. Symmetric mirror (MANDATORY)

| Subject's claim | Our comparable claim | Both labelled |
|-----------------|----------------------|---------------|
| `make verify` runs `pass=2070 fail=0`; CLAIMS.md three-tier taxonomy (2026-05-20) | GoldenFloat ladder arithmetic 9/9; `goldenfloat-ladder` skill five-label framework | both [Verified] for harness/arithmetic only |
| Pointer (k=6) vs Burkert (k=4) at unmatched k; Burkert dominates AIC win-rate 103/13 | IGLA RACE v2 BPB-per-format table circulated as comparison, sources not pre-registered | both [Empirical fit] / [Risk] until matched-control pre-registered held-out run |
| THINGS / LITTLE THINGS replication is the decisive experiment, not yet run | Phase B1-real four-arm matched-cardinality phi-vs-non-phi ablation, blocked on compute | both [Open conjecture] with executable Fpath, both compute-pending |
| Phi_PA as a consciousness discriminator on toy substrates | phi as architecture prior with phi-anchored hyperparameters | both [Open conjecture] with stated Fpath; harness-only [Verified] for the computation |
| Pilot D cosmogenesis interpretation -- no look-elsewhere over alternative stack VMs | "phi is special for the constants" -- our own control-grammar test demoted to [Retracted]/[High-risk] | both [Risk] for look-elsewhere; we have demoted, subject has stated but not executed F2 |

Both programmes are in the **pre-falsification regime**: each has the
decisive replication / matched-control experiment identified, neither has
executed it. The productive joint move is a cross-repo falsification
ledger: agree on what counts as a PASS / FAIL / PARTIAL for each side's
decisive experiment, and run both within a shared 9-month window.

---

## 10. Audit summary

Strongest part of Pointer Architecture / Sixth: the three-tier taxonomy in
`CLAIMS.md`, the `make verify` reproducibility harness, the honest negative
results in `RESULTS.md` (Phi_PA exactly linear, HEDGE3 no separation,
L2=0), and the pre-registration discipline in `METHODOLOGY.md`. These are
genuine [Verified] / [Open conjecture] practices and they are recorded
first.

Weakest claim: the [Risk] cluster on the SPARC fit -- Burkert (k=4)
dominates Pointer (k=6) at unmatched k, NFW/Burkert CV is not run, and the
composite age proxy is post-hoc. The subject's own Phase 3 (constrained
k=4) shows AIC indistinguishability across all three models. This is
[Empirical fit] with [Risk] on the matched-control comparison, not a
demonstration that Pointer is the best halo model.

Single experiment that would resolve the largest claim: pre-registered
THINGS / LITTLE THINGS replication with frozen mass-free composite and
r_ratio-only test, as the subject himself names in `phase2_report.md`.

Symmetric position of the lab: our own analogous experiment (Phase B1-real
champion-scale phi-vs-non-phi ablation) is in the same state -- specified,
falsifier explicit, compute-pending.

---

## 11. Sources

- 2026-06-02: https://github.com/mikefluff/pointer-architecture/blob/HEAD/README.md
- 2026-06-02: https://github.com/mikefluff/pointer-architecture/blob/HEAD/analysis.py
- 2026-06-02: https://github.com/mikefluff/pointer-architecture/blob/HEAD/final_report.md
- 2026-06-02: https://github.com/mikefluff/pointer-architecture/blob/HEAD/phase2_report.md
- 2026-06-02: https://github.com/mikefluff/pointer-architecture/blob/HEAD/phase3_report.md
- 2026-06-02: https://github.com/mikefluff/pointer-architecture/blob/HEAD/phase4_report.md
- 2026-06-02: https://github.com/mikefluff/sixth/blob/HEAD/CLAIMS.md
- 2026-06-02: https://github.com/mikefluff/sixth/blob/HEAD/METHODOLOGY.md
- 2026-06-02: https://github.com/mikefluff/sixth/blob/HEAD/RESULTS.md
- 2026-06-02: https://github.com/mikefluff/sixth/blob/HEAD/LANGUAGE.md
- 2026-06-02: https://github.com/mikefluff/sixth/blob/HEAD/SUBSTRATE.md
- 2026-06-02: https://neuralcosmology.com/en/essays/falsifiers-in-research-and-regulated-ai
- 2026-06-02: https://neuralcosmology.com/en/science/pointer-architecture

Lab-internal cross-reference (not for redistribution):
- The full symmetric audit (665 lines) sits in the maintainer's working
  notes at `savchenko_response/pointer_architecture_symmetric_audit.md`.
  This CASE-01 is the public extract.

---

## 12. Subject's reply

Empty. The subject has not been notified of this CASE file as of
2026-06-02. Per CHARTER.md s 3, a reply submitted at any time will be
included verbatim with a source link.

---

**End of CASE-01.**
