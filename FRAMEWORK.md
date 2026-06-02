# The Five-Label Claim-Status Framework

This is the only normative document in the repository. Every CASE file must
classify every claim into one of these five labels, with no others. No new
labels may be invented for a single case; if a claim does not fit, it goes to
the closest label and the boundary case is noted in prose.

---

## [Verified]

A claim is [Verified] iff at least one of:

(a) **Exact-by-construction.** The claim is an algebraic identity that can be
    re-derived from definitions in a few lines. Example: `phi^2 + phi^-2 = 3`
    is [Verified] (Lucas L_2 = 3, since phi is a root of x^2 = x + 1).

(b) **Deterministically measured by a public reproducible harness.** The
    harness has a frozen seed, frozen config, a sha256 of outputs, and a
    public test script that exits non-zero on any deviation. The claim is
    [Verified] FOR THE HARNESS OUTPUT ONLY, never for the metaphysical
    interpretation the harness was built to support.

**Anti-pattern.** A harness verifying that `Phi_PA(observer) = 50000` is
[Verified] for the integer 50000. It is NOT [Verified] that Phi_PA measures
consciousness. Promoting (b) to a metaphysical claim is the most common
abuse of the [Verified] label.

---

## [Empirical fit]

A claim is [Empirical fit] iff:

- It matches data (chi^2, accuracy, correlation, AIC/BIC, etc.),
- AT LEAST ONE parameter was chosen post-hoc to make the fit work,
- A pre-registered held-out test is either absent or pending.

A "post-hoc" parameter includes: any parameter inside a fitted model; any
composite proxy whose definition was chosen after seeing the data; any cut
on the data range; any choice of which model variant to advertise as the
headline result.

**Calibration.** An [Empirical fit] with k free parameters competing against
a baseline with k' < k free parameters is automatically [Risk] unless model
selection is reported at MATCHED k.

**Promotion path.** [Empirical fit] -> [Verified] requires (a) full
pre-registration of the prediction, (b) replication on a held-out dataset
the authors did not see at fit time, (c) the held-out test confirms the
prediction within the pre-registered tolerance.

---

## [Open conjecture]

A claim is [Open conjecture] iff:

- It is plausible and motivated by the rest of the programme,
- It is not yet supported by [Verified] or matched-baseline [Empirical fit]
  evidence,
- **It carries a stated falsification path (Fpath).** This is mandatory.

The Fpath is a one-sentence statement of the form: "this claim is falsified
if X is observed", where X is a specific, in-principle-observable event.

**Without an Fpath, the claim is not [Open conjecture]. It is [Risk] (see
below).** This is the most important rule in the framework. Quoting
Savchenko 2026-05-19 from outside the lab and applied here as policy: *"A
falsifier that nobody can act on is decorative."* The Fpath must be
actionable: a specific experiment, a specific dataset, a specific
arithmetic check.

---

## [Risk] / [High-risk]

A claim is [Risk] iff at least one of:

(a) **No Fpath stated.** A claim that aspires to be a conjecture but has no
    stated falsifier defaults to [Risk], not [Open conjecture].

(b) **Look-elsewhere correction missing.** "phi appears in X" is [Risk]
    unless the author has bounded the search space and shown that the
    appearance survives multiple-testing correction.

(c) **A control programme matches.** If a plausible non-phi alternative
    explains the data with comparable or fewer free parameters, the
    phi-specific reading is [Risk] until the control is ruled out.

(d) **Venue weakness.** Self-published only, journal with documented prior
    scandal, or a venue with no peer review for the specific claim. This is
    not a character judgment of the author; it is a calibration of the
    evidence available.

[High-risk] is reserved for claims that fail TWO or more of (a)-(d).

---

## [Retracted]

A claim is [Retracted] iff the author, OR this lab acting in good faith on
the author's behalf, has explicitly withdrawn it. A [Retracted] claim is
never to be cited again as evidence. It is recorded permanently so that the
retraction itself is on the public ledger.

A [Retracted] claim does not damn the surrounding programme. It is, on the
contrary, a Popperian success: a research programme that retracts is a
research programme that learns.

---

## Mapping from external taxonomies

When a programme uses its own claim-status taxonomy, the case file maps it
explicitly. Two common mappings:

**Savchenko three-tier (sixth/CLAIMS.md):**

| Author label | Our label |
|--------------|-----------|
| Tier 1 (proved-by-running-the-code) | [Verified] for the harness only |
| Tier 2 (demonstrated-by-construction) | [Empirical fit] on synthetic data |
| Tier 3 (philosophical conjecture under empirical falsifier) | [Open conjecture] with stated Fpath |

**No taxonomy stated:**

Default to the most permissive reading consistent with the author's
strongest published wording. Promote only when the author meets our
[Verified] / [Empirical fit] / [Open conjecture] requirements.

---

## Banned words (in any CASE file)

The following words MUST NOT appear in a CASE file (except inside a verbatim
quote from the subject's own work, in which case they remain verbatim and
are not silently edited). The list is inside a fenced block so the CI scanner
skips it:

```
crank
pseudoscience
numerology (as a pejorative)
breakthrough
revolutionary
first-ever
world-first
Nobel (as a rhetorical amplifier)
proves (used non-logically)
```

Use the five labels instead. They carry all the necessary epistemic force
and require no insult.

---

## Symmetric mirror (mandatory section in every CASE)

Every CASE file must contain a section titled "Symmetric mirror" that
classifies one or more comparable claims from the lab's own work
(`gHashTag/trios-trainer-igla`, `gHashTag/goldenfloat-preprint`,
`gHashTag/phi-paper`) under the same framework. If the subject's claim is
labelled [Open conjecture], a comparable claim from the lab's own work is
also labelled and the two are placed side-by-side. This is non-negotiable.

If a CASE file has no symmetric mirror, the case is rejected from the
register until the mirror is added. This rule is what distinguishes the lab
from a debunking site.

---

## Promotion ledger

Promotions and demotions between labels are recorded with a date, a one-line
reason, and the commit hash that records the change. The promotion ledger is
maintained in [`PROMOTION-LEDGER.md`](PROMOTION-LEDGER.md). Once a label is
assigned, it does not change silently.

---

**Last update:** 2026-06-02.
