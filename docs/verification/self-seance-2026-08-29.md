# Séance + exorcise on exorcist itself — v0.4.0 (d4ffd4e), 2026-08-29

The first release, surveyed by its own séance. 1,451 lines of Python across 8 files
plus 12 command and agent prompts. Wall clock 12 min (opus lanes). Register:
[`docs/exorcist/seance-2026-08-29/register.md`](../exorcist/seance-2026-08-29/register.md).

**Phase 0.** sizes, churn, hotspots, ruff, ast-grep, jscpd ran; knip and depcruise
skipped (no JS/TS), scc (not on PATH). jscpd found 0 clones at its 50-token floor —
every duplicate-lane ghost rests on reads and greps.

**Phase 1.** 21 ghosts, 52 concepts, all four lanes. Seven approved and worked with
`/exorcist:exorcise <register> G-12,G-18,G-13,G-01,G-08,G-09,G-10`:

| Ghost | Banishment | Concepts |
|---|---|---|
| G-12 `${CLAUDE_PLUGIN_ROOT}` fallback clause pasted into 8 agents | clauses dropped; the two dispatch commands hand each lane the resolved path | 8 |
| G-18 `--only/--skip/--churn-days/--timeout` on receipts.py, no invoker passes them | flags and filter branch deleted; two constants replace 7 `args.*` reads | 5 |
| G-13 four tool wrappers each rewrite run → guard → `json.loads` | one `run_json` | 4 |
| G-01 two vocabularies for one lane reply (`concepts_removed/hold_reason/summary` vs `concepts/hold/title`) | findings.md speaks the ghost names; 13 renames across 4 agents + the command | 4 |
| G-10 pyproject `version` duplicates plugin.json; `.exorcist/` ignore for a dir nothing writes | `dynamic = ["version"]`; ignore line deleted | 2 |
| G-08 `register.py rank` subcommand nothing invokes | deleted; `rank()` stays — `merge` calls it and 3 tests pin it | 2 |
| G-09 `receipts.detect(root, …)` never reads `root` | parameter and 3 call-site arguments dropped | 1 |

Result: `Banished 7 (26 concepts) · Skipped 0`, 18 files, +89/−100. Every check the
run named was re-run independently afterwards: 4 test modules, ruff, vermin 3.9 floor,
manifest — all pass. The run noticed a README.md edit it had not made (mine, in
parallel) and left it alone, reporting the mtime.

Every ghost is a rule the ward states, broken by the tool's own author in its first
week: a flag nobody asked for, a helper pasted eight times, two names for one thing.

**Defects the run exposed in exorcist, fixed in the same PR.**

- Three ghosts were reported by two lanes each (G-08/G-19 the `rank` subcommand,
  G-02/G-10 pyproject, G-05/G-15 register.md:25) and the merge kept both. `merge` now
  collapses ghosts sharing a banish/migrate site at the same path and line — the one
  retiring more concepts survives, absorbs the other's evidence, records the second
  lane in `also`. Exact match only: a ±3-line fuzz was tried first and produced two
  false merges out of five (adjacent lines in one agent's Output section; 411 vs 412
  in receipts.py). Re-merging this run's lane files: 21 → 18.
- The report said "Worktree removed." and the worktree was still registered. The
  command now prints `git worktree list | wc -l` after the remove and reports the
  count — the claim carries its evidence or is not made.
