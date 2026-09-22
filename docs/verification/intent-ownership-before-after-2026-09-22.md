# Intent and simplicity ownership — before/after replay, 2026-09-22

Question: on one real build, does every finding the to-be-deleted checks raised have an
exorcise finding after? This is the run the [coverage matrix](intent-ownership-coverage-2026-09-22.md)
defers to. Subject: studious build `build/pin-audit-model-202609082320` (#136's
reproducibility half, m1-gate-build-cost), replayed into a scratch repo as base 4794c13 →
head 3994ff7 (replay e276594 → 543a1e5): 8 files, +152/-38, 14 hunks, 0 added or deleted,
6 new exports (all pytest functions), 0 new dependency lines. The diff and tripwire line
match the recorded 2026-09-08 exorcise exactly. One task, one PLAN.md, no design doc
(the design gate was skipped by ruling), no Amendments block.

- **Before**: the checks gauntlet#89 and studious#442 delete. plan-drift (run from
  `~/Projects/studious/scripts/plan-drift`), the Inspector's contract-match lens, and
  product-reviewer, architecture-auditor and code-auditor held to their deletable
  scope. One dispatch each.
- **After**: exorcist's four lanes at 55a1174 (PR #12), each reply validated by
  `scripts/report.py findings`, then merged with `report.py merge` (scope `--base HEAD~1`
  in the replay, `includes_worktree: false`, 14 hunks).
- **Recorded**: the build's own history. Its exorcise report (14 traced, 3 rewritten,
  3 held), 2 audit rounds (12 fingerprints, 1 Critical), 7 carried acceptance findings,
  and #400-#403 on studious for the finding bodies.

## Counts

| Side | Lane | Findings |
|---|---|---|
| before | plan-drift | 1 (`do-path-untouched`), 0 `out-of-plan-file` |
| before | Inspector, contract match | 6 CONCERN, 0 DEFECT |
| before | product-reviewer | 9 (1 critical, 6 important, 2 track) |
| before | architecture-auditor | 4 |
| before | code-auditor | 3 |
| after | trace | 2 holds (1 `behavior change`, 1 `unmet claim`) |
| after | abstraction | 6 (3 inline, 2 reuse, 1 hold) |
| after | threshold | 0 |
| after | deletion | 11 (9 delete, 2 hold) |
| after | merged | 14 to apply, 5 held, `out_of_intent_files` 0 |

Dedup merged nothing. trace-1 (`agents/doc-auditor.md:5`) and deletion-1
(`tests/test_dispatch_telemetry.sh:70`) are the same defect at two loci, so the PR body
would show it twice.

## out_of_intent_files vs out-of-plan-file

0 and 0. All 8 changed files are named in `Do:`, so the matrix's `Read first:` and
PLAN.md caveats never fired, and the tracer reverted 0 of 14 hunks. The recorded
exorcise traced the same 14 and reverted 0.

## Mapping — before findings

`LOST (kept)`: no exorcist rule catches it, and it sits in a `keep` row or a named gap,
so a lane gauntlet#89 or studious#442 keeps must still catch it. `LOST → rule`: it was
exorcist's to catch, and a rule has been added since (see below).

| Before | After | Note |
|---|---|---|
| plan-drift-1 | FALSE-POSITIVE | `scripts/run_ab_eval.py` is named inside the A/B rule the change keeps, not as a file to edit. The tracer rightly emits no unmet claim for it |
| inspector-1 | LOST (kept) | The alias fallback was taken on "undocumented", not "rejects an ID". Claim 3 as derived accepts that reason, and no grep settles whether undocumented means rejected. Contract-match gap |
| inspector-2 | LOST → rule | DESIGN.md omits the full-ID rule that claim 6's "matches CONTRIBUTING.md" requires. Row: specced capability dropped (`covered`) |
| inspector-3 | partial: deletion-2, -3, -4, trace-1 | Every contradicting site is flagged, but the overclaiming sentence at CONTRIBUTING.md:155 is not |
| inspector-4 | trace-1, deletion-1 | The telemetry test breaks. trace-1 ran it: FAIL, expected `inherit` |
| inspector-5 | LOST → rule | CONTRIBUTING.md:118 calls the four local agents "merge-blocking". PRODUCT.md:28-30 says the judges are gauntlet's |
| inspector-6 | LOST → rule | epic-driver.js:1075 "opus (reserved … for verdict-compiling judgment)" is now contradicted by five producer pins |
| product-reviewer-1 | trace-1, deletion-1 | = inspector-4 |
| product-reviewer-2 | LOST → rule | = inspector-5 |
| product-reviewer-3 | LOST (kept) | The tests assert presence, not the exact value. Claim 9 asks only for presence, so this is test adequacy: technicality gap, test-auditor |
| product-reviewer-4 | LOST (kept) | An agent with no `model:` key passes. Claim 9(a) is met literally. Technicality gap |
| product-reviewer-5 | partial: deletion-2, -3, -4, trace-1 | = inspector-3 |
| product-reviewer-6 | LOST → rule | = inspector-2 |
| product-reviewer-7 | deletion-8, deletion-9 | The eslint rule prose still offers the suppression the new test bans |
| product-reviewer-8 | LOST → rule | = inspector-6 |
| product-reviewer-9 | LOST (kept) | The prose guard matches only the old wording. Technicality gap |
| architecture-1 | deletion-11, abstraction-4 | Line-scan tests beside the eslint rule, and overlapping each other |
| architecture-2 | abstraction-6 | MODEL_LINE beside `run_ab_eval.MODEL_LINE_RE`, held as a behavior change |
| architecture-3 | abstraction-1, -2, -3 | The same three inlines the recorded exorcise applied |
| architecture-4 | deletion-10 | The duplicated assertion. Its exact-value half is product-reviewer-3 |
| code-1 | abstraction-6 | The frontmatter-scoping difference code-1 names is not in abstraction-6's evidence |
| code-2 | deletion-11, abstraction-4 | = architecture-1 |
| code-3 | deletion-10, abstraction-1, -2 | |

## Mapping — recorded findings

| Recorded | After | Note |
|---|---|---|
| exorcise rewrite `_agent_files` | abstraction-1 | |
| exorcise rewrite `FORMERLY_INHERIT` | abstraction-2 | |
| exorcise rewrite `NON_JUDGE_DISPATCH_LABELS` | abstraction-3 | |
| exorcise held `MODEL_LINE` (→ #402) | abstraction-6 | held again, as a behavior change |
| exorcise held tests/ab/README.md:158 | deletion-3 | was held, now a delete |
| exorcise held reference/telemetry-format.md:62 | deletion-2 | was held, now a delete |
| audit R1 `code-auditor/telemetry-test-inherit-case` (Critical) | trace-1, deletion-1 | the recorded exorcise missed it |
| audit R1 `test-auditor/pin-tests-presence-not-tier` | LOST (kept) | = product-reviewer-3 |
| audit R1 `product-reviewer/driver-pin-guard-value-blind` | LOST (kept) | = product-reviewer-3 |
| audit R1 `doc-auditor/eslint-rule-doc-dead-escape-hatch` | deletion-8 | |
| audit R1 `doc-auditor/ab-readme-baseline-inherit` | deletion-3 | |
| audit R1 `product-reviewer/ab-arm-baseline-inherit` | deletion-4 | |
| audit R1 `product-reviewer/driver-alias-not-id` | LOST (kept) | = inspector-1 |
| carried `architecture-auditor/pins-on-undispatched-mirror-agents` (#400) | LOST (kept) | a design call resting on the plan's `Why now:` and `Not here:`, which exorcise is not handed. Its CONTRIBUTING.md:118 symptom is inspector-5 |
| carried `prompt-auditor/full-id-on-mirror-agents` (#400) | LOST (kept) | prompt-auditor is not deleted |
| carried `code-auditor/file-level-disable-escapes-guard` (#402) | LOST (kept) | test adequacy |
| carried `code-auditor/opus-reserved-comment-contradiction` (#401) | LOST → rule | = inspector-6 |
| carried `code-auditor/contributing-merge-blocking-claim` (#400) | LOST → rule | = inspector-5 |
| acceptance `id-pins-on-mirror-files` (#400) | LOST (kept) | = pins-on-undispatched-mirror-agents |
| acceptance `opus-pins-cost-direction-unstated` (#401) | LOST (kept) | product judgment |
| acceptance `opus-pin-no-fallback` (#401) | LOST (kept) | product judgment |
| acceptance `nothing-carries-inherit-overstated` (#403) | partial | = inspector-3. The instance #403 names, `skills/build/SKILL.md:255` `inherited: <model>`, is doc accuracy, which doc-auditor keeps |
| acceptance `design-md-omits-model-id-rule` (#403) | LOST → rule | = inspector-2 |
| acceptance `guard-misses-absent-model-key` (#402) | LOST (kept) | = product-reviewer-4 |
| acceptance `opus-5-id-resolution-unverified` (#403) | LOST (kept) | a runtime observation, not a diff fact |

## LOST items and what changed

Three distinct defects were exorcist's to catch and no lane caught them. Each now has a
rule, re-run by hand against this case:

- **A claim that one file matches another** (inspector-2, product-reviewer-6,
  `design-md-omits-model-id-rule`). New reverse-roll-call bullet,
  `agents/intent-tracer.md:53-54`: grep the first file for a rule the other states.
  CONTRIBUTING.md:120-123 states the full-ID rule, and `grep -c claude-opus-5 DESIGN.md`
  gives 0, so this is an `unmet claim` on claim 6. Covered.
- **A reached hunk whose prose contradicts a context doc** (inspector-5,
  product-reviewer-2, `contributing-merge-blocking-claim`). `spec conflict` in
  `agents/intent-tracer.md:63-68` now reaches it. CONTRIBUTING.md:118 "the four
  merge-blocking changeset auditors" against PRODUCT.md:28-30 "judge lanes are dispatched
  from `gauntlet` … never the judges" gives a hold on CONTRIBUTING.md:118, claim 7.
  Covered, provided the tracer reads PRODUCT.md, which the rule names.
- **A comment that states a rule about a value the diff adds** (inspector-6,
  product-reviewer-8, `opus-reserved-comment-contradiction`). New §1 bullet,
  `agents/deletion-scout.md:24-26`. The lane grepped for the retired values
  (`unpinned`, `inherit`) but not for the added one. `grep -n opus workflows/epic-driver.js`
  hits :1075, and the five new producer pins break its "reserved for verdict-compiling"
  rule, so the parenthetical is a delete. Covered. The rule also names what deletion-2
  to -7 already did unprompted.

The other LOST items are test adequacy (the technicality gap), product and design calls
that rest on `Why now:` / `Not here:`, which the Step 3 handoff leaves out, and runtime
facts no grep shows. Two gaps the matrix did not name yet, both for studious#442:

- **The intent excludes `Why now:` and `Not here:`.** inspector-5 and
  pins-on-undispatched both judge the diff against the plan's goal, not its `Do:`.
- **A claim that branches on a fact** ("ID if `agent()` accepts one, else `opus`"). The
  tracer checks that a reason is recorded, not that the reason settles the branch
  (inspector-1).

## Verdict

No finding lost: **no**, as measured. inspector-2 / product-reviewer-6 sits in a `covered`
row (specced capability dropped), and no after lane caught it. 10 of 23 before findings
are LOST and 2 are partial. Six of the ten are three defects exorcist should own, and
the rules above now catch them when re-run by hand. The other four belong to lanes the
deletions keep: test-auditor, product-reviewer's own judgment, and the Inspector's
technicality lens.

What the after side gained: the Critical telemetry break the recorded exorcise missed
(trace-1, running the test), an unmet claim 9(b) over 31 non-judge dispatches (trace-2),
and 8 stale-text deletes (deletion-2 to -9), two of them the recorded exorcise's holds. 

## Re-run after the rule edits

intent-tracer and deletion-scout re-ran on the same replay with the edited prompts.

| LOST item | Rule | Re-run |
|---|---|---|
| inspector-2 / product-reviewer-6 (DESIGN.md omits the full-ID rule, claim 6) | intent-tracer: a claim that one file matches another | caught — `unmet claim`, claim 6 |
| inspector-5 / product-reviewer-2 (CONTRIBUTING.md:118 vs PRODUCT.md:28-30) | intent-tracer: reached-hunk spec conflict | caught — `spec conflict` at CONTRIBUTING.md:118-124, claim 7 |
| inspector-6 (`epic-driver.js:1075` "opus reserved" comment) | deletion-scout: stale rule about an added value | caught — `delete` at :1075-1076 |

The three rules fire, so nothing assigned to exorcist stays LOST. The re-run exposed variance
the first run hid: neither re-run lane raised the Critical telemetry break
(`tests/test_dispatch_telemetry.sh:70`), which trace-1 and deletion-1 caught the first time.
Both lanes grepped the line and dismissed it without reading it. deletion-scout found 7
findings against the first run's 11. One lane run cannot yet vouch for a finding that
gauntlet would otherwise have re-raised; the next real build is the check.

The #13 fix and its 3-run measurement: [lane-variance-2026-09-22.md](lane-variance-2026-09-22.md).
