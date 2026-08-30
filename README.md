# exorcist

Aggressive simplification for LLM-generated code, as a Claude Code plugin.

Code an LLM writes arrives from outside, mimics the host, and multiplies. GitClear
measured it across 2022–2026: refactored lines fell from 21% to 3.8% of all changes,
duplicated blocks rose 81%, error-masking constructs 47%. The cleanup passes that exist
are cosmetic and deliberately cautious. Exorcist asks a prior question — *does this
belong here at all?* — and acts on the answer.

It is scored in **concepts removed, not lines**. A consolidation that adds 30 lines and
leaves one way to do a thing beats a deletion that removes 30 and leaves two. Line count
is a tripwire, never the goal.

## Sixty seconds

```text
/plugin marketplace add jacquardlabs/marketplace
/plugin install exorcist@jacquardlabs-marketplace

/exorcist:ward                                   # stance into CLAUDE.md — every future change
/exorcist:exorcise "add retry to the webhook"    # this changeset vs. that intent — edits your tree
/exorcist:seance                                 # whole repo at HEAD → a register, read-only
/exorcist:exorcise docs/exorcist/seance-2026-08-29/register.json G-01,G-04
```

Needs `git` and `python3` 3.9+. The séance fetches its analysis tools through `npx`
and `uvx` when they are not on PATH; pass `--no-fetch` to forbid that.

## Run on itself

Exorcist's first release was written by an LLM under supervision, in one session. The
séance was then pointed at that release — 1,451 lines of Python across 8 files, plus 12
command and agent prompts. Twelve minutes later, 21 ghosts, 52 concepts:

| # | Ghost | Lane | Concepts |
|---|---|---|---|
| 1 | eight agent prompts each carry the same `${CLAUDE_PLUGIN_ROOT}` fallback clause | duplicate | 8 |
| 2 | four `receipts.py` CLI flags no invoker passes, threaded through seven readers | strata | 5 |
| 3 | four tool wrappers each rewrite run-then-parse-JSON-stdout | duplicate | 4 |
| 4 | two vocabularies for one lane reply — `concepts_removed/hold_reason/summary` vs `concepts/hold/title` | contention | 4 |
| 11 | a `rank` subcommand nothing invokes; `merge` already ranks | dead | 2 |
| 21 | `receipts.detect` takes a `root` it never reads | dead | 1 |

Every one is a rule the ward states, broken by the tool's own author in its first
week: a flag nobody asked for, a helper pasted eight times, two names for one thing.
Seven were approved and worked: 26 concepts gone, 18 files, +89/−100, every check
green — [the record](docs/verification/self-seance-2026-08-29.md).

On a repository it had never seen — [specdeck](https://github.com/jacquardlabs/specdeck),
20,718 lines of Python — the same séance returned 21 ghosts and 55 concepts, among
them a helper written twice in one file 110 lines apart, a fake API response
hand-rolled seven times across four test modules, and a latent `str(None)` bug at two
of four sites that re-derived a fact the trace boundary already owned. Two ghosts were
worked; the diff was +4/−8 confined to their sites, and 1,084 tests passed.

## Three mounts

### Ward — the ground slop cannot take root in

`/exorcist:ward` copies [`ward.md`](ward.md) to `.claude/ward.md` and adds one `@`
import to CLAUDE.md (`user` installs to `~/.claude` instead). It is 87 lines and states
only departures from default behavior: the smallest change that satisfies the request;
search before writing, and cite the file that shows the prior shape; no new abstraction
below two call sites; fix where a value enters the system, not where it is read; a
rationalization table for the moments the model argues with itself. It also says what
minimal is not — an elided error path or a skipped test is a wrong change, not a
smaller one.

Same prompt, same repository, two clones — one warded:

| | Unwarded | Warded |
|---|---|---|
| New helper functions | 3, one with a single caller, one parallel to an existing helper | 1; the existing helper extended |
| Cites the prior shape it followed | no | `Following provider.py:28`, `Following tests/test_provider.py:33` |
| `ruff check` | 1 error | clean |

### Exorcise — the possession is recent

`/exorcist:exorcise [intent | PR]` takes the intent as input — a sentence, a PR body, or
the branch's commit log — restates it as numbered claims, and holds every hunk of the
diff against them. Four lanes run in parallel: does this hunk reach a claim; does this
new symbol have two callers and no prior shape; does this null-check belong at the
value's entry point; what does this change let us delete. Then it edits the working
tree: reverts what no claim reaches, inlines single-caller symbols, swaps new code for
the helper that already existed, moves point-of-use fixes to the threshold. It never
commits.

Run against an unwarded change on specdeck, with the intent that produced it:

```text
# Exorcise — main (uncommitted) 6a528f8..working tree · 8 hunks

Traced 8 · Reverted 0 · Rewritten 2 · Deleted 0 · Held 1

## Rewritten
- src/specdeck/provider.py:166-168  `_retryable`, one caller → inlined into the loop; definition removed
- tests/test_provider.py:44-54  `_patch_sequence`, parallel to `_patch` → folded into `_patch`; 5 call sites moved

## Held
- tests/test_judge.py:385-394  asserts one POST on a 429; the retry loop makes it three — behavior change.
  The test's own comment pins the opposite contract. Spec conflict for the human, not a patch.

Concepts removed: `_retryable`, `_patch_sequence`
Tripwires: +140/-19 lines across 2 file(s) · 0 new · 1 new export(s) · 0 new dep line(s)
Checks: ruff format: pass · pytest: 72 passed, 1 failed (the held case, failing identically before)
```

The held finding is the point. The intent conflicted with a test the repository already
had; neither the model that wrote the change nor the one that reviewed it had noticed.
Exorcise surfaced it instead of patching the test green.

### Séance — the possession is old

`/exorcist:seance [ref]` reads the whole repository at a ref, from a detached worktree,
and writes nothing to it. Phase 0 runs a zero-config tool core for receipts — size and
churn always; ast-grep pass-through rules, jscpd clones, knip (JS/TS) or ruff (Python),
dependency-cruiser cycles, scc when installed — and names every tool it could not run.
Phase 1 fans out over the lanes no deterministic tool owns: **pattern contention** (two
ways to do one job — count the call sites, name the survivor, size the migration),
**dead code** the tools could not prove, **duplicated helpers** written independently
rather than pasted, and **wrapper strata** (pass-throughs, single-caller indirection,
interfaces with one implementation).

Out comes `docs/exorcist/seance-<date>/register.json`, rendered as `register.md`: each
ghost with its evidence (a grep with its count, a receipt, a caller trace), the
concepts it retires, blast radius, and a one-line banishment, ranked by concepts
retired. Receipts are leads, never findings — a lane cites a tool line only after
opening the file. Schema in [`reference/register.md`](reference/register.md).

The register is the approval surface. Set `status` to `approved` on what should go,
delete what should stay, then `/exorcist:exorcise <register> [ids | all]` works it one
ghost at a time: re-run the evidence and recount (drift → skip, never guess), snapshot
the site files, apply the banishment, run the scoped checks, restore the snapshot on
failure, write the outcome back. A run interrupted halfway leaves a register that says
exactly how far it got.

## How it decides

- **Every changed line traces to a claim** in one sentence. A line that needs two is out.
- **Two call sites** is the earliest a helper may exist. One caller → inline.
- **Salt the threshold.** For a null check, default, coercion, or try/catch at a point
  of use: where does the value enter, how many consumers read it unfixed, move the fix
  there. Ousterhout's Information Leakage is the one-sentence test.
- **Slop is relative to the file it sits in.** A defensive check normal elsewhere is
  slop in a file whose other functions trust their callers.
- **Tripwires warn, never block** — 200 lines changed, a new file, a new exported
  symbol, a new dependency. Each costs a sentence of justification.
- **Hold vocabulary.** `trust boundary`, `public API`, `behavior change`, `spec
  conflict`, `implied by intent` — a finding that is real but not the tool's to apply.
  Reported, never acted on without a human.

## What it will not do

- **Remove a trust-boundary check.** Input validation, authorization, data-loss guards,
  accessibility affordances, a test that pins behavior — never slop, whatever wrote them.
- **Confuse minimal with incomplete.** Elision is the opposite failure mode, and the
  ward names it.
- **Apply a whole-codebase deletion on its own.** Find and apply are separate mounts
  because that is exactly where autonomous apply becomes dangerous.
- **Commit.** Exorcise edits the working tree; `git diff` is the review and `git
  checkout` is the undo.
- **Duplicate `/simplify`.** Reuse, nesting, efficiency, and altitude cleanups ship
  with Claude Code. Exorcist runs before that pass and answers a different question.

## Cost

| Mount | Lanes | Model | Measured |
|---|---|---|---|
| exorcise (changeset) | 4 | sonnet | ~3 min on a 2-file, +140-line diff |
| seance | 4 | opus | 12 min on 1,451 lines · ~75 min on 20,718 lines |
| exorcise (register) | — | inherits | ~2 min per ghost, dominated by the scoped checks |

The séance lanes read the whole tree regardless of size; on a trunk it is worth
running weekly, on a branch it is not.

## Prior art

Claude Code's built-in `/simplify` skeleton (fan-out, dedup, apply); Every's
`ce-simplify-code` guardrails; Sentry's `deslop` (slop is relative to the surrounding
file); obra/superpowers' rationalization tables and root-cause tracing; Karpathy's
"every changed line traces to the request"; Danger.js warn-not-block predicates;
Ousterhout's red flags; Muratori's two-instance rule; Carmack's single-caller inlining.
The proposal and static-analysis survey are in [`docs/proposal.md`](docs/proposal.md);
per-mount verification records in [`docs/verification/`](docs/verification/).

## License

MIT.
