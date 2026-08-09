# Autonomous improvement plan -- claim-audit-lab

Working branch `claude/modest-williams-631991`, PR #8. This file is the loop's
durable state: the scratchpad does not survive a session (lesson recorded in the
`fpga-income` skill), so plan and status live in the repo.

**Owner discipline carried into this work** (from the publication stop-rule):
never assert a number, theorem or source that is not measured or derivable; when
a thing is unverifiable, label it and say so; a comparison whose control is
broken is not a comparison.

---

## Weakness inventory (what is actually wrong, ranked)

| # | Weakness | Evidence | Severity |
|---|---|---|---|
| W1 | Batch is written as competitive analysis, not audit: `Threat level:` ratings, "Most dangerous institutional competitor", "red flags", "Numerological", "lends credibility" | 7 files, greppable | **blocks review** (CHARTER s1/s4, reviewer guideline 6) |
| W2 | No five-label inventory sections; claims sit in an assessment table with verdicts like "Plausible"/"Absent" | CASE-11, 17-22 | **blocks review** (reviewer guideline 2 -- CASE-11's subject has [Verified]-class claims with no [Verified] section) |
| W3 | CASE-00 [Retracted] inventory has 1 entry, but the lab's own record documents 7 claims withdrawn in one night (2026-08-10) plus 12 self-caught defects | `fpga-income` skill vs CASE-00 s 8 | **high** -- every symmetric mirror written this session cites the thin inventory |
| W4 | No archive snapshot URLs | CONTRIBUTING.md s 4 mandates them | medium (needs network + source verification) |
| W5 | Two subject-identity collisions unresolved | CASE-15/21 (SCIRP 122814), CASE-14/20 (Zenodo 19112358) | medium -- a duplicate subject means two mirrors audit one claim |
| W6 | `cases/CASE-12-g-phi-rank-2-of-394/README.md` referenced but absent | manifest + README | low |
| W7 | Scorecard unscoreable, `data/scorecard.json` covers CASE-00..06 only | README | low, blocked on W2 |
| W8 | Gates not wired to the generator; index drift can return | `.github/workflows/` | low |

**Root cause of W1+W2:** the batch was produced by a competitive-analysis pass
("Wave Loop 9/10") and filed into an audit register without conversion. W5 is
the same root cause -- subject identity was never checked against entries the
register already held.

---

## Decomposed plan

- [x] **P0** Clear the two failing CI gates (ASCII + symmetric mirror), register the batch, generate the index. *Done, PR #8, all gates green on the runner.*
- [x] **P1 / W1** Remove competitive framing from all 7 files; replace threat ratings with framework-based evidence calibration.
- [x] **P2 / W3** Expand CASE-00 with the lab's real documented record: 7 withdrawn claims (2026-08-10), the surviving theorems, the measured working point. Append PROMOTION-LEDGER rows.
- [x] **P3 / W2** Add five-label inventory sections (4-8) to the 7 files, converting the assessment tables. Unblocks W7.
- [x] **P4** Wire `gen_readme_index.py --check` into CI as a fourth job.
- [ ] **P5 / W5** Attempt source verification of the two identity collisions; record the outcome either way.
- [ ] **P6 / W4** Archive snapshots where sources verify.

Each item: run the three gate scripts + `scripts/gen_readme_index.py --check`,
commit, push to the PR branch. Do **not** merge PR #8.

---

## Status log

- **2026-08-10, iteration 2.** Completed P3: all 7 files restructured to the
  template (sections 1-11), assessment tables converted to five-label
  inventories with FRAMEWORK.md (a)-(d) reasons cited per entry. CHARTER s 1
  credit rule now satisfied -- CASE-11 (3), CASE-17 (3), CASE-19/21/22 (1 each)
  carry [Verified] entries crediting the subject first; CASE-18 and CASE-20
  state explicitly why theirs are empty and that the section is filled first if
  a claim is supplied. Reviewer guideline 2 no longer grounds a rejection.
  Next: W7 (scorecard, now countable), then P5/P6.
- **2026-08-10, iteration 1 (cont 2).** Completed P4: `case-index` added as a
  fourth CI job running `gen_readme_index.py --check`. Index drift can no
  longer reach main silently.
- **2026-08-10, iteration 1 (cont).** Completed P2: CASE-00 s 4a adds 9
  [Verified] entries (Z[phi] closure, accuracy law, diagnostic theorem, Kraft
  bound T12, regime-radix T13, exact taper laws, area law, trade-curve
  prediction); s 8a adds the seven withdrawn silicon claims R1-R7 plus three
  withdrawn headline results; s 8b records the common mechanism. 19 ledger rows
  appended. Mirror table and audit summary updated. Next: P3 (five-label
  inventories in the 7 files), which unblocks the scorecard.
- **2026-08-10, iteration 1.** Read the owner stop-rule. Armed hourly loop.
  Built this plan. Completed P1: removed `Threat level:` ratings from 7 files,
  removed reputation and motive commentary, reframed Section 3 from
  "Differentiation from Trinity" to a stated-basis comparison and Section 4 from
  "Risk Assessment" to framework-based evidence calibration.
