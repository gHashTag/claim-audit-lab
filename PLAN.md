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
| W5 | ~~Two subject-identity collisions~~ **RESOLVED 2026-08-10 by source check.** Both are one subject entered twice; both earlier entries had the wrong given name. Names corrected; **merge decision + COI escalation left to maintainer** | CASE-14/20 = Luis Morato de Dalmases; CASE-15/21 = Stergios Pellis | corrections done, 2 decisions open |
| W6 | `cases/CASE-12-g-phi-rank-2-of-394/README.md` referenced but absent | manifest + README | low |
| W7 | ~~Scorecard unscoreable~~ **CLOSED 2026-08-10.** Counted by `scripts/count_labels.py`, validated 6/6 against the hand-written rows | README, data/scorecard.json | closed |
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
- [x] **P5 / W5** Attempt source verification of the two identity collisions; record the outcome either way.
- [ ] **P6 / W4** Archive snapshots where sources verify.

Each item: run the three gate scripts + `scripts/gen_readme_index.py --check`,
commit, push to the PR branch. Do **not** merge PR #8.

---

## Status log

- **2026-08-10, iteration 3.** Completed P5 against primary sources.
  CASE-14 "Carles Morato de Dalmases / Independent (Spain)" -> **Luis Morato de
  Dalmases / CronNet-Holo Initiative** (Zenodo 20443946 + 19112358, both list
  him). CASE-15 "Cosimo Pellis / Independent (Italy)" -> **Stergios Pellis**
  (SSRN 4003636, the record CASE-15 itself cites, plus JHEPGC 2023
  DOI 10.4236/jhepgc.2023.91021 = SCIRP paperid 122814; no Cosimo Pellis exists
  in this literature). CASE-20 date 2025 -> 2026-03-19. 5 ledger rows.
  **Two decisions deliberately NOT taken autonomously:** (1) merging the
  duplicate pairs -- four files audit two people; (2) re-gating CASE-21 under
  the co-author rule, since CASE-15 records the subject as Strand III of the
  lab's own phi-paper, so CASE-21 audits a co-author while gated as external.
  Also: broke cases.yaml with an unescaped inner quote; the `case-index` CI job
  added in iteration 1 caught it immediately. Residual: CASE-21 still asserts
  country "Greece", unverified.
  Next: P6 (archive snapshots). Note SSRN and SCIRP return HTTP 403 to the
  fetcher; Zenodo works. Archive coverage will be partial and must say so.
- **2026-08-10, iteration 2 (cont).** Closed W7. Wrote
  `scripts/count_labels.py` and regenerated `data/scorecard.json` + the README
  scorecard for all 22 case files on disk. **The first counter was wrong**: its
  pattern could not express `[High-risk]` or `[Risk] (a)` and reported 0 where
  the truth was 3 and 4, which would have shipped a scorecard understating the
  register's risk rows. Caught by validating against the hand-written numbers
  before trusting the output; `--validate` now reproduces 6/6 and is the gate.
  CASE-07..10 marked not-counted (they predate the inventory structure).
  Next: P5 (identity collisions), P6 (archive snapshots).
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
