# CASE-06: Bert de Groot, Rene Segers, David Prins -- phi in economic cycle lengths

**Subject:** E.A. (Bert) de Groot (lead author); R. (Rene) Segers; D. (David) Prins (co-authors).
**Affiliation:** De Groot and Segers: Econometric Institute, Erasmus University Rotterdam,
Netherlands. Prins: Gibbs Analytics Consulting, Rotterdam.
**Programme:** Single-paper programme: "Disentangling the enigma of multi-structured economic
cycles -- A new appearance of the golden ratio" (2021).
**Audit date:** 2026-06-02
**Maintainer:** @gHashTag
**Status:** draft
**Last update:** 2026-06-02

> **Positive-control note.** This is the second positive-control case in the register, alongside
> CASE-05 (Kramer/Klimesch). The audit records this as an example of a phi-observation published
> in a standard peer-reviewed venue with appropriate epistemic hedging. The purpose is not to
> confirm the finding but to calibrate what responsible phi-empiricism looks like at the level of
> methodology and framing discipline.

---

## 1. Identity

De Groot is a Professor of Governance and Strategic Investment Policy at the Erasmus School of
Economics, Erasmus University Rotterdam, Netherlands. Segers is at the same Econometric Institute;
Prins is at Gibbs Analytics Consulting. In 2021 they published a single paper in *Technological
Forecasting and Social Change* (Elsevier, ISSN 0040-1625, Scopus/WoS indexed) that is the sole
subject of this audit. The paper is open-access under CC BY-NC-ND 4.0.

The central claim of the paper is that a meta-analysis of detected economic cycle lengths across
25 OECD countries plus Europe reveals that the ratio of shorter to longer consecutive cycle lengths
averages 0.619, which the authors note is close to the reciprocal of phi (1/phi = 0.6180...). They
present this as "a new appearance of the golden ratio" in empirical economic data, and as a
direction for further theory development, not as a claim that phi is a fundamental constant of
economics.

The same group published a 2022 follow-up paper in the same journal, "Non-resonating cycles in a
dynamic model for investment behavior" (TFSC vol. 177), which extends the dynamic modelling
context. That paper is not itself the subject of this audit but is noted as evidence of a live
research programme.

Primary references for this case (all URLs fetched on 2026-06-02):

- https://doi.org/10.1016/j.techfore.2021.120793 -- primary paper (ScienceDirect, Elsevier).
- https://repub.eur.nl/pub/135548/1-s2.0-S0040162521002250-main.pdf -- open-access PDF, EUR
  repository (CC BY-NC-ND 4.0).
- https://pure.eur.nl/en/publications/disentangling-the-enigma-of-multi-structured-economic-cycles-a-ne/ -- Erasmus PURE record.
- https://ideas.repec.org/a/eee/tefoso/v169y2021ics0040162521002250.html -- IDEAS/REPEC citation
  record with citing-paper list (fetched 2026-06-02).
- https://www.sciencedirect.com/science/article/pii/S0040162522000476 -- 2022 follow-up paper
  (ScienceDirect abstract page, paywall; abstract only fetched).
- https://www.goldennumber.net/gdp-economic-subcycles-golden-ratio-patterns/ -- third-party
  popularisation by Gary Meisner (goldennumber.net, 2021-06-26); fetched as a framing-contrast
  reference only.

---

## 2. Programme claims (verbatim)

The authors' central claims, in their own words from the paper:

> "A meta-analysis on the detected cycle lengths reveals that the ratio between the lengths of
> consecutive cycles often closely matches the golden ratio, phi."
> -- de Groot, Segers & Prins (2021), *Technological Forecasting and Social Change*, 169, 120793,
> Abstract. [https://doi.org/10.1016/j.techfore.2021.120793]

> "The average of the calculated ratio's is equal to 0.619."
> -- Same paper, Section 4 (Results).

> "The probability value for the test statistic is equal to P(t44 = 0.0745) = 0.94. Therefore
> hypothesis H cannot be rejected."
> -- Same paper, Section 4 (Results). Hypothesis H is: "The ratios between consecutive cycle
> lengths come from a distribution that is centered around Phi = 0.618."

> "Opposed to what was previously suggested, the relative distance between cycle lengths is
> supposedly far from an integer fraction. Instead, the ratio between the cyclical lengths is
> remarkably close to Phi."
> -- Same paper, Section 4.

> "Our results suggest that the ratio's between these cyclical lengths are often close to the
> reciprocal of the golden ratio, Phi."
> -- Same paper, Section 5 (Conclusion). [Emphasis on "suggest" and "often" is in the original.]

> "Our analysis was necessarily confined to our choice of data, the time span of the data, our
> cycle detection method, and our research objectives."
> -- Same paper, Section 5 (Conclusion, limitations paragraph).

> "Our paper thus provides a new direction for theory development regarding economic cycles and
> dynamic stability."
> -- Same paper, Abstract.

---

## 3. Tier mapping

The paper does not use an explicit epistemic taxonomy. The authors do not label claims as
conjectures, hypotheses, or established results in a formal sense. The mapping below is the
lab's reading of the paper's language:

| Paper's language | Our label |
|-----------------|-----------|
| "often closely matches" / "suggest" / "remarkably close" | [Empirical fit] -- hedged fit claim |
| "a new direction for theory development" | [Open conjecture] -- the mechanism is not yet specified |
| "confined to our choice of data, the time span ... our cycle detection method" | Authors' own acknowledgement of free parameters |

The authors' language is precisely calibrated. They do not write "phi is a law of economics."
They write "a new appearance" -- exactly the framing the lab considers appropriate for this
epistemic status.

---

## 4. [Verified] inventory

- **[Verified]** The methodology pipeline (Fourier + GARCH + harmonic regression + BIC-based
  cycle-count selection) is standard econometric practice for cycle detection in GDP time series.
  Each step is individually attributable to established sources: GARCH to Bollerslev (1986) and
  Engle (1982); Fourier spectral analysis is classical; harmonic regression with BIC model
  selection is textbook. The combination as described is a reasonable extension of standard
  practice for non-stationary time series. Source:
  https://repub.eur.nl/pub/135548/1-s2.0-S0040162521002250-main.pdf (methodology sections 2-3).
  Evidence: each methodological component has prior literature; the paper correctly cites these
  prior sources. This is [Verified] for "the methodology is legitimate econometric practice," not
  for "the cycle lengths detected are the true cycle lengths."

- **[Verified]** The paper is published in *Technological Forecasting and Social Change*, vol. 169
  (2021), Elsevier, with DOI 10.1016/j.techfore.2021.120793, under open access (CC BY-NC-ND 4.0),
  and is indexed in Scopus and Web of Science. The paper was received 4 May 2020, revised 1 April
  2021, accepted 6 April 2021, available online 24 April 2021. Source:
  https://repub.eur.nl/pub/135548/1-s2.0-S0040162521002250-main.pdf (journal header). Evidence:
  the open-access PDF is retrievable from the EUR repository.

- **[Verified]** The arithmetic: the sample average of 45 ratios reported in the paper is 0.619;
  the sample standard deviation is 0.097; the t-statistic for a t-test against the hypothesised
  mean 0.618 is t = (0.619 - 0.618) / (0.097 / sqrt(45)) = 0.0745, with p-value 0.94 on 44
  degrees of freedom. This arithmetic is reproducible from the reported summary statistics.
  Source: https://repub.eur.nl/pub/135548/1-s2.0-S0040162521002250-main.pdf (Section 4).
  Evidence: the numbers are self-consistent and checkable in one line of arithmetic.

---

## 5. [Empirical fit] inventory

- **[Empirical fit]** The average ratio of shorter-to-longer consecutive cycle lengths across 25
  OECD countries plus Europe is 0.619, with the authors' t-test (p = 0.94) failing to reject the
  hypothesis that this is consistent with 1/phi = 0.618. Source:
  https://doi.org/10.1016/j.techfore.2021.120793. Free parameters:
  (a) the cycle detection method (Fourier + GARCH + harmonic regression; alternative methods
      -- e.g., Hodrick-Prescott filter, band-pass filter, wavelet decomposition -- may detect
      different cycle lengths for the same countries);
  (b) the definition of "consecutive cycles" in a multi-cycle decomposition (the BIC selects
      2-5 cycles per economy; which pairs are called "consecutive" is a modelling choice);
  (c) the aggregation method used in the meta-analysis (simple average of country-level ratios;
      a GDP-weighted average, or a random-effects meta-analysis, might differ);
  (d) the restriction to cycles of 3-15 years (this excludes Kuznets and Kondratieff cycles by
      construction; the authors explicitly acknowledge this). Pre-registered held-out test:
      ABSENT. No pre-registration statement is present in the paper. The authors acknowledge
      that applying the methodology to a different time span, different countries, or different
      GDP indicators would be a natural extension. They do not call this "replication"; this
      lab calls it the missing next experiment. Control condition: no alternative ratio (e.g.,
      1/2, 1/3) was formally tested against the same data; the test is one-sided (against phi).
      This is the primary gap in the matched-control argument.

The p-value of 0.94 is reported as the probability of observing the data under H: mean = phi.
It is not a p-value in the standard null-hypothesis-rejection sense (which would test against
mean = phi and report the probability of a more extreme result). A p = 0.94 means the test
statistic is well within the phi-consistent region -- it does not mean the probability the
true mean is phi is 94%. This distinction is stated in the framework and is noted here for
calibration, not as a criticism of the paper, which correctly states the test as "H cannot be
rejected."

---

## 6. [Open conjecture] inventory

- **[Open conjecture]** The phi ratio between consecutive cycle lengths reflects a structural
  property of economic dynamics -- specifically, the authors' 2022 follow-up proposes a
  "non-resonating cycles" mechanism in a dynamic investment model. The 2021 paper frames this
  as "a new direction for theory development." No complete theoretical model deriving phi from
  economic primitives is stated in the 2021 paper. Source: 2021 paper Section 5; 2022 follow-up
  at https://www.sciencedirect.com/science/article/pii/S0040162522000476. **Fpath (lab-stated,
  not stated by the authors in the 2021 paper):** the conjecture that phi has structural economic
  causes (not just being an aggregation artefact) is falsified if the ratio 0.619 fails to
  replicate in an independent sample of countries with a different cycle-detection method, OR if
  the same Fourier + GARCH pipeline applied to synthetic AR(2) processes with known non-phi
  cycle ratios returns ratios close to 0.619 (which would identify the result as a pipeline
  artefact). The 2022 non-resonating-cycles paper provides a candidate theoretical mechanism;
  whether it predicts phi specifically is not retrievable from the abstract alone. Executable:
  data (OECD GDP) is public; code would need to be released or reconstructed.

---

## 7. [Risk] / [High-risk] inventory

- **[Risk]** Look-elsewhere correction absent. The paper tests one hypothesis: are cycle-length
  ratios consistent with phi = 0.618? It does not report whether other "nice" ratios (1/2 = 0.5,
  1/sqrt(2) = 0.707, 1/e = 0.368, sqrt(phi) = 0.786) were also tested against the same 45
  ratios and also could not be rejected. Given a sample standard deviation of 0.097, many values
  in the range [0.4, 0.85] would produce a high p-value under a one-tailed fail-to-reject test.
  This is FRAMEWORK.md [Risk] criterion (b): look-elsewhere correction missing. Source:
  https://repub.eur.nl/pub/135548/1-s2.0-S0040162521002250-main.pdf (Section 4, statistical test
  section). Note: the authors do not claim this correction is unnecessary; they simply did not
  perform it. The absence is a gap in the evidence, not a flaw in the authors' stated framing.

- **[Risk]** Meta-analysis aggregation method is post-hoc. The meta-analysis averages ratios
  across countries without a pre-specified weighting scheme, without accounting for the different
  number of cycles detected per country (2 to 5), and without a formal meta-analytic random-
  effects model. Countries with 4 or 5 cycles contribute more ratio observations than countries
  with 2 cycles, creating implicit weighting that is not discussed. This is FRAMEWORK.md [Risk]
  criterion (b). Source: same PDF, Sections 3-4. Again, this is a gap in the presented
  analysis, not an accusation of bad faith; the authors acknowledge the analysis was confined to
  their methodological choices.

- **[Risk]** No independent replication has been found with the same methodology applied to
  a different country sample or time window. A 2024-2025 Turkish study (published in a
  Turkish econometrics journal, dergipark.org.tr/en/download/article-file/5566160) applied
  cycle-ratio analysis to Turkish GDP data and found short- and medium-term cycles clustering
  around 0.618, citing de Groot et al. (2021). This is a partial confirmation but uses the
  same general approach and explicitly builds on the same phi hypothesis, so it does not count
  as an independent pre-registered replication. No paper has re-run the full OECD 25-country
  sample with an alternative cycle-detection method and reported whether the phi result survives.
  This is FRAMEWORK.md [Risk] criterion (b): the finding is not yet independently replicated.

The [Risk] items above are modest. They are the standard missing experiments for a first empirical
paper in a new direction, not indicators of methodological failure. The paper is correctly
labelled [Empirical fit] with [Risk] on the unreplicated meta-analysis component.

---

## 8. [Retracted] inventory

No claims have been retracted by the authors or the journal. The paper carries its 2021
conclusions without amendment as of the fetch date (2026-06-02). The corrections column of
the ScienceDirect record shows no corrigenda.

---

## 9. Symmetric mirror (MANDATORY)

| Subject's claim | Our comparable claim | Both labelled |
|-----------------|----------------------|---------------|
| Average ratio of OECD consecutive cycle lengths = 0.619, consistent with 1/phi (p = 0.94); no pre-registration; one cycle-detection method | IGLA RACE v2 hidden=64 phi-arm matching non-phi-arm; no pre-registration; one training run at proxy scale | both [Empirical fit] -- real data, real fit, missing pre-registered held-out replication |
| No independent replication of OECD result in a different country set with a different method | Phase B1-real four-arm champion-scale ablation not yet run; Phase B1-proxy only | both [Open] for the strongest claim; both have stated the missing experiment |
| Framing: "often closely matches," "suggest," "new direction for theory development" -- phi is an empirical pattern, not a universal | Framing: "phi is an architecture prior, the method survives, phi does not (yet)" -- phi is a hypothesis, not a law | same framing discipline: both decline the stronger universal claim |
| Look-elsewhere correction absent for the ratio 0.618 vs. other candidate ratios | phi-free grammars of equal cardinality match our compression -- our own internal control demoted the strongest phi-specificity claim to [Risk] | both [Risk] on the look-elsewhere/matched-control dimension; de Groot's gap is the missing alternative-ratio test; our gap is the already-demoted constants claim |

The symmetry here is the tightest in the register. The de Groot result and the IGLA proxy result
are at the same epistemic level for the same reasons: both are real empirical fits on real data,
both use a pipeline with free parameters that were not pre-specified in a registered protocol,
both report the phi-consistent result without a matched alternative-hypothesis test, and both name
the missing experiment without having run it. The joint Fpath is straightforward: (a) for de Groot,
run the same OECD GDP analysis with at least two alternative cycle-detection methods (e.g.,
band-pass filter and wavelet) and test whether the ratio distribution is equally consistent with
several candidate constants; (b) for the lab, run Phase B1-real at champion scale with four arms
and a pre-registered held-out evaluation. Either experiment resolves both gaps at once, if results
are shared: both programmes would gain from a pre-registered, multi-method, multi-constant null
test applied to each respective dataset.

---

## 10. Audit summary

Strongest part of the programme: the methodology is standard, well-documented, and
reproducible in principle (data is public from OECD; methods are clearly described). The
statistical fit (mean ratio 0.619 vs. 1/phi = 0.618, p = 0.94 fail-to-reject) is the cleanest
numerical phi-consistency result in the economics domain audited by this lab to date. The authors'
framing is exemplary: they write "suggest," "often," and "a new appearance," not "phi governs
economic dynamics." [Empirical fit] is the correct label and the authors' own language is
consistent with it.

Weakest claim: the meta-analysis aggregation component is the most post-hoc element --
country ratios are combined without pre-specified weighting, without a look-elsewhere test
against other candidate ratios, and without a formal random-effects model. This is [Risk] on the
matched-control dimension. The finding that consecutive cycle-length ratios are consistent with
phi is real; the claim that phi specifically is the relevant constant (rather than a value
anywhere in [0.55, 0.68]) requires the missing alternative-constant test.

Single experiment that would move the result: run the full 25-country Fourier + GARCH pipeline
with at least two alternative cycle-detection methods, test the distribution of consecutive-cycle
ratios against phi AND against two or three other candidate constants (e.g., 1/2, sqrt(2)/2),
apply a Bonferroni or FDR correction, and pre-register the prediction. If phi survives as
uniquely consistent, the result upgrades toward [Verified]; if several constants are equally
consistent, the result is correctly classified as a numerical coincidence.

Symmetric position of the lab: our own Phase B1-real (champion-scale four-arm ablation) is in
identical epistemic position -- the proxy result is real, the missing experiment is named, the
compute is pending. This is what a careful phi-empirical claim looks like in econometrics.
The framing is responsible, the methodology is sound, the missing piece is pre-registered
independent replication across methods and candidate constants -- which is the same missing
piece we acknowledge in our own Phase B1-real.

---

## 11. Sources

- 2026-06-02: https://doi.org/10.1016/j.techfore.2021.120793 -- primary paper DOI, Elsevier.
- 2026-06-02: https://repub.eur.nl/pub/135548/1-s2.0-S0040162521002250-main.pdf -- open-access
  PDF, EUR institutional repository (CC BY-NC-ND 4.0); full text read for methodology, stats,
  and verbatim quotes.
- 2026-06-02: https://pure.eur.nl/en/publications/disentangling-the-enigma-of-multi-structured-economic-cycles-a-ne/ -- Erasmus PURE record with journal metadata.
- 2026-06-02: https://ideas.repec.org/a/eee/tefoso/v169y2021ics0040162521002250.html -- REPEC
  record; citing-paper list shows one primary citing paper: the authors' own 2022 follow-up.
- 2026-06-02: https://www.sciencedirect.com/science/article/pii/S0040162522000476 -- 2022 follow-
  up paper abstract (paywall; only abstract/metadata page fetched).
- 2026-06-02: https://www.goldennumber.net/gdp-economic-subcycles-golden-ratio-patterns/ -- third-
  party popularisation; read to contrast the authors' hedged framing with a more expansive
  secondary interpretation. Gary Meisner, goldennumber.net, 2021-06-26.
- 2026-06-02: https://dergipark.org.tr/en/download/article-file/5566160 -- Turkish replication
  study (2024-2025, journal not fully identified from snippet); cites de Groot et al. 2021 and
  applies similar cycle-ratio analysis to Turkish GDP; classified as partial confirmation, not
  independent pre-registered replication.

---

## 12. Subject's reply

Empty. The subjects have not been notified of this CASE file as of 2026-06-02. Per CHARTER.md
s 3, a reply submitted at any time will be included verbatim with a source link.

---

**End of CASE-06.**
