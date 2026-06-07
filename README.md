# claim-audit-lab

A public, symmetric, falsifiable register of audits of theoretical-physics,
numeric-format, and metaphysical claims that invoke the golden ratio phi,
Fibonacci/Lucas structure, or related "fundamental constant" framings.

This repository applies the same five-label epistemic framework to itself
that it applies to other published programmes. **The framework is non-negotiable
and applied symmetrically.**

---

## Why this exists

Phi-anchored theories form a recognisable cluster across number systems,
cosmology, consciousness studies, architecture, and ML. Some of those
programmes are careful: they label their claims, state their falsifiers, and
record their negative results. Some are not. The distinction matters and is
rarely made explicit in one place.

This lab takes published claims (the authors' own words, with source URLs)
and assigns each one a single epistemic label from a fixed taxonomy. It does
this for outside programmes AND for the maintainers' own work (see
[`cases/CASE-00-self-audit.md`](cases/CASE-00-self-audit.md)).

**This is not a debunking site.** Many programmes audited here contain
[Verified] arithmetic, [Empirical fit] data, and honestly labelled [Open
conjectures] with stated falsification paths. The lab records what each
programme is, in its own terms, against a fixed standard.

---

## The framework (one paragraph)

Every claim gets exactly one of five labels:

- **[Verified]** -- exact-by-construction or directly measured by a
  deterministic harness.
- **[Empirical fit]** -- matches data but at least one parameter was chosen
  post-hoc.
- **[Open conjecture]** -- plausible; **must carry a stated falsification
  path (Fpath)**.
- **[Risk]** / **[High-risk]** -- weak venue, no Fpath, unbounded
  look-elsewhere, or a control matches.
- **[Retracted]** -- withdrawn; never to be cited as evidence again.

Full rules and examples: [`FRAMEWORK.md`](FRAMEWORK.md).

---

## Repository charter

- **No ad hominem.** Claims, not people. Every entry quotes the author's own
  words with a source URL.
- **Symmetric application.** The lab's own work (IGLA, GoldenFloat, phi-paper)
  is audited under the same rules in CASE-00.
- **English + ASCII only.** Public artefact discipline.
- **Banned words in entries:** see the list inside the fenced block in
  `FRAMEWORK.md` (the CI scanner skips fenced blocks and blockquotes, so the
  policy can list the forbidden tokens without tripping itself). State labels,
  not insults.
- **Corrections welcome.** Open a PR or an issue. If a subject of a case file
  documents that we misread their claim, the case is updated and the prior
  version is preserved in `archive/`.
- **Right of reply.** Subjects of any CASE file may submit a one-page reply;
  it is included verbatim in the case file under "Subject's reply" with a
  link to the source.

See [`CHARTER.md`](CHARTER.md) for the full text.

---

## Index of cases

| ID       | Subject                                | Domain                              | Status |
|----------|----------------------------------------|-------------------------------------|--------|
| [CASE-00](cases/CASE-00-self-audit.md) | self-audit (lab maintainers) | numeric formats / ML training | draft |
| [CASE-01](cases/CASE-01-savchenko-pointer-architecture.md) | A. Savchenko -- Pointer Architecture v9.0 | consciousness / dark matter | draft |
| [CASE-02](cases/CASE-02-stakhov-mathematics-of-harmony.md) | A. Stakhov -- Mathematics of Harmony | number systems / phi-universalism | draft |
| [CASE-03](cases/CASE-03-el-naschie-e-infinity.md) | M.S. El Naschie -- E-infinity theory | quantum spacetime / dimensions | draft |
| [CASE-04](cases/CASE-04-petoukhov-matrix-genetics.md) | S.V. Petoukhov -- Matrix Genetics | bioinformatics / phi-matrices | draft |
| [CASE-05](cases/CASE-05-kramer-klimesch-golden-rhythms.md) | M.A. Kramer & W. Klimesch -- Golden EEG Rhythms | neuroscience (positive control) | draft |
| [CASE-06](cases/CASE-06-de-groot-economic-cycles.md) | B. de Groot -- Phi-period economic cycles | econometrics (positive control) | draft |
| [CASE-07](cases/CASE-07-carroll-kaplan-m-planck.md) | Carroll/Kaplan -- M_pl coincidence class | adjacent class declined in v2.1 | draft |
| [CASE-08](cases/CASE-08-vasilev-bnf-equivalence-class.md) | Vasilev -- BNF equivalence-class result (v2.3 self-audit) | symbolic regression / methodology calibration | draft |
| [CASE-09](cases/CASE-09-corona-rom-vs-closed-rule.md) | Corona ROM CATALOG vs closed rule (self-audit) | numeric formats / ROM consistency | draft |

---

## Scorecard dashboard

Claim counts per CASE file, machine-readable source in
[`data/scorecard.json`](data/scorecard.json). Label taxonomy in
[`data/labels.json`](data/labels.json). Counts are bulleted top-level
claims inside each inventory section; joint or sub-claims may share a
bullet, so the table is a calibration aid, not a precise inventory.
Label changes are recorded in [`PROMOTION-LEDGER.md`](PROMOTION-LEDGER.md).

| Case | Subject | V | EF | OC+Fpath | R | HR | Ret | Fpath executable | Reply |
|---|---|---:|---:|---:|---:|---:|---:|---|---|
| [CASE-00](cases/CASE-00-self-audit.md) | self-audit (maintainers) | 4 | 1 | 2 | 2 | 0 | 1 | yes | n/a |
| [CASE-01](cases/CASE-01-savchenko-pointer-architecture.md) | A. Savchenko | 7 | 3 | 4 | 3 | 0 | 1 | partial | pending |
| [CASE-02](cases/CASE-02-stakhov-mathematics-of-harmony.md) | A. Stakhov | 6 | 1 | 2 | 4 | 1 | 0 | partial | pending |
| [CASE-03](cases/CASE-03-el-naschie-e-infinity.md) | M.S. El Naschie | 3 | 0 | 0 | 2 | 3 | 0 | no | pending |
| [CASE-04](cases/CASE-04-petoukhov-matrix-genetics.md) | S.V. Petoukhov | 3 | 2 | 1 | 4 | 0 | 0 | pending | pending |
| [CASE-05](cases/CASE-05-kramer-klimesch-golden-rhythms.md) | Kramer & Klimesch (positive control) | 2 | 2 | 1 | 2 | 0 | 0 | yes | pending |
| [CASE-06](cases/CASE-06-de-groot-economic-cycles.md) | B. de Groot (positive control) | 3 | 1 | 1 | 3 | 0 | 0 | yes | pending |
| [CASE-07](cases/CASE-07-carroll-kaplan-m-planck.md) | Carroll/Kaplan M_pl class | 0 | 0 | 0 | 3 | 0 | 0 | partial | n/a |
| [CASE-08](cases/CASE-08-vasilev-bnf-equivalence-class.md) | Vasilev BNF (v2.3 self-audit) | 1 | 0 | 3 | 0 | 0 | 0 | yes | pending |
| [CASE-09](cases/CASE-09-corona-rom-vs-closed-rule.md) | Corona ROM vs closed rule (self-audit) | 1 | 0 | 3 | 0 | 0 | 0 | yes | n/a |
| [CASE-10](cases/CASE-10-phi-bias-coincidence-scan.md) | PHI_BIAS coincidence-class survey (self-audit) | 0 | 0 | 1 | 0 | 0 | 0 | yes | n/a |
| **Totals (v0.5, CASE-10)** | 11 cases | **30** | **10** | **18** | **23** | **4** | **2** | -- | -- |

**Reading the table.** `V` = [Verified], `EF` = [Empirical fit],
`OC+Fpath` = [Open conjecture] with stated falsification path, `R` =
[Risk], `HR` = [High-risk], `Ret` = [Retracted]. `Fpath executable` =
whether the largest [Open] claim's falsification path can be run by an
outside reader today. `Reply` = whether the subject's right-of-reply
(CHARTER.md s 3) has been exercised (`pending` = invitation open, no
reply received; `n/a` = self-audit).

**What the v0.2 baseline shows.** The cleanest [Open conjecture] with
an executable Fpath in the catalog is CASE-05 (Kramer-Klimesch),
followed by CASE-06 (de Groot). Both are deliberately included as
**positive controls** -- the test of whether the framework recognises
responsibly-labelled, peer-reviewed phi work as such. CASE-00
(self-audit) carries the only [Retracted] entry in the register, by
construction (delta_CP = 3/phi^2, withdrawn). CASE-03 (El Naschie)
carries the highest [High-risk] count in the register.

The framework itself is labelled [Open conjecture] -- see
[`methodology/README.md`](methodology/README.md) Section 0 and the
`framework_self_label` block in `data/labels.json`.

### Adjacent (not audited as a primary subject)

- **Scott A. Olsen** -- co-author of the Pellis-Vasilev-Olsen short paper that
  this lab's CASE-00 self-audit is partly built around. As a current
  collaborator he is conflict-of-interest excluded from being a primary audit
  subject; his contribution is therefore part of the self-audit (CASE-00) and
  the symmetric-mirror sections of CASE-02 / CASE-03 / CASE-04, not a
  standalone case file. See [`phi_theorists_catalog.md`](phi_theorists_catalog.md)
  entry #9 for the catalog record.

### Cases under consideration (not yet written)

See [`phi_theorists_catalog.md`](phi_theorists_catalog.md) for the working
list of 14 candidate subjects ranked by independent-publication weight.
Not every candidate will receive a full CASE file: under-verified subjects
(no confirmed primary URL) are skipped; fringe-adjacent entries that have no
falsifiable claim are catalog-only.

---

## How to read a case

Every CASE file has fixed sections:

1. **Identity** -- who, where, primary claim, source URLs.
2. **Programme claims** -- verbatim quotes of the main claims.
3. **Tier mapping** -- author's own labelling (if any) mapped to our 5-label
   framework.
4. **[Verified] inventory** -- what survives [Verified] under our framework.
5. **[Empirical fit] / [Open conjecture] inventory** -- post-hoc fits and
   stated-or-implied conjectures, with explicit Fpath when given.
6. **[Risk] / [Retracted] inventory** -- claims that fail one or more of:
   stated Fpath, look-elsewhere control, peer-reviewed venue, reproducibility.
7. **Symmetric mirror** -- a comparable claim from our own work, classified
   under the same rule. This is non-optional.
8. **Sources** -- every URL fetched, with date.
9. **Subject's reply** -- empty unless the subject sends a reply.

---

## Contributing

PRs welcome for: new cases (one author per case), corrections, source URL
additions, subject replies.

PRs rejected for: ad hominem, removal of [Verified] labels we honestly
assigned, removal of CASE-00 self-audit, edits without source URLs.

---

## License

Text in this repository is licensed under [CC-BY-4.0](LICENSE-CC).
Code (if any) is licensed under [MIT](LICENSE-MIT).

Quoted material from other authors is used under fair-use / fair-dealing for
purposes of scholarly criticism and review, with attribution and source URL
to every quotation.

---

**Maintainers:** Dmitrii Vasilev (`@gHashTag`).
**Contact:** open an issue.
**Last index update:** 2026-06-02 (v0.2 -- scorecard, methodology, contributing, COI, promotion-ledger added).
