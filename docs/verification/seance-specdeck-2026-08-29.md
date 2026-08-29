# Séance verification — specdeck, 2026-08-29

Subject: jacquardlabs/specdeck @ 6a528f82ae8b, 67 files / 20,718 lines of Python.
Invocation (headless, `--plugin-dir`, `CLAUDE_CODE_PRINT_BG_WAIT_CEILING_MS=0`):
`/exorcist:seance`. Wall clock ≈ 75 min; four opus lanes at high effort.

**Phase 0.** Ran: sizes, churn, hotspots, ruff, ast-grep, jscpd. Skipped with reason:
knip and depcruise (no JS/TS), scc (not on PATH). Receipts after the two fixes made
during this run: jscpd restricted to code formats (was 36.8% "duplication" from JSON
trace fixtures; now 14 clone pairs, 0.64%); the pass-through post-filter rejects
computed callees (`(a - b).total_seconds`, `''.join`) — 11 candidates, all plausible.

**Phase 1.** All four lanes reported. 21 ghosts, 55 concepts. Ranked table as
rendered (banishment column trimmed):

| # | id | lane | status | ghost | concepts | radius |
|---|---|---|---|---|---|---|
| 1 | G-11 | duplicate | proposed | The fake Anthropic response is hand-rolled seven times across four test modules | 7 | 5f/22c/22t |
| 2 | G-12 | duplicate | proposed | English pluralization is written thirteen times, including two byte-identical helpers 110 lines apart in report.py | 5 | 5f/19c/84t |
| 3 | G-01 | contention | proposed | console rendering has two homes: report.py and cli.py | 4 | 7f/2c/2t |
| 4 | G-13 | duplicate | proposed ⚠ behavior change | "Which tool this span ran" is re-derived from raw attributes at four sites past the boundary property that owns it | 4 | 4f/4c/24t · exported |
| 5 | G-14 | duplicate | proposed | "The budget may be absent" is known at four call sites instead of at the entry points | 4 | 4f/4c/40t |
| 6 | G-15 | duplicate | proposed | Four rule classes each restate the same vacuous `tested` default | 3 | 1f/3c/1t |
| 7 | G-02 | contention | proposed ⚠ behavior change | two ways to read a user-owned TOML file at the boundary | 3 | 5f/4c/2t · exported |
| 8 | G-20 | strata | proposed | two configuration knobs no invocation ever turns | 3 | 7f/0c/2t |
| 9 | G-09 | dead | proposed ⚠ spec conflict | cli.EXIT_CODES: a registry the source itself certifies nothing reads | 2 | 2f/0c/2t |
| 10 | G-10 | dead | proposed | RunMeasures.nothing: a production factory on a production model, called only from tests | 2 | 4f/2c/2t |
| 11 | G-03 | contention | proposed | closed vocabularies: StrEnum everywhere, Literal aliases in affected.py | 2 | 6f/3c/1t |
| 12 | G-08 | dead | proposed | Trace.final_response: a property no production code reads, whose docstring names a caller that does not exist | 2 | 4f/3c/3t |
| 13 | G-17 | duplicate | proposed | Finding the JSON object inside a model reply is implemented twice | 2 | 2f/2c/9t |
| 14 | G-04 | contention | proposed ⚠ behavior change | the test suite has two trace-fixture builders | 2 | 4f/14c/1t |
| 15 | G-16 | duplicate | proposed | The budget-charged provider call is written twice, so "an empty reply is billed too" lives in four places | 2 | 3f/2c/32t |
| 16 | G-18 | strata | proposed | the sync/async split is duplicated at two levels of one call path, and both sync halves only restate their parameters | 2 | 7f/57c/3t |
| 17 | G-19 | strata | proposed | _Invocation is an option bag built once and read by one helper, justified by helpers that do not exist | 2 | 3f/1c/0t |
| 18 | G-05 | contention | proposed | three vocabularies for printing an error line | 1 | 3f/2c/1t |
| 19 | G-06 | contention | proposed | the cassette directory is named twice: a constant and a literal | 1 | 3f/2c/1t |
| 20 | G-07 | contention | proposed | the console is threaded as a parameter, except once where it is constructed inline | 1 | 4f/2c/1t |
| 21 | G-21 | strata | proposed | rubric_hash is a one-line wrapper the lockfile does not use | 1 | 4f/1c/0t |

Spot checks against the tree: G-12's `_plural`/`_runs` are at report.py:258 and :369
with identical bodies; G-18's `run_cell` is `asyncio.run(run_cell_async(...))` with all
parameters forwarded; G-13's four raw `attributes.get(GenAI.TOOL_NAME)` reads exist
outside `Span.executed_tool`, and the lane found a latent `str(None)` bug at two of
them. G-02 and G-09 were held as `spec conflict` against DECISIONS.md rather than
proposed — the right call.

**Defects found and fixed.**

- Lanes wrote evidence `kind` values outside the schema (`read` ×33, `clone`,
  `receipt`, `surface`). `read` was a real gap — added to the vocabulary; the rest are
  now aliased at the merge boundary (`scripts/register.py: KIND_ALIASES`).
- Lane text arrived HTML-escaped through the Agent transport (`-&gt;`, `&lt;`); the
  merge unescapes it.
- Headless `-p` mode kills subagents after 600s by default; the first run died there.
  Documented in CONTRIBUTING.

**Observed, not fixed.** Two lanes stalled once each and were relaunched by the
command; a third stall on dead-code was resumed. That is harness behavior, but a lane
that never returns is the failure mode the merge already reports as "did not report".
