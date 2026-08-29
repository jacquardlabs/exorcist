---
description: Audit the current changeset (or a PR) against its stated intent, then apply — revert hunks nothing in the intent reaches, inline single-caller abstractions, swap new code for existing helpers, move point-of-use fixes to the entry point, delete what the change made unnecessary. Pass the intent as text, a PR number or URL, or nothing to read it from the branch. Pass a séance register path to work a register instead.
allowed-tools: Bash, Read, Edit, Write, Glob, Grep, Task, AskUserQuestion
argument-hint: "[intent | PR number or URL | path/to/register.json]"
---

# Exorcise

The possession is recent. You hold the change against what was asked, cast out what
does not belong, and leave the soul — the request, complete — intact. Scored in
concepts removed, not lines.

This is not `/simplify`. Reuse, nesting, redundant state, and efficiency cleanups are
that command's job; run it after this one. Your question is prior: does each piece of
this change belong here at all?

## 0. Mode

If `$ARGUMENTS` is a path to an existing `.json` file, this is a **register run** —
see "Working a register" at the end. Otherwise it is a **changeset run**.

## 1. Gather the intent

The intent is the input everything traces to. Get it, in this order:

- `$ARGUMENTS` is a PR number or URL → `gh pr view <n> --json title,body,baseRefOid,headRefOid,headRefName`. Intent is the title and body. If `git rev-parse HEAD` is not `headRefOid`, say so and stop: applying against a different tree than the one described is how a fix lands in the wrong place.
- `$ARGUMENTS` is text → that is the intent.
- Empty → read the branch: `git log --format='%s%n%b' <base>..HEAD`. Commit subjects are usually enough. If the log is empty or is one word ("wip", "fix"), ask the human for the intent in one sentence with AskUserQuestion, and stop until they answer. Never invent it.

Restate the intent as **numbered claims** — each one thing the change must do —
followed by the obligations the claims imply: tests where the project keeps them
(check for an existing test file beside the changed module), the failure path each
claim entails. This list is what every hunk answers to. Print it before anything else.

## 2. Gather the diff

Same scope rule as `/simplify`: `git diff @{upstream}...HEAD`, or `git diff
main...HEAD` / `git diff HEAD~1` without an upstream. If there are uncommitted changes,
or the range diff is empty, add `git diff HEAD` — the pass usually runs before the
commit. A PR argument uses `git diff <baseRefOid>...<headRefOid>`. Record `BASE`; the
apply step reads original hunk content from it.

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

- the numbered claims, verbatim;
- the path to `<tmp>/diff.patch` and to `<tmp>/tripwires.json`;
- the repository root and `BASE`;
- the instruction that its entire reply is one JSON array per
  `reference/findings.md`, nothing else.

Write each reply verbatim to `<tmp>/findings/<lane>.json`. Strip exactly one code
fence wrapped around the whole reply — that is transport, not content. A reply that
still does not parse as a JSON array is a lane that did not report — say which in the
report, do not repair or re-ask.

Without the Agent tool: run the four lanes yourself in one pass, same contract, and say
in the report that it was a single pass.

## 4. Decide

Merge the arrays. Dedup findings that share `file` + `line` or the same `target`,
keeping the highest-precedence action: `hold` > `revert` > `delete` > `inline` >
`reuse` > `move`.

Then, before touching anything, apply the ward's two guards to every finding:

- **Never a trust-boundary check.** If a `revert`, `delete`, or `move` would remove
  the first validation an external value meets, authorization, or a data-loss guard,
  it becomes `hold`.
- **Minimal is not incomplete.** If a `revert` would remove a test or error path one of
  the claims implies, it becomes `hold`, `hold_reason: "implied by intent"`.

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
- <file>:<lines>  <summary> → <what was done>

## Rewritten
- <file>:<lines>  <summary> → inlined into … / replaced by <target> / moved to <target>

## Deleted
- …

## Held
- <file>:<lines>  <summary> — <hold_reason>. <what the human or register run would do>

Concepts removed: <list> · Concepts kept: <new symbols that survived, each with its caller count>
Tripwires: <the text line> — <one sentence per crossed wire>
Checks: <name: outcome> …
Next: /simplify for cosmetic cleanup.
```

Sections with nothing in them are omitted. A change with no findings gets the header,
`Nothing to cast out — every hunk traced.`, the concepts line, and the tripwires line.

## Working a register

`$ARGUMENTS` named a séance register. Not yet implemented — say so, point at
`/exorcist:seance`, and stop.
