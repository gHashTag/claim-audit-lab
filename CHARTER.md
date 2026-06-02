# claim-audit-lab Charter

This document is the binding policy for the repository. It is more
restrictive than the framework and exists to keep the lab from sliding into
a debunking site, a personal grudge log, or a numerology-of-numerology
project.

---

## 1. Subjects are not enemies

Subjects of CASE files are authors of published work. They are not adversaries
to be defeated. The lab's product is calibration of claims, not character
verdicts.

- A CASE file that reads as a takedown is rejected.
- A CASE file with no [Verified] claims credited to the subject when the
  subject has any is rejected.
- A CASE file with no symmetric mirror against the lab's own work is
  rejected (per FRAMEWORK.md).

---

## 2. Sources are mandatory

Every claim about a subject must have a source URL fetched on a specific
date. The URL goes in the case file. If a quote cannot be sourced, it does
not appear.

When primary sources are paywalled or otherwise unfetched at audit time, the
case file says so explicitly and uses the closest verified secondary source,
clearly labelled.

---

## 3. Right of reply

Any subject of a CASE file may, at any time, submit a one-page reply. The
reply is included verbatim in the case file under a "Subject's reply"
section, with a link to the source from which the reply was received (email
thread archive, public statement, etc.). The reply is not edited.

If a subject objects to a specific characterisation, the maintainers will
either correct the case file or include the objection verbatim. The default
is to correct.

---

## 4. No ad hominem, no insult, no mind-reading

The lab classifies claims, not people. The framework labels are sufficient
vocabulary. The banned words list in FRAMEWORK.md is enforced.

Specifically forbidden in any CASE file:

- Claims about a subject's motives, mental state, sincerity, or intelligence.
- Claims about a subject's career trajectory ("once was a serious scientist,
  now ...").
- Claims about a subject's commercial interests except as factually relevant
  to a specific claim (e.g., "the subject markets a product based on this
  claim" with a source URL).
- Editorial adjectives ("absurd", "ridiculous", "obvious").

---

## 5. Symmetric mirror is non-negotiable

Every CASE file contains a symmetric mirror section that classifies a
comparable claim from the lab's own work under the same framework. This is
the structural defence against the lab becoming a one-sided weapon.

CASE-00 is the global self-audit and is updated whenever the lab's own
claims change status.

---

## 6. English + ASCII only

All public artefacts in this repository are English + ASCII only. Cyrillic
or other non-ASCII text is only permitted inside verbatim quotes from
subjects, in which case the original-script quote is followed by an
ASCII transliteration and an English translation.

---

## 7. Banned-word CI

A CI check on every PR scans all touched files for the banned-word list in
FRAMEWORK.md. PRs that fail the check are blocked. The CI rule is in
`.github/workflows/banned-words.yml` (added in the bootstrapping phase).

---

## 8. Promotion ledger discipline

Every label change is recorded in PROMOTION-LEDGER.md with date, reason, and
commit. Labels do not change silently.

---

## 9. The lab audits itself

CASE-00 is the global self-audit of the maintainers' own work
(`gHashTag/trios-trainer-igla`, `gHashTag/goldenfloat-preprint`,
`gHashTag/phi-paper`). It is treated with the same rigour as any other case
file. The self-audit is updated on the same cadence (whenever a claim
changes status) as the external cases.

If the maintainers' own work is found to be in worse epistemic shape than a
subject of an external CASE, this is recorded plainly in CASE-00, and the
external CASE notes the comparison.

---

## 10. Failure modes the lab is designed to avoid

- **Becoming a debunking site.** Prevented by the symmetric-mirror rule and
  the [Verified]-credit-to-subject rule.
- **Becoming a personal grudge log.** Prevented by the no-ad-hominem rule,
  the right-of-reply rule, and the no-mind-reading rule.
- **Becoming a numerology-of-numerology site.** Prevented by the source URL
  rule and the requirement that every quote be from the subject's own
  published work.
- **Quiet relabelling under pressure.** Prevented by the promotion-ledger
  discipline.

---

**Last update:** 2026-06-02.
