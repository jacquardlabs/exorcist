# Lane variance — deterministic leads, 3 runs, 2026-09-22

Continues [Re-run after the rule edits](intent-ownership-before-after-2026-09-22.md#re-run-after-the-rule-edits).
Problem (#13): on the same replay, run 1's intent-tracer and deletion-scout raised the
Critical telemetry break (`tests/test_dispatch_telemetry.sh:70`, which expects `inherit`
for an agent the diff pins), and the re-run's did not. Both lanes grepped the line and
dismissed it without reading it, and gauntlet#89 and studious#442 delete the checks that
would otherwise re-raise it.

## Fix

A new `scripts/leads.py` (7b45bfa). §2 runs it after `tripwires.py` and writes
`<tmp>/leads.json`. It lists each value the diff retires and every whole-word reference
to it outside the changed files, test files first. §3 hands the path to intent-tracer,
abstraction-hunter and deletion-scout, and each lane file now says to open and read every
test lead rather than judge it from its grep line. threshold-salter is untouched.

A value is retired when a `-` line drops it and no `+` line anywhere in the diff adds the
same kind back: a yaml `key: value` pair, a quoted or backticked literal, or a code
identifier. Bare tokens would have lost `inherit`, which the `+` side adds back 22 times as
prose in CONTRIBUTING.md, DESIGN.md and test_model_pins.py. Prose files and comment lines
contribute only backticked literals and `key: value` pairs, tokens under 4 characters and
keywords are dropped, and every filter and cap reports a count.

On the replay (diff.patch against head 543a1e5) it emits one value, `inherit` (yaml, from
`agents/{code-auditor,doc-auditor,frontend-reviewer,test-auditor}.md:5`): 22 references,
20 shown, 2 non-test references dropped by the per-value cap of 20. 9 of the 20 are test
references. Filtered: `still_added` 22, `short` 1, `keyword` 0, `unreferenced` 0. The
telemetry assertion is a lead, ranked 3rd: `tests/test_dispatch_telemetry.sh:73`
`check "model: inherit recorded verbatim" "inherit" ...`, with the `:70` comment 8th.
`:168` ("inherits") is left out by the whole-word match. `leads.json` was byte-identical
across the three runs.

## Measurement

Round 1, three runs of intent-tracer and deletion-scout on the same replay, each reply
validated by `report.py findings` (exit 0). abstraction-hunter was not run. Leads are
references opened of the 20 listed.

| Run | Caught | By | intent-tracer findings | leads | deletion-scout findings | leads |
|---|---|---|---|---|---|---|
| r1-1 | yes | intent-tracer, deletion-scout | 1 | 9/20 | 6 | 9/20 |
| r1-2 | yes | intent-tracer, deletion-scout | 1 | 14/20 | 5 | 20/20 |
| r1-3 | yes | intent-tracer, deletion-scout | 1 | 20/20 | 6 | 15/20 |

The same two findings every run. intent-tracer: a `behavior change` hold on
`agents/doc-auditor.md:5`, claim 1, with `:73` as evidence and a `next` that updates
`:70-73` (`:70-74` in r1-2). deletion-scout: a `delete` on
`tests/test_dispatch_telemetry.sh:70-73` (`:70-74` in r1-2), citing the `:73` lead.
intent-tracer read all 9 test leads every run. The rest of deletion-scout's list was
stable too: the three `unpinned` comments in `epic-driver.js` (:2512, :2531, :3554) and `tests/ab/README.md:158`
in all three runs, `test_epic_appetite_canary.py:405` in r1-1 only, and
`test_model_pins.py:20` in r1-3 only. Artifacts: the scratchpad `replay-run/runs/r1-{1,2,3}/`.

## Verdict

Done means, first item: the `tests/test_dispatch_telemetry.sh:70` break is raised in
**3 of 3** runs, by both lanes each time. Before the leads step, it was 1 of 2. The
second item is open: neither gauntlet#89 nor studious#442 cites this issue yet.

Noise cost: intent-tracer read and cleared 8 of the 9 test leads each run.
`test_run_ab_eval.py:26` and `:147` use their own inline fixture,
`tests/ab/arms/model-drop-136.json:3` is an arm name, and the other five use "inherit" as
an English word. r1-2's notes do not name `:70`, and r1-3 cleared it as prose while
deletion-scout's range covered it. So the cost was eight cleared reads per intent-tracer run
for one real break. One non-test lead, `tests/ab/README.md:158`, became a
deletion-scout finding every run.

Known gaps: `key: value` lines in `.md` files are read as YAML even outside frontmatter,
and numeric values (a retry limit changed from 3 to 5) are never leads, since a token needs
a letter.
