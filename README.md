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

<!-- BEGIN GENERATED case-index (scripts/gen_readme_index.py) -->

*Generated from [`cases.yaml`](cases.yaml) by `scripts/gen_readme_index.py`. Do not edit this table by hand -- edit the manifest and re-run the script.*

| ID       | Subject                                | Domain                              | Class  | Status |
|----------|----------------------------------------|-------------------------------------|--------|--------|
| [CASE-00](cases/CASE-00-self-audit.md) | Self-audit  --  methodology calibration on our own work | numeric formats / ML training | Verified | draft |
| [CASE-01](cases/CASE-01-savchenko-pointer-architecture.md) | Savchenko pointer architecture | consciousness / dark matter | Risk | draft |
| [CASE-02](cases/CASE-02-stakhov-mathematics-of-harmony.md) | Stakhov Mathematics of Harmony | number systems / phi-universalism | Efit | draft |
| [CASE-03](cases/CASE-03-el-naschie-e-infinity.md) | El Naschie E-infinity theory | quantum spacetime / dimensions | Retr | draft |
| [CASE-04](cases/CASE-04-petoukhov-matrix-genetics.md) | Petoukhov matrix genetics | bioinformatics / phi-matrices | Risk | draft |
| [CASE-05](cases/CASE-05-kramer-klimesch-golden-rhythms.md) | Kramer-Klimesch golden rhythms (EEG) | neuroscience (positive control) | Risk | draft |
| [CASE-06](cases/CASE-06-de-groot-economic-cycles.md) | de Groot economic cycles | econometrics (positive control) | Risk | draft |
| [CASE-07](cases/CASE-07-carroll-kaplan-m-planck.md) | Carroll/Kaplan M_pl coincidence class | adjacent class declined in v2.1 | Risk | draft |
| [CASE-08](cases/CASE-08-vasilev-bnf-equivalence-class.md) | Vasilev BNF equivalence-class result (symmetric self-audit, v2.3 phi-paper) | symbolic regression / methodology calibration | Conj | draft |
| [CASE-09](cases/CASE-09-corona-rom-vs-closed-rule.md) | Corona ROM CATALOG vs closed-form ladder rule (symmetric self-audit) | numeric formats / ROM consistency | Conj | draft |
| [CASE-10](cases/CASE-10-phi-bias-coincidence-scan.md) | PHI_BIAS coincidence-class survey for v1.3 rule-derived rungs (GF6/10/14/48/96) | numeric formats / coincidence classes | Conj | draft |
| [CASE-12](cases/CASE-12-g-phi-rank-2-of-394/README.md) | Vasilev II + Pellis III -- v2.3 BNF equivalence-class rank 2/394 for G_phi (Conj, Pellis-gated) | symbolic regression / MDL-optimality | Conj | draft |
| [CASE-13](cases/CASE-13-singh-trace-dynamics.md) | Tejinder P. Singh -- trace dynamics + octonion unification with phi-arithmetic (Wave-10 HIGH) | trace dynamics / octonionic unification | Conj | draft |
| [CASE-14](cases/CASE-14-morato-spectral-triple.md) | L. Morato de Dalmases -- phi-anchored spectral-triple SM unification | spectral triples / SM unification | Risk | draft |
| [CASE-15](cases/CASE-15-pellis-coupling-constants.md) | S. Pellis -- solo prior phi-arithmetic publications (co-author audit) | phi-arithmetic / co-author mirror-audit | Risk | draft |
| [CASE-16](cases/CASE-16-phi-grid-collaboration.md) | Phi-Grid Project -- methodologically-aligned collaboration probe (positive control, NOT adversarial) | methodology (positive control) | Conj | draft |
| [CASE-18](cases/CASE-18-vasilev-tnf-golden-alphabet.md) | Vasilev Ternary Network Floats and the golden weight alphabet | numeric formats / ternary weight alphabet | Verified | draft |

**Register totals:** 17 cases -- Verified 2, Efit 1, Conj 6, Risk 7, Retr 1.

<!-- END GENERATED case-index -->

### Register-integrity issues

**Two subject-identity collisions, resolved 2026-08-10 by source check.** In
both cases a register case and an unregistered draft cover the **same person**,
and the registered file carried an incorrect given name.

| Was | Verified | Evidence, fetched 2026-08-10 |
|---|---|---|
| CASE-14: "Carles Morato de Dalmases", Independent (Spain) | **Luis Morato de Dalmases**, CronNet-Holo Initiative | [zenodo.org/records/20443946](https://zenodo.org/records/20443946) and [/19112358](https://zenodo.org/records/19112358) both list this author. (The sources spell the surname with an acute accent; ASCII here per CHARTER.md s 6.) |
| CASE-15: "Cosimo Pellis", Independent (Italy) | **Stergios Pellis** | [SSRN 4003636](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=4003636) -- the record CASE-15 itself cites -- is authored by Stergios Pellis, as is JHEPGC 2023 (DOI [10.4236/jhepgc.2023.91021](https://doi.org/10.4236/jhepgc.2023.91021)) = SCIRP paper id 122814. A search of the phi / coupling-constant literature returns no Cosimo Pellis. |

Names and affiliations are corrected in both files, and each names its draft
counterpart. **Promoting either draft means folding it into the registered
case, not opening a second one for the same subject.**

**COI escalation, unresolved.** CASE-15 records its subject as **Strand III of
the Vasilev-Pellis-Olsen phi-paper** -- a co-author of the maintainer. `COI.md`
COI-excludes the paper's *other* non-maintainer co-author from being a primary
audit subject but not this one. See "The Pellis asymmetry" in `COI.md`; three
readings are recorded there and none is chosen.

**Also open:** **CASE-12's manifest path**
(`cases/CASE-12-g-phi-rank-2-of-394/README.md`) does not exist on disk.

**Fixed while merging `main` (2026-08-10).** The manifest entry added by PR #7
was indented at column 1 instead of column 3, which made `cases.yaml`
**unparseable**, and it claimed id `CASE-10`, already held by the PHI_BIAS
survey. Indentation fixed; the new case renumbered to **CASE-18** with the
original id recorded in its `public_status` so the change is one line to
revert. Both defects are of the class the `case-index` CI job below now
catches.

### Archive coverage is zero (CONTRIBUTING.md s 4)

`CONTRIBUTING.md` s 4 requires every primary-source URL in a CASE file to carry
an archived snapshot (web.archive.org or archive.today). Measured by
[`scripts/check_archive_coverage.py`](scripts/check_archive_coverage.py):

| | |
|---|---|
| CASE files | 22 |
| Distinct URLs cited | 93 |
| **Archive-host URLs anywhere in the register** | **0** |
| `archive_uri` front-matter fields | 0 real, **4 populated but not an archive**, 18 absent |

The four populated fields are the part worth acting on. CASE-14 and CASE-16
repeat `primary_source_uri` verbatim; CASE-13 and CASE-15 point at a different
paper. **A populated field reads as satisfied** -- to a reviewer skimming the
front matter, and to any check that tests for non-emptiness rather than for an
archive host. The checker validates the host for that reason.

`--strict` exits 1 and is deliberately **not** wired into CI: a gate that fails
on every run from day one teaches people to ignore it. Wire it once coverage is
real.

**Snapshots could not be created from the environment that produced this
report.** `web.archive.org` was unreachable: the availability API returned
HTTP 429 to every request (parallel and serial, with delays and a User-Agent),
and the site itself was blocked. Separately, `papers.ssrn.com` and
`www.scirp.org` return HTTP 403 to automated fetches, so two of the venues this
register depends on resist both verification and archiving by script. Closing
this gap needs a human session or a host that those services accept;
`--commands` emits the exact `web.archive.org/save/` calls, one per URL.

Sources: [SSRN 4003636](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=4003636),
[Zenodo 20443946](https://zenodo.org/records/20443946),
[Zenodo 19112358](https://zenodo.org/records/19112358).

---

## Scorecard dashboard

Claim counts per CASE file, machine-readable source in
[`data/scorecard.json`](data/scorecard.json). Label taxonomy in
[`data/labels.json`](data/labels.json). Counts are bulleted top-level
claims inside each inventory section; joint or sub-claims may share a
bullet, so the table is a calibration aid, not a precise inventory.
Label changes are recorded in [`PROMOTION-LEDGER.md`](PROMOTION-LEDGER.md).

| Case | Subject | V | EF | OC | R | HR | Ret | Fpath executable | Reply |
|---|---|---:|---:|---:|---:|---:|---:|---|---|
| [CASE-00](cases/CASE-00-self-audit.md) | self-audit (maintainers) | 13 | 1 | 2 | 2 | 0 | 4 | yes | n/a |
| [CASE-01](cases/CASE-01-savchenko-pointer-architecture.md) | A. Savchenko | 7 | 3 | 4 | 3 | 0 | 1 | partial | pending |
| [CASE-02](cases/CASE-02-stakhov-mathematics-of-harmony.md) | A. Stakhov | 6 | 1 | 2 | 4 | 1 | 0 | partial | pending |
| [CASE-03](cases/CASE-03-el-naschie-e-infinity.md) | M.S. El Naschie | 3 | 0 | 0 | 2 | 3 | 0 | no | pending |
| [CASE-04](cases/CASE-04-petoukhov-matrix-genetics.md) | S.V. Petoukhov | 3 | 2 | 1 | 4 | 0 | 0 | pending | pending |
| [CASE-05](cases/CASE-05-kramer-klimesch-golden-rhythms.md) | Kramer & Klimesch (positive control) | 2 | 2 | 1 | 2 | 0 | 0 | yes | pending |
| [CASE-06](cases/CASE-06-de-groot-economic-cycles.md) | B. de Groot (positive control) | 3 | 1 | 1 | 3 | 0 | 0 | yes | pending |
| [CASE-07](cases/CASE-07-carroll-kaplan-m-planck.md) | Carroll/Kaplan M_pl class * | 0 | 0 | 0 | 3 | 0 | 0 | partial | n/a |
| [CASE-08](cases/CASE-08-vasilev-bnf-equivalence-class.md) | Vasilev BNF (v2.3 self-audit) * | 1 | 0 | 3 | 0 | 0 | 0 | yes | pending |
| [CASE-09](cases/CASE-09-corona-rom-vs-closed-rule.md) | Corona ROM vs closed rule (self-audit) * | 1 | 0 | 3 | 0 | 0 | 0 | yes | n/a |
| [CASE-10](cases/CASE-10-phi-bias-coincidence-scan.md) | PHI_BIAS coincidence survey (self-audit) * | 0 | 0 | 1 | 0 | 0 | 0 | yes | n/a |
| [CASE-13](cases/CASE-13-singh-trace-dynamics.md) | T.P. Singh (trace dynamics) | 1 | 1 | 1 | 1 | 0 | 0 | pending | pending |
| [CASE-14](cases/CASE-14-morato-spectral-triple.md) | L. Morato de Dalmases | 0 | 1 | 1 | 3 | 0 | 0 | pending | pending |
| [CASE-15](cases/CASE-15-pellis-coupling-constants.md) | S. Pellis (co-author) | 0 | 1 | 1 | 3 | 0 | 0 | pending | pending |
| [CASE-16](cases/CASE-16-phi-grid-collaboration.md) | Phi-Grid Project (positive control) | 2 | 0 | 0 | 0 | 0 | 0 | yes | pending |
| [CASE-18](cases/CASE-18-vasilev-tnf-golden-alphabet.md) | Vasilev TNF golden alphabet (self-audit) | 0 | 0 | 0 | 0 | 0 | 0 | yes | n/a |
| **Totals** | **16 cases** | **42** | **13** | **21** | **30** | **4** | **5** | -- | -- |

**Scope of this table.** Counts are produced by
[`scripts/count_labels.py`](scripts/count_labels.py) from the five-label
inventory sections, and written to
[`data/scorecard.json`](data/scorecard.json). All registered case files are covered.
Files under `drafts/` are unregistered and not scored. CASE-12 is absent because its manifest path does not exist on disk
(see the integrity note above the index).

Rows marked **\*** are **not counted**: CASE-07..CASE-10 predate the inventory
structure and record claims in prose sections, so their figures are
hand-assigned and carried forward unchanged. Everything else is machine-counted.

**On trusting this table.** The counter is validated against the six
hand-written rows it replaced and reproduces all six exactly
(`scripts/count_labels.py --validate`). That check exists because the first
version of the counter used a pattern that could not express `[High-risk]` or
`[Risk] (a)`, and **reported 0 where the truth was 3 and 4** -- a label the
pattern cannot match reads as an absence, not as an error. The register uses
four different bullet decorations; a counter that handles only the plainest one
silently under-reports. The qualitative columns (`Fpath executable`, `Reply`)
are not derivable from the files and remain hand-maintained.

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
**Last index update:** 2026-08-10 (v0.7 -- index regenerated from `cases.yaml`:
23 cases, adds CASE-10, CASE-11, CASE-13..CASE-22; the Wave-Loop batch was
renumbered 12->18, 13->19, 14->20, 15->21, 16->22 to clear ID collisions).
