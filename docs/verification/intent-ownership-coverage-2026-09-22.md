# Intent and simplicity ownership — coverage matrix, 2026-09-22

Question: once gauntlet#89 and studious#442 delete their changeset-simplicity and
diff-vs-intent checks, does exorcise cover what each one caught? Subject: the
inventory of those checks, one row each, held against exorcist at the #11 commit.
Issue #11's done-means asks for a before/after run on a real build; this matrix
stands in for it until that run is done (last section).

`covered` — an exorcist rule catches the same thing. `partial` — it catches a
narrower thing, named in the row. `keep` — not exorcist's; the deletion must not
take it.

## Diff vs intent

| Check (source) | Catches | Exorcist rule | Status |
|---|---|---|---|
| plan-drift out-of-plan-file (studious `scripts/plan-drift:97-103`) | a changed file no task path names | `out_of_intent_files`: files with a trace `revert` or `trust boundary` hold, pre-dedup, pre-apply — `scripts/report.py:369-375`, `reference/report.md:120-134` | partial — content-based, not name-based; see consumer decisions |
| plan-drift do-path-untouched (`scripts/plan-drift:105-111`) | a `Do:` path the commits never touched | reverse roll call, named path absent from `git diff --name-only` → `unmet claim` — `agents/intent-tracer.md:44-45`, `:79-82` | covered, when the `Do:` path is in the claims |
| plan-drift promised-method-missing (`scripts/plan-drift:113-121`) | a `Done means` method path that does not exist after the commits | reverse roll call, `test -e` / grep → `unmet claim` — `agents/intent-tracer.md:46-47` | partial — model-run, not zero-model; studious must pass the method paths inside the claims |
| Inspector contract-match lens (studious `skills/build/SKILL.md:417-419`) | a shipped contract that does not match its design section or `Do`/`Done means` | reverse roll call, contract that contradicts the claim or its quoted design section → `unmet claim` — `agents/intent-tracer.md:48-50`; `implied by intent` for what must stay — `:74-75` | partial — judged once per build after downstream tasks built on it, not per task before them |
| product-reviewer, unspecced scope built (gauntlet `agents/product-reviewer.md:85-87`) | something built that the spec never called for | forward roll call → `revert` — `agents/intent-tracer.md:27-35`, `:72-73` | covered, against the intent exorcise is handed, not the full design doc |
| product-reviewer, specced capability dropped (`agents/product-reviewer.md:85-87`) | a capability the spec called for that the changeset omits | reverse roll call, capability never reached → `unmet claim` — `agents/intent-tracer.md:51-52` | covered, against the intent exorcise is handed |
| held-finding context for the PR body (exorcist `reference/findings.md`) | `spec conflict`, `behavior change`, trust-boundary holds gauntlet stops re-raising | tracer emits `spec conflict` and `behavior change` — `agents/intent-tracer.md:57-66`; every hold carries `claim` and `next` — `:88-92`; `held[]` contract — `reference/report.md:111-119`; Held text line quotes the claim — `commands/exorcise.md:176-191` | covered |

## Simplicity

| Check (source) | Catches | Exorcist rule | Status |
|---|---|---|---|
| architecture-auditor Reuse (gauntlet `agents/architecture-auditor.md:66-68`) | reimplementation of something the codebase has | prior-shape search — `agents/abstraction-hunter.md:37-47`, extended to added blocks with no new symbol — `:49-51`; parallel helper — `:53-56`; dependency — `:70-71` | covered |
| architecture-auditor Altitude (`:68-70`) | a wrapper over a wrapper; logic every caller must repeat | pass-through `inline` — `agents/abstraction-hunter.md:28-30`; point-of-use fixes — `agents/threshold-salter.md:14-42`; logic added beside 2+ calls to one callee → `move` — `agents/abstraction-hunter.md:63-64` | covered |
| architecture-auditor Scaffold (`:70-73`) | a directory, class, flag, or interface standing in for one function | 0/1-caller `delete`/`inline` — `agents/abstraction-hunter.md:23-26`; one-implementation interface or one-function module at any caller count — `:32-35`; unused option — `:66-68` | covered |
| architecture-auditor premature generality (`:60-64`) | speculative abstraction, god-object growth, complexity in glue | overlap only: unused option and 0-caller `delete` — `agents/abstraction-hunter.md:23`, `:66-68` | keep — #89 keeps it at the architecture level |
| code-auditor duplicate logic across added files (`agents/code-auditor.md:89-92`) | the same logic duplicated within one changeset | two added blocks that do the same job → `reuse` — `agents/abstraction-hunter.md:58-61` | covered |
| code-auditor unused exports (`:90`) | exports the changeset adds that nothing imports | 0 callers → `delete` — `agents/abstraction-hunter.md:20-23` | covered |
| code-auditor dead code paths (`:90-91`) | branches that can no longer execute | superseded paths, always-on flags — `agents/deletion-scout.md:16-25`; a branch the diff adds that no caller can reach — `agents/abstraction-hunter.md:66-68` | covered |
| code-auditor god files, magic numbers (`:89-90`) | files past ~500 lines; unnamed literals | none | keep — not a concept removal |
| code-auditor complexity (`:86-88`) | function length, nesting, cyclomatic count, parameters | none — `commands/exorcise.md:13-15` cedes it to `/simplify` | keep — #89's overlap is maintainability `:89-92`, not this |
| code-auditor hygiene (`:106-107`, `:91-92`) | debug logging, commented-out code, unused variables, TODOs | partial overlap: file-norm slop — `agents/deletion-scout.md:28-42`; orphan cleanup — `agents/intent-tracer.md:20-21` | keep — not in #89's list |
| product-reviewer intake simplicity (`agents/product-reviewer.md:62-63`) | a proposal that could be half as much, at design intake | none — exorcise reads diffs, not documents | keep — #89 keeps intake mounts |

## Gaps named

- **Technicality gaming.** A claim met in letter only — a test that asserts nothing, a
  flag parsed and ignored — is outside what the reverse roll call's grep can show
  (`agents/intent-tracer.md:54-55`). studious#442 should keep the Inspector's
  technicality lens.
- **Blocking.** plan-drift exit 1 and an Inspector DEFECT block per task. Exorcise runs
  once per build and never blocks. Whether that is acceptable is studious#442's call.

## Consumer decisions

For studious#442, recorded here so the count is read the way it is built:

- `Read first:` paths. plan-drift counts them in plan; build Step 3 does not hand them
  to exorcise, so a file only `Read first:` names is a revert for the tracer and counts
  in `out_of_intent_files`. Either pass them in the intent or accept the stricter
  count.
- PLAN.md. plan-drift exempts it by name. Exorcise has no such rule; a PLAN.md edit
  counts unless a claim reaches it.
- Timing. The count is taken once, over the whole `--base..HEAD` range, before
  apply — not per task. `len(out_of_intent_files)` is the number rule 2 ranks on.
- Label. `exorcist:report` names the text report today; the JSON needs its own
  evidence label or replaces that one.

## Follow-up — the before/after run

Not run. One real studious build, the same PLAN.md, in each of the 3 repos (exorcist,
gauntlet, studious), twice: once before gauntlet#89 and studious#442 land, once after.
In each build's Step 3, invoke:

```text
/exorcist:exorcise --base <build base sha> --json <scratch>/exorcise-report.json "<Step 3 intent>"
```

Compare, per repo:

1. `len(out_of_intent_files)` against the distinct files plan-drift's `out-of-plan-file`
   flagged across the build's tasks, from the before run. A difference traces to a row above
   (`Read first:`, PLAN.md, or content-vs-name).
2. `held[]` entries with `hold: "unmet claim"` against plan-drift's
   `do-path-untouched` and `promised-method-missing` lines, and the Inspector's and
   product-reviewer's contract and delivery findings, from the before run. Each
   before-run finding has an after-run unmet claim, or is named here as a gap.
3. The after run's PR body against the before run's: every `spec conflict`,
   `behavior change`, and trust-boundary hold gauntlet raised before appears in the
   `## Held` section with its claim, evidence, and `next`.
4. gauntlet's architecture and code auditor findings from the before run against the
   after run's `applied[]`: each simplicity finding in a `covered` row above is an
   applied or held exorcise finding after.

Pass: no before-run finding in a `covered` row is missing from the after run.
