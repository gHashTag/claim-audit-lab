# METHODOLOGY

The philosophical and meta-scientific scaffold behind the five-label
claim-status framework used by this repository.

This file complements `FRAMEWORK.md` (which is the normative spec) and
`CHARTER.md` (which is the binding policy). Where `FRAMEWORK.md` says
*what* the rules are, this file says *why* those particular rules and
not others.

---

## 0. The lab applies the framework to itself

Before anything else: the five-label taxonomy of this repository is itself
an **[Open conjecture]**. Its Fpath is:

> If the criteria fail to predict replication success better than chance
> on a held-out corpus of claims, the taxonomy requires revision.

This declaration follows pitfall C10 below and the C2 symmetric-standards
rule. The lab does not claim its own framework is [Verified]; it claims
the framework is a falsifiable design prior, like everything else it
audits.

---

## 1. Philosophical scaffold of the 5 labels

**[Verified]** corresponds to claims that are exact-by-construction or pass
deterministic reproducibility checks, satisfying Mayo's strong severity
criterion ([Mayo 2018](https://doi.org/10.1017/9781107286184), p. 14) with
no residual free parameters; equivalently, these are claims whose
description length under the MDL principle ([Rissanen
1978](https://doi.org/10.1016/0005-1098%2878%2990005-5)) requires no
post-hoc parameter coding.

**[Empirical fit]** applies to claims that are Hempel-confirmed by data
([Hempel 1945](https://doi.org/10.1093/mind/LIV.213.1)) and Carnap-consistent
with total evidence ([Carnap
1950](https://archive.org/details/logicalfoundations00carn)) but carry at
least one parameter adjusted after observing the data, placing them in what
[Lakatos 1978](https://doi.org/10.1017/CBO9780511621123) (Ch. 1, p. 34)
would call a potentially **degenerating problemshift**; these claims survive
p-value reporting consistent with the [ASA Statement (Wasserstein and Lazar
2016)](https://doi.org/10.1080/00031305.2016.1154108) but do not meet the
[Benjamin et al. 2018](https://doi.org/10.1038/s41562-017-0189-z) discovery
threshold without look-elsewhere correction.

**[Open conjecture]** corresponds to claims that articulate a non-empty set
of potential falsifiers in [Popper 1959](http://strangebeautiful.com/other-texts/popper-logic-scientific-discovery.pdf)
(p. 18) sense and carry a stated falsification path (**Fpath**) that
operationalizes the [Gelman-Loken 2014](https://sites.stat.columbia.edu/gelman/research/published/ForkingPaths.pdf)
requirement of precommitted analysis; without such a path, no severity
assessment is possible (Mayo 2018, BENT criterion, p. 5).

**[Risk]** and **[High-risk]** apply when [Ioannidis
2005](https://doi.org/10.1371/journal.pmed.0020124) PPV analysis predicts
low post-study probability: no Fpath, no look-elsewhere correction per
[Gross and Vitells 2010](https://doi.org/10.1140/epjc/s10052-010-1470-8),
weak venue, or control matches insufficient to rule out confounding by
[Pearl 2009](https://doi.org/10.1017/CBO9780511803161) Ch. 4 identification
criteria; the evidence structure may exhibit one or more of [Langmuir
1953](https://en.wikipedia.org/wiki/Pathological_science) symptoms of
pathological science *without any inference about researcher intent*.

**[Retracted]** records claims withdrawn from the published record. This
label denotes withdrawal, not misconduct (see pitfall C7).

Crucially, this taxonomy does **not** draw a [Laudan
1983](https://en.wikipedia.org/wiki/Larry_Laudan)-refuted demarcation
boundary between science and its alternatives; it grades the degree to
which claims have been subjected to, and survive, severe testing. The
membership question ("is this science?") is replaced by the evidential
question ("under what description does this evidence count?"). The
specific terms refused as labels are listed inside a fenced block in
`FRAMEWORK.md` (the CI scanner skips fenced blocks; see also pitfall C1
below).

---

## 2. Core citations

The following ten citations are the load-bearing literature for the five
labels.

1. **Popper, K. (1959). _The Logic of Scientific Discovery_. Hutchinson, London.** (Ch. 4, p. 57; criterion stated p. 18.) [PDF](http://strangebeautiful.com/other-texts/popper-logic-scientific-discovery.pdf) -- Defines the falsifiability requirement that grounds the Fpath obligation in [Open conjecture] and the absence-of-Fpath criterion for [Risk].

2. **Lakatos, I. (1978). _The Methodology of Scientific Research Programmes_. CUP.** DOI: [10.1017/CBO9780511621123](https://doi.org/10.1017/CBO9780511621123). (Hard core: Ch. 1 sec. 3(a), p. 48; progressive vs degenerating: sec. 2(c), p. 34.) -- Grounds the distinction between [Verified] (progressive, no new free parameters) and [Empirical fit] (potentially degenerating, post-hoc parameter addition).

3. **Mayo, D.G. (2018). _Statistical Inference as Severe Testing_. CUP.** DOI: [10.1017/9781107286184](https://doi.org/10.1017/9781107286184). (Severity weak p. 5; strong p. 14.) -- Operational definition of what distinguishes [Verified] from [Empirical fit] (severe test passed vs not) and the BENT criterion for [Risk].

4. **Ioannidis, J.P.A. (2005). Why Most Published Research Findings Are False. _PLOS Medicine_ 2(8): e124.** DOI: [10.1371/journal.pmed.0020124](https://doi.org/10.1371/journal.pmed.0020124). [PMC1182327](https://pmc.ncbi.nlm.nih.gov/articles/PMC1182327/) -- PPV framework that grounds [Risk] classification based on base rate, power, and bias.

5. **Gelman, A. and Loken, E. (2014). The Statistical Crisis in Science. _American Scientist_ 102(6): 460-465.** [PDF](https://sites.stat.columbia.edu/gelman/research/published/ForkingPaths.pdf) -- Formalizes the garden-of-forking-paths problem; grounds the Fpath requirement as the claim-level analog of preregistration.

6. **Wasserstein, R.L. and Lazar, N.A. (2016). The ASA's Statement on p-Values. _The American Statistician_ 70(2): 129-133.** DOI: [10.1080/00031305.2016.1154108](https://doi.org/10.1080/00031305.2016.1154108). [PDF](https://www.amstat.org/asa/files/pdfs/p-valuestatement.pdf) -- Minimum acceptable p-value reporting; non-compliance places a claim in [Risk].

7. **Gross, E. and Vitells, O. (2010). Trial Factors for the Look Elsewhere Effect in High Energy Physics. _European Physical Journal C_ 70: 525-530.** DOI: [10.1140/epjc/s10052-010-1470-8](https://doi.org/10.1140/epjc/s10052-010-1470-8). [arXiv:1005.1891](https://arxiv.org/abs/1005.1891) -- Formalizes look-elsewhere correction; absence of correction is a [Risk] criterion.

8. **Open Science Collaboration (2015). Estimating the Reproducibility of Psychological Science. _Science_ 349(6251): aac4716.** DOI: [10.1126/science.aac4716](https://doi.org/10.1126/science.aac4716) -- Empirical calibration of the expected rate of replication failure.

9. **Pearl, J. (2009). _Causality: Models, Reasoning, and Inference_, 2nd ed. CUP.** DOI: [10.1017/CBO9780511803161](https://doi.org/10.1017/CBO9780511803161). (Direct and indirect effects: Ch. 4 sec. 4.5, pp. 126-133.) -- Defines the CDE used by F2 and the identification conditions that must be met for a CDE claim to qualify as [Empirical fit].

10. **Laudan, L. (1983). The Demise of the Demarcation Problem. In _Physics, Philosophy and Psychoanalysis_. Reidel, pp. 111-127.** -- Establishes that the strong demarcation binary is philosophically untenable; the five-label system explicitly follows Laudan's recommendation to replace demarcation with graded evidence evaluation.

Secondary anchors (cited where directly relevant):
- [Munafo et al. 2017](https://doi.org/10.1038/s41562-016-0021) Manifesto for Reproducible Science
- [Chambers 2013](https://doi.org/10.1016/j.cortex.2012.12.016) Registered Reports
- [Camerer et al. 2016](https://doi.org/10.1126/science.aaf0918) Economics replication
- [Klein et al. 2018 Many Labs 2](https://doi.org/10.1177/2515245918810225)
- [Brier 1950](https://doi.org/10.1175/1520-0493%281950%29078%3C0001%3AVOFEIT%3E2.0.CO%3B2) calibration
- [Lichtenstein et al. 1982](https://en.wikipedia.org/wiki/Calibration_(statistics)) calibration of probabilities
- [Grunwald 2007](https://mitpress.mit.edu/9780262072816/) MDL Principle

---

## 3. Per-domain decomposition for Open conjecture (adapted from Cochrane RoB 2)

[Cochrane RoB 2](https://methods.cochrane.org/bias/resources/rob-2-revised-cochrane-risk-bias-tool-randomized-trials)
decomposes the overall risk-of-bias judgement into per-domain signalling
questions. We adopt the same pattern for `[Open conjecture]` and `[Risk]`
labels.

Each `[Open conjecture]` claim in a CASE file MAY (and from CASE-07 onward
SHOULD) carry a small block of three signalling questions:

| # | Domain | Signalling question | Answer |
|---|---|---|---|
| 1 | Mathematical internal consistency | Does the claim re-derive from definitions without contradiction? | Yes / No / Partial |
| 2 | Empirical contact | Does the claim predict a measurable quantity, with a stated tolerance? | Yes / No / Partial |
| 3 | Selection / reporting | Has the claimant reported all variants tried, or only the matching one? | Yes / Unknown / No |

The overall label is the **least favourable** judgement, matching Cochrane
RoB 2's rule. Demotion from `[Open conjecture]` to `[Risk]` requires
naming which of (1)-(3) drove the change. This satisfies lesson L2.4
([GRADE](https://gradepro.org/handbook/) upgrade / downgrade rationale).

Retrofitting CASE-00..CASE-06 to use signalling-question blocks is *not*
required in this loop; the requirement applies to CASE-07 onward.

---

## 4. The C-list: pitfalls the lab must avoid

The following ten practices would undermine the credibility of the
five-label system and, depending on jurisdiction, could create legal
exposure. Each is stated as an operational prohibition with the
corresponding epistemic reason. This list is binding alongside `CHARTER.md`.

**C1. Do not use membership labels of the demarcation kind that Laudan 1983 refused (the precise tokens are listed in `FRAMEWORK.md` inside a fenced block).**
Laudan 1983 p. 125 established that these terms carry purely emotive force. The labels grade evidence structure, not membership in a scientific category. Applying a membership label to a researcher exposes the lab to defamation liability; it also undermines epistemic standing because Laudan's argument shows no principled membership criterion exists.

**C2. Do not apply asymmetric evidential standards between the lab's own claims and the claims being audited.**
The same severity criterion (Mayo 2018) that places an audited claim in [Risk] applies equally to the lab's own classification methodology. The lab's own procedures -- including the phi-architecture prior and F2 CDE estimates -- are stated with their own epistemic status on the same five-label scale. Asymmetric standards are a form of the *ad hominem tu quoque* fallacy dressed as epistemics.

**C3. Do not treat Fpath absence as evidence of intent to deceive.**
Gelman and Loken 2014 showed that forking-paths problems arise even when researchers do not consciously p-hack. The absence of a Fpath is an evidential deficit, not a character attribution. The [Risk] label describes what can be inferred from the data, not what was in the researcher's mind.

**C4. Do not use look-elsewhere corrections asymmetrically.**
If the lab applies Gross-Vitells LEE correction to the claims it audits, it must apply the same correction to its own multi-comparison analyses. Selective correction is itself a form of the forking-paths problem.

**C5. Do not equate [Empirical fit] with "probably true."**
Ioannidis 2005 showed that [Empirical fit] status -- a significant result consistent with prior data and reported honestly -- carries a PPV that can be far below 0.5 in low-base-rate fields. The label denotes structural fitness for the class, not a posterior probability of truth.

**C6. Do not apply Langmuir/Park/Gardner phenomenology as a direct label for individual researchers.**
The six Langmuir symptoms are descriptions of evidence patterns. A claim can exhibit all six symptoms while its author acts in complete good faith. The [Risk] and [High-risk] labels encode the evidence pattern, not the author's status.

**C7. Do not allow the [Retracted] label to imply fraud absent an explicit retraction notice.**
Retraction means withdrawal from the published record, not misconduct. Retractions occur for a range of reasons including honest error. The label should be applied only when a formal retraction notice exists in the publishing journal's record, and the retraction notice itself should be cited.

**C8. Do not use calibration scores (Brier, prediction accuracy) from the lab's own models as evidence that those models are correct in new domains.**
Calibration on historical data (Lichtenstein et al. 1982, Tetlock 2015) does not transfer automatically to out-of-distribution domains. Generalization claims require severity analysis specific to the new domain.

**C9. Do not treat MDL compression gain as proof of causal structure.**
MDL (Rissanen 1978) establishes that a model is a good description of data. Pearl 2009 established that description is at Layer 1 (associational) of the causal hierarchy; causal interpretation requires identification conditions at Layer 2 or higher. Compressing data with phi does not establish that phi causes the observed regularities.

**C10. Do not claim that the five-label system itself is [Verified].**
The taxonomy is a normative framework grounded in published literature. It is not derived from a deductive proof. Its own epistemic status is `[Open conjecture]` with the Fpath stated in section 0.

---

## 5. Mapping to other reporting frameworks

For readers familiar with peer audit / quality frameworks:

| External framework | What we adopt from it | Reference |
|---|---|---|
| Cochrane RoB 2 | Per-domain signalling questions; overall judgement is least favourable domain | [methods.cochrane.org](https://methods.cochrane.org/bias/resources/rob-2-revised-cochrane-risk-bias-tool-randomized-trials) |
| GRADE handbook | Documented upgrade/downgrade rationale on every label change | [gradepro.org](https://gradepro.org/handbook/) |
| CONSORT / PRISMA / EQUATOR | Checklist as submission gate (YAML front-matter in CASE files) | [equator-network.org](https://www.equator-network.org/reporting-guidelines/) |
| OSF / AsPredicted | Pre-audit plan committed before verdict (Fpath rule) | [help.osf.io](https://help.osf.io/article/330-welcome-to-registrations) / [aspredicted.org](https://aspredicted.org/) |
| Science Feedback | Right-of-reply with 14-day response window | [science.feedback.org/process](https://science.feedback.org/process/) |
| Wikipedia BLP / FRINGE | Discipline on contentious characterisations of living persons; FRINGE intake filter | [BLP](https://en.wikipedia.org/wiki/Wikipedia:Biographies_of_living_persons) / [FRINGE](https://en.wikipedia.org/wiki/Wikipedia:Fringe_theories) |
| PCI / Hypothes.is | Immutable versioned CASE files; structured claim/evidence/label triple in YAML | [peercommunityin.org](https://peercommunityin.org) / [hypothes.is](https://web.hypothes.is/about/) |
| Retraction Watch | Separate documented act from lab interpretation | [retractionwatch.com](https://retractionwatch.com/) |
| PubPeer / Sarkar v. Doe | Verifiable source anchor for every sub-claim | [pubpeer FAQ](https://pubpeer.com/static/faq) / [ACLU](https://www.aclu.org/cases/sarkar-v-doe-pubpeer-subpoena-challenge) |

What we explicitly do NOT adopt:
- A demarcation criterion (per C1 and Laudan 1983).
- Anonymous moderation (we use maintainer review under a public charter).
- Reviewer identity disclosure at the case level (premature for a 7-case
  lab; revisit at >= 20 cases).

---

## 6. Where to from here

This file is itself an `[Open conjecture]` (see section 0). Improvements to
the methodology that change a load-bearing rule require:

1. A pull request to `methodology/README.md` and (if affected) to
   `FRAMEWORK.md`.
2. A `PROMOTION-LEDGER.md` entry recording the change.
3. Updated cross-links in any CASE file whose label depends on the changed
   rule.

The two known weaknesses we have not yet addressed:

- **CASE-00 is not yet decomposed by underlying project.** A future split
  into CASE-00a (IGLA), CASE-00b (GoldenFloat), CASE-00c (phi-paper) is on
  the queue.
- **No Zenodo DOI yet.** Tag `v0.1-methodology` will be archived once
  M1-M9 land cleanly.

---

**Last update:** 2026-06-02.
