---
description: Audit the current changeset (or a PR) against its stated intent, then apply — revert hunks nothing in the intent reaches, inline single-caller abstractions, swap new code for existing helpers, move point-of-use fixes to the entry point, delete what the change made unnecessary. Pass the intent as text, a PR number or URL, or nothing to read it from the branch. Pass a séance register path to work a register instead.
allowed-tools: Bash, Read, Edit, Write, Glob, Grep, Task, AskUserQuestion
argument-hint: "[--base REF] [--json PATH] [intent | PR number or URL | path/to/register.json]"
---

# Exorcise

The possession is recent. You hold the change against what was asked, cast out what
does not belong, and leave the soul — the request, complete — intact. Scored in
concepts removed, not lines.

This is not `/simplify`. Reuse, nesting, redundant state, and efficiency cleanups are
that command's job; run it after this one. Your question is prior: does each piece of
this change belong here at all?

## 0. Mode

First take the flags off the front of `$ARGUMENTS`. Consume leading tokens only, and
stop at the first token that is neither flag, or at a literal `--`, which is itself
consumed; everything after is the argument, left intact — an intent may say "--json".

- `--base <ref>` or `--base=<ref>` — the diff base (§2). Default: `@{upstream}`, then
  `main`, then `HEAD~1`.
- `--json <path>` or `--json=<path>` — also write the report as JSON to `<path>`, per
  `${CLAUDE_PLUGIN_ROOT}/reference/report.md` (§7). The parent directory must exist.

A flag with no value, a flag given twice, or a `--json` path whose directory does not
exist is an error: say which and stop before any work.

Then, on what remains: if its first token is a path to an existing `.json` file, this
is a **register run** — skip to "Working a register" at the end. With `--base` or
`--json` set, print `--json/--base apply to changeset runs; a register run records
its outcome in the register itself` and stop before loading the register. Otherwise
it is a **changeset run**; the argument is the intent.

## 1. Gather the intent

The intent is the input everything traces to. Get it, in this order:

- The argument is a PR number or URL → `gh pr view <n> --json title,body,baseRefOid,headRefOid,headRefName`. Intent is the title and body. If `git rev-parse HEAD` is not `headRefOid`, say so and stop: applying against a different tree than the one described is how a fix lands in the wrong place.
- The argument is text → that is the intent.
- Empty → resolve `BASE` (§2) first, then read the branch: `git log --format='%s%n%b' BASE..HEAD`. Commit subjects are usually enough. If the log is empty or is one word ("wip", "fix"), ask the human for the intent in one sentence with AskUserQuestion, and stop until they answer. Never invent it.

Restate the intent as **numbered claims** — each one thing the change must do —
followed by the obligations the claims imply: tests where the project keeps them
(check for an existing test file beside the changed module), the failure path each
claim entails. This list is what every hunk answers to. Print it before anything else.

## 2. Gather the diff

Resolve the base. Pass `--base` when it was given and `--pr-base <baseRefOid>` for a
PR argument:

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/report.py" resolve-base [--base REF] [--pr-base SHA]
```

It prints `{"base_sha", "base_ref", "source"}`. The rule, in order: `--base` (a ref
that does not resolve is an error, never a fallback); the PR's base (a `--base` that
names a different commit is an error); `@{upstream}`; `main`; `HEAD~1`. `base_sha` is
the merge-base with HEAD. Exit 2 → print its message and stop.

`BASE` is `base_sha`; the apply step reads original hunk content from it. The diff is
`git diff BASE...HEAD`. If there are uncommitted changes, or that diff is empty, add
`git diff HEAD` — the pass usually runs before the commit.

Write the diff to `<tmp>/diff.patch` and run the tripwires:

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/tripwires.py" --text < <tmp>/diff.patch
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/tripwires.py" < <tmp>/diff.patch > <tmp>/tripwires.json
```

Print the text line. A crossed tripwire is a sentence of justification in the report,
never a block and never a finding by itself. If the diff is empty, say so and stop.

## 3. Fan out

Dispatch the four lanes **in parallel** via the Agent tool, one call each in a single
message: `exorcist:intent-tracer`, `exorcist:abstraction-hunter`,
`exorcist:threshold-salter`, `exorcist:deletion-scout`. Each gets the same context:

- the numbered claims and their obligations, verbatim, and the intent as gathered in
  §1 — the tracer's reverse roll call checks each claim against the diff, and a claim
  that quotes a design section against that section's words;
- the path to `<tmp>/diff.patch` and to `<tmp>/tripwires.json`;
- the repository root and `BASE`;
- the resolved absolute path of `${CLAUDE_PLUGIN_ROOT}/reference/findings.md` and
  the instruction that its entire reply is one JSON array per that contract, nothing
  else.

Write each reply verbatim to `<tmp>/findings/<lane>.json`, named by the findings lane
(`trace`, `abstraction`, `threshold`, `deletion`). Write the resolve-base object plus
`head_sha`, `includes_worktree`, and `hunks` to `<tmp>/scope.json`, then merge:

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/report.py" merge <tmp>/report.json <tmp>/findings/*.json \
  --tripwires <tmp>/tripwires.json --scope <tmp>/scope.json [--single-pass]
```

It strips exactly one code fence wrapped around each reply — that is transport, not
content — and validates every finding against the contract. A lane with any invalid
finding did not report: merge prints its errors; say which lane in the report, do not
repair or re-ask. It writes the draft report — lanes, deduped findings, and
`out_of_intent_files` — whether or not `--json` was given; §4 to §7 work from it.

Without the Agent tool: run the four lanes yourself in one pass, same contract, write
the four arrays the same way, pass `--single-pass`, and say in the report that it was
a single pass.

## 4. Decide

Merge has already deduped: findings that share `file` + `line`, the same `target`, or
the same unmet claim keep the highest-precedence action (`hold` > `revert` > `delete`
> `inline` > `reuse` > `move`), and the losing lane is in the survivor's `also`. The
draft's `applied` holds every finding to act on, `held` every hold.

Before touching anything, apply the ward's two guards to every finding in `applied`:

- **Never a trust-boundary check.** If a `revert`, `delete`, or `move` would remove
  the first validation an external value meets, authorization, or a data-loss guard,
  it becomes `hold`.
- **Minimal is not incomplete.** If a `revert` would remove a test or error path one of
  the claims implies, it becomes `hold`, `hold: "implied by intent"`, with that claim's
  number in `claim`.

A finding converted to `hold` moves to `held` with `target: null`, `concepts: []`,
`claim` (the claim it answers to, or null), and a `next` line.

A `move` whose entry point lies outside the files the diff touches stays `hold` with
the consumer count; a register run or the human works it.

## 5. Apply

Edit the working tree directly. No commits, no `git checkout --`, no `git reset`, no
history rewriting.

- `revert` — restore the hunk's region to its `BASE` content (`git show BASE:<path>`
  for reference) and remove any orphan the revert creates.
- `inline` — fold the symbol's body into its one caller; delete the definition and
  its now-unused imports.
- `reuse` — replace the new code with a call to `target`; delete what it replaced.
- `move` — add the fix at `target`, remove it at the point of use.
- `delete` — remove it.
- `hold` — touch nothing.

Skip a finding, with a note, when applying it would change behavior a test pins,
require edits well outside the diff, or when you judge it a false positive. Note the
skip; do not argue with it.

## 6. Verify

Run what the project runs — look at `Makefile`, `package.json` scripts, `pyproject.toml`,
CI config — scoped to the blast radius: the changed modules' tests and the typecheck
or lint over the changed files. Report each check by name with its outcome. A failure
you caused is fixed or the responsible edit is reverted; never weaken an assertion,
loosen a type, or skip a test to get green. No configured checks → say so.

## 7. Report

```text
# Exorcise — <branch or PR> <BASE-short>..<HEAD-short> · <n> hunks

Traced <n> · Reverted <n> · Rewritten <n> · Deleted <n> · Held <n>

## Reverted — no claim reaches them
- <file>:<lines>  <title> → <what was done>

## Rewritten
- <file>:<lines>  <title> → inlined into … / replaced by <target> / moved to <target>

## Deleted
- …

## Held
- <file>:<lines>  <title> — <hold>. <evidence> <what the human or register run would do>
- claim <n>  <title> — unmet claim: "<claim text>". <evidence> <what the human would do>

Concepts removed: <list> · Concepts kept: <new symbols that survived, each with its caller count>
Tripwires: <the text line> — <one sentence per crossed wire>
Checks: <name: outcome> …
Next: /simplify for cosmetic cleanup.
```

Sections with nothing in them are omitted. A change with no findings gets the header,
`Nothing to cast out — every hunk traced.`, the concepts line, and the tripwires line.
The Held line's closing clause is the finding's `next`; a hold that answers to a claim
also quotes it (`claim <n>: "<text>"`). An unmet claim has no `file:lines` and leads
with its claim number. Each Held line reads without the rest of the report — nothing
downstream re-raises a hold.

With `--json`, print the text report unchanged, then finish `<tmp>/report.json` per
`${CLAUDE_PLUGIN_ROOT}/reference/report.md`. Merge wrote `scope`, `lanes`,
`single_pass`, `tripwires`, and `out_of_intent_files`; never edit them. Fill `branch`,
`intent`, `claims` from §1, each `applied` entry's `status` and `outcome` from §5,
§4's guard conversions in `held`, `concepts_removed`, `concepts_kept` with their
caller counts, `checks` from §6, and one `justifications` entry per warning. Then:

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/report.py" validate <tmp>/report.json
```

Exit 0 → copy it to the `--json` path and print `JSON: <path>`. Exit 1 → print the
errors and `JSON: not written — the report failed validation`, and leave the path
untouched. Do not repair the draft to get it past the validator. An early stop — PR
head mismatch, no intent, empty diff, unresolved base — writes no JSON.

## Working a register

`$ARGUMENTS` named a séance register, optionally followed by ghost ids or the word
`all`: `/exorcist:exorcise docs/exorcist/seance-2026-08-29/register.json G-01,G-04`.

The register is the approval surface. Find and apply are separate mounts because
whole-codebase deletion is where autonomous apply becomes dangerous; here the human
has already read the evidence and said which ghosts go.

### 1. Load and select

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/register.py" validate <path>
```

Invalid → print the errors and stop. Then select, in this order:

- ids were given → those ghosts, whatever their status. Naming a ghost with `hold`
  set is the human's decision to override it; say so in the report.
- `all` → every ghost with status `proposed` or `approved` and **no** `hold`.
- nothing → every ghost with status `approved` and no `hold`.

None selected → print the counts by status, say how to approve (`"status":
"approved"` in the file, or pass ids), and stop.

### 2. Preconditions

- `git status --porcelain --untracked-files=no` is empty — no modified tracked files.
  A dirty tree means a failed batch cannot be cleanly undone; stop and say so. The
  register itself is usually untracked, which is fine.
- `git rev-parse HEAD` equals the register's `ref`. If not, say so and continue: the
  evidence is re-verified per ghost below, so drift is caught where it matters.

### 3. One ghost at a time, in rank order

For each selected ghost:

1. **Re-verify the evidence.** Re-run every `grep` in `evidence` and recount. Open
   every `site`. A count that changed, a site that moved, a survivor that no longer
   exists → `status: "skipped"`, `outcome: "evidence drifted: <what changed>"`. Move
   on; never guess at the new location.
2. **Snapshot.** Copy every file in `sites` (and any importer you expect to touch) to
   `<tmp>/snap-<id>/`. This is the undo for this ghost alone — it leaves earlier
   batches in other files intact.
3. **Banish.** Apply `banishment`: delete `banish` sites, rewrite `migrate` sites to
   the `survivor`, leave `keep` sites alone. Remove the orphans the deletion creates
   — imports, manifest lines, a test file whose subject is gone. Edit nothing outside
   the sites and their direct importers.
4. **Verify.** The project's checks scoped to the sites' modules and the tests that
   reference them; the typecheck or lint over the touched files. A failure → restore
   the snapshot, `status: "skipped"`, `outcome: "check failed: <name>: <first line>"`.
   Never weaken an assertion or a type to get green.
5. **Record.** `status: "banished"`, `outcome: "<what was done>; checks: <name: pass>…"`.
   Write the register back after every ghost, then re-render:

   ```bash
   python3 "${CLAUDE_PLUGIN_ROOT}/scripts/register.py" render <path> > <path minus .json>.md
   ```

   A run interrupted halfway leaves a register that says exactly how far it got.

### 4. Close

Run the project's full check suite once over the result. Then:

```text
# Exorcise — <register path> @ <ref-short>

Banished <n> (<m> concepts) · Skipped <k> · Untouched <j> (held or not selected)

## Banished
- G-01  <title> — <outcome>
## Skipped
- G-04  <title> — <outcome>

Concepts removed: <list>
Checks: <name: outcome> …
Diff: <git diff --stat, last line>
```

No commit. The human reviews `git diff` and commits in the batches they want; the
register records what each ghost did so the commit message can cite it.
