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
- **Banned words in entries:** breakthrough, revolutionary, first-ever,
  Nobel, world-first, "proves" used non-logically, pseudoscience, crank,
  numerology (as a slur). State labels, not insults.
- **Corrections welcome.** Open a PR or an issue. If a subject of a case file
  documents that we misread their claim, the case is updated and the prior
  version is preserved in `archive/`.
- **Right of reply.** Subjects of any CASE file may submit a one-page reply;
  it is included verbatim in the case file under "Subject's reply" with a
  link to the source.

See [`CHARTER.md`](CHARTER.md) for the full text.

---

## Index of cases

| ID       | Subject                           | Domain                 | Status   |
|----------|-----------------------------------|------------------------|----------|
| CASE-00  | self-audit (lab maintainers)      | numeric formats / ML   | draft    |
| CASE-01  | Pointer Architecture v9.0         | consciousness / dark matter | draft |
| ...      | (more cases pending; see queue)   |                        |          |

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
**Last index update:** 2026-06-02.
