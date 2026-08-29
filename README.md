# exorcist

LLM-generated code arrives from outside, mimics the host, and multiplies. GitClear
measures it: refactored lines fell from 21% to 3.8% of changes between 2022 and 2026,
duplicated blocks rose 81%, error-masking constructs 47%. A possession, not a mess.
Exorcist casts out what does not belong and lets the soul remain.

It is scored in **concepts removed, not lines removed**. A consolidation that adds 30
lines and leaves one way to do a thing beats a deletion that removes 30 and leaves two.
Line count is a tripwire, never the goal.

```text
/exorcist:exorcise "add retry to the webhook sender"
```

```text
# Exorcise — feat/webhook-retry a1b2c3d..f6e5d4c · 14 hunks

Traced 9 · Reverted 3 · Held 2

## Reverted — no line of intent reaches them
- src/http/client.ts:44-71  new `RetryPolicy` class, 1 caller → inlined into sendWebhook
- src/utils/sleep.ts        new helper; `delay()` already in src/lib/time.ts:8 → deleted, import swapped
- src/webhook/sender.ts:12  try/catch around a call whose caller already catches → removed

## Held — traced, but the ward says no
- src/webhook/sender.ts:30  null-check on `payload.url` — value enters at api/webhooks.ts:22 unvalidated,
  4 other consumers read it raw. Salt the threshold: validate at the route, not here.
  Not applied: 4 consumers outside this diff.

Tripwires: +212 LOC (warn ≥200) · 2 new files · 1 new export
```

## Install

```text
/plugin marketplace add jacquardlabs/marketplace
/plugin install exorcist@jacquardlabs-marketplace
```

## Three mounts

| Mount | Command | Scope | Acts? |
|---|---|---|---|
| **Ward** | `/exorcist:ward` | every future change | no — a stance, imported via CLAUDE.md |
| **Exorcise** | `/exorcist:exorcise [intent \| PR]` | one changeset against its stated intent | yes — reverts and rewrites inside the diff |
| **Séance** | `/exorcist:seance [ref]` | the whole repository at a ref | no — emits a ranked register |
| **Exorcise a register** | `/exorcist:exorcise <register>` | the ghosts the séance found | yes — in batches, from the register you approved |

**Ward** is the ground slop cannot take root in. `/exorcist:ward` copies `ward.md` into
the project and adds one `@` import to CLAUDE.md. It states only deltas from default
behavior: the smallest change that satisfies the request; search before writing and
name the file that shows the preferred shape; no new abstraction below two call sites;
fix where the value enters the system, not where it is read; and a rationalization
table for the moments the model argues with itself. It also says what minimal is not —
elision is a failure mode, and "complete but minimal" is the target.

**Exorcise** takes the intent as input — an argument, a PR body, or it asks — and
audits the diff against it. Every hunk gets a one-line trace to the intent or a flag.
Numeric tripwires (LOC, new files, new exports) warn Danger-style and never block. A
deletion-first pass asks what the change lets us delete. Then it applies: reverts what
nothing in the intent reaches, rewrites what the ward forbids, and skips with a note
anything whose blast radius leaves the diff. Cosmetic cleanup — naming, nesting,
redundant state — is left to Claude Code's built-in `/simplify`, which already does it.

**Séance** reads a repository at a ref and never writes to it. Phase 0 shells out to a
zero-config tool core — ast-grep, knip or ruff, jscpd, scc, dependency-cruiser or tach
— for receipts: call-site counts, unreferenced exports, clone pairs, size and churn.
Phase 1 fans out over the lanes no deterministic tool owns: **pattern contention** (two
ways to do one job — count the call sites, name the winner, size the migration),
**dead code** the tools could not prove, **duplicated helpers** written independently
rather than pasted, and **wrapper strata** (pass-throughs, single-caller indirection).
Out comes a register: each ghost with its evidence, blast radius, the concepts it
retires, and a one-line banishment. The register is the approval surface — edit it,
delete what you want kept, and hand it back.

**Salting the threshold** runs inside both acting mounts. For every transform,
default, or validation at a point of use, trace the value to where it enters the
system, count the consumers that read it unfixed, and move the fix there. Ousterhout's
Information Leakage is the one-sentence test.

## What it will not do

- **Remove a trust-boundary check.** Input validation, authorization, data-loss
  guards, and accessibility affordances are never slop, whatever wrote them.
- **Confuse minimal with incomplete.** An elided error path or a missing test is not a
  smaller change; it is a wrong one.
- **Apply a whole-codebase deletion on its own.** Find and apply are separate mounts
  because that is exactly where autonomous apply becomes dangerous.
- **Duplicate `/simplify`.** Reuse, nesting, efficiency, and altitude cleanups already
  ship with Claude Code. Exorcist runs before that pass and answers a different
  question: does this belong here at all?

## Status

| Deliverable | State |
|---|---|
| Scaffold, manifest, README | landed |
| `ward.md` + `/exorcist:ward` | landed — [verified on specdeck](docs/verification/ward-specdeck-2026-08-29.md) |
| `/exorcist:exorcise` (changeset) | planned |
| `/exorcist:seance` + register schema | planned |
| `/exorcist:exorcise <register>` | planned |
| Marketplace registration | planned |

## Prior art

Built on Claude Code's built-in `/simplify` skeleton (fan-out, dedup, apply), Every's
`ce-simplify-code` guardrails, Sentry's `deslop` (slop is relative to the surrounding
file), obra/superpowers' rationalization tables and root-cause tracing, Karpathy's
"every changed line traces to the request", Danger.js warn-not-block predicates,
Ousterhout's red flags, Muratori's two-instance rule, and Carmack's single-caller
inlining. See `docs/` for the proposal and the static-analysis survey.

## License

MIT.
