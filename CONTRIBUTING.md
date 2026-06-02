# Contributing to claim-audit-lab

This file documents the three inbound flows the lab supports:

1. **Subject reply** -- a subject of a CASE file submits a one-page reply.
2. **Factual correction** -- any reader points out a factual error.
3. **New CASE proposal** -- a reader proposes auditing a new subject.

Before contributing, please read `FRAMEWORK.md` (5-label taxonomy),
`CHARTER.md` (binding policy), and `methodology/README.md` (philosophical
scaffold). The framework labels and the symmetric-mirror rule are
non-negotiable.

---

## 1. Subject reply

**Who.** Any author of work that is the subject of an existing CASE file.
**What.** A one-page (~500 words) reply to the lab's audit.
**How.** Open an issue using the **Subject reply** template
(`.github/ISSUE_TEMPLATE/subject-reply.yml`), OR open a PR that adds
content directly under Section 12 of the relevant CASE file.

**Maintainer SLA.** 14 days from issue/PR open to first response. This
mirrors [Science Feedback's reach-out protocol](https://science.feedback.org/process/).

**Inclusion rule.** Subject replies are included **verbatim** under
Section 12 "Subject's reply" of the relevant CASE file. The reply is not
edited for grammar, style, or argument strength. The maintainer may add
a one-line "received via [channel] on [date]" attribution.

**Redaction.** The lab redacts only:
- Banned-word usage directed at named third parties (the lab does not
  reproduce defamation of a non-subject).
- Personal contact information unless the subject explicitly requests
  inclusion.

The lab does not redact substantive criticism of the audit itself.

**Right of reply does not require maintainer agreement.** A subject who
disagrees with a CASE verdict can have the disagreement recorded
verbatim. The verdict and the reply coexist; the reader judges both.

---

## 2. Factual correction

**Who.** Any reader.
**What.** A specific factual error: a wrong URL, a misattributed quote,
a wrong date, a citation that does not support the cited claim, an
algebraic error.
**How.** Open an issue using the **Factual correction** template, OR
open a PR with the fix.

**Maintainer SLA.** 7 days from issue/PR open to merge or decline. A
declined correction includes a written reason in the issue.

**Standard.** Corrections must point at a specific sentence and a
specific source. "I disagree with the verdict" is not a factual
correction -- that goes through the Subject Reply flow or remains a
public disagreement.

---

## 3. New CASE proposal

**Who.** Any reader.
**What.** A proposal that the lab audit a new subject.
**How.** Open an issue using the **New CASE proposal** template.

**Intake filter.** A proposed subject is in scope if:

(a) The subject publishes claims invoking the golden ratio phi,
    Fibonacci/Lucas structure, or related "fundamental constant" framings
    in physics, biology, cosmology, consciousness studies, numeric
    formats, ML/AI, or economics.

(b) The subject has at least one verifiable primary source (peer-reviewed
    paper, preprint with DOI, monograph with ISBN, or self-published spec
    with a stable URL).

(c) The claim has at least one of:
    - explicit empirical content (predicts a measurable quantity),
    - explicit mathematical content (a theorem or identity), or
    - an explicit Fpath stated by the subject.

Subjects whose claims have none of these (no source, no empirical
content, no math, no Fpath) belong in `phi_theorists_catalog.md`
under "fringe-adjacent: cited only by sympathetic outlets", not in a full
CASE file. This filter follows [Wikipedia:Fringe theories](https://en.wikipedia.org/wiki/Wikipedia:Fringe_theories).

**Conflict-of-interest filter.** Proposals naming a current collaborator
of the lab maintainers (currently: Scott Olsen) are declined as primary
audit subjects; their contribution is recorded inside CASE-00 and the
symmetric-mirror sections of related cases. See `COI.md`.

**Maintainer SLA.** 21 days from proposal to accept / decline / queue.

---

## 4. Primary-source archive rule

Every primary-source URL cited in a CASE file MUST also have an archived
snapshot URL (web.archive.org or archive.today). This is the verifiability
discipline drawn from [PubPeer's evidence rule](https://pubpeer.com/static/faq)
and the [Sarkar v. Doe](https://www.aclu.org/cases/sarkar-v-doe-pubpeer-subpoena-challenge)
precedent.

To archive a page:
- Visit `https://web.archive.org/save/<url>` for a one-shot snapshot.
- Or visit `https://archive.today/?url=<url>` (preserves more JS state).
- Record the resulting archive URL alongside the primary URL in the CASE
  file's Section 11 "Sources".

`scripts/archive-helper.md` (planned) will collect the canonical commands.

---

## 5. PR checklist

Every PR to this repository MUST pass:

- [ ] CI banned-word check passes (`.github/workflows/banned-words.yml`).
- [ ] CI symmetric-mirror check passes (every new CASE file has Section 9).
- [ ] CI ASCII-only check passes (no non-ASCII outside quoted blocks).
- [ ] If a CASE file: every primary-source URL has an archive snapshot URL.
- [ ] If a CASE file: every [Verified] claim cites algebra or harness.
- [ ] If a CASE file: every [Open conjecture] claim states a Fpath.
- [ ] If a CASE file: Section 9 "Symmetric mirror" is non-empty.
- [ ] Promotion ledger updated if a label changed (`PROMOTION-LEDGER.md`).

The PR template (`.github/PULL_REQUEST_TEMPLATE.md`) reproduces this list
as a fill-in checklist.

---

## 6. Reviewer guidelines

(For maintainers and future external reviewers.)

When reviewing a CASE file PR:

1. **Verify the symmetric mirror first.** If Section 9 is empty, decline
   immediately with a pointer to FRAMEWORK.md s "Symmetric mirror".
2. **Verify [Verified] credit goes to the subject first.** A CASE file
   that has no [Verified] section for a subject who has any [Verified]
   claims is rejected (CHARTER.md s 1).
3. **Verify primary-source URLs are reachable.** If a URL 404s, ask the
   contributor for the archive snapshot URL.
4. **Verify no banned words and no ad hominem.** The CI catches the
   word list; the reviewer catches the structure.
5. **Verify the Fpath is actionable.** "This could in principle be
   falsified by future data" is not actionable. "If experiment X with
   tolerance Y fails to observe Z by date W" is actionable.
6. **Verify no membership labelling.** Do not use the demarcation tokens listed in `FRAMEWORK.md` (inside the fenced block);
   no "fringe author" used as an epithet. The labels grade evidence,
   not membership (C1).

---

## 7. Code of conduct

This repository follows a simple rule: criticise claims, never people.

- Comments on subjects are out of scope. Comments on claims are in scope.
- Disagreement with a verdict is welcome through Section 12 (subject) or
  the factual-correction issue flow (anyone).
- Personal attacks against any contributor, subject, or maintainer are
  removed without warning.

Repeat violations result in a block. This is the only enforcement
mechanism the lab uses; everything else routes through the framework.

---

**Maintainer:** Dmitrii Vasilev (`@gHashTag`).
**Last update:** 2026-06-02.
