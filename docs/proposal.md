# Exorcist — aggressive simplification, prior art and proposal

The complaint: LLM-generated code is overly complex. GitClear measures it — devs are
~5x likelier to paste than refactor (moved/refactored lines 21%→3.8%, 2022→2026),
duplicated blocks +81%, error-masking constructs +47%. arXiv:2510.03029 finds LLM code
carries +63% more code smells than human reference, mostly implementation-level.

Three facets of the ask, and what exists for each:

1. **Minimum viable change** — is every hunk traceable to the request?
2. **Pattern reuse** — extend what the codebase has, don't introduce parallel patterns.
3. **Root-cause fix** — fix where data enters the system, not at each point of use.

## What already exists

### Ours

- **Claude Code built-in `/simplify`** (extracted from binary v2.1.251): 4 parallel
  cleanup agents — Reuse ("flag new code that re-implements something the codebase
  already has… name the existing helper to call instead"), Simplification (redundant/
  derivable state, copy-paste variation, deep nesting, dead code), Efficiency, Altitude
  ("special cases layered on shared infrastructure are a sign the fix isn't deep
  enough") — then dedup and apply fixes. Post-hoc, diff-scoped, intent-blind.
- **gauntlet `architecture-auditor`**: `simplicity` dimension (reuse / altitude /
  scaffold, must name the smaller version concretely), plus `pattern-fit` and
  `complexity` (premature generality). Findings only — judges never fix.
- **`~/.claude/CLAUDE.md`** already states the philosophy ("minimize structural drift,
  prefer reuse over creation… fix data at the boundary, not at the point of use") —
  but as prose, with nothing that computes or enforces it.

### Out there (reusable)

- **Anthropic `code-simplifier` agent** (pr-review-toolkit; brianlovin's 10.7k-install
  `simplify` skill is a near-verbatim copy — the de-facto community standard).
  Deliberately *conservative*: "Maintain Balance", "avoid prioritizing 'fewer lines'
  over readability".
- **Every's compound-engineering `ce-simplify-code`**: closest analog. Steal its
  guardrails ("net lines removed is not the success metric"; "never simplify away a
  safety check") and its code-reuse-reviewer persona: three-tier search (existing
  helpers → stdlib → framework guarantees), behavior-equivalence gating, name-the-
  replacement-symbol output contract.
- **Sentry `deslop`**: defines slop *relative to the surrounding file's norms* —
  "extra defensive checks or try/catch abnormal for that area of the codebase".
- **obra/superpowers `root-cause-tracing`**: "NEVER fix just where the error appears —
  trace backward through the call chain, fix at the source." Debugging-framed.
  Structural lesson: its rationalization tables (Excuse | Reality) pre-empting the
  model's own evasions outperform stated principles.
- **Karpathy guidelines skill**: best one-sentence MVC test — "every changed line
  should trace directly to the user's request."
- **Non-LLM checklist shapes**: Sonar cognitive complexity (hand-computable nesting
  increments — usable as a diff-delta check), Danger.js warn-not-block size predicates
  (>600 LOC → warn, `#trivial` escape hatch), Google Small CLs (~100 LOC reasonable,
  reviewers may reject on size alone), Ousterhout red flags (Shallow Module,
  Pass-Through Method, Information Leakage — the boundary-fix test), Muratori
  ("don't reuse until two instances"), Carmack ("single caller → inline"), Sandi Metz
  wrong-abstraction recovery (inline back into callers, then delete branches).
- **Caution from Aider**: minimality and laziness are opposite failure modes — a skill
  that only shouts "write less" induces elision. Target "complete but minimal."
- **The metric that survives both failure modes: concept count, not line count.**
  Consolidating three libraries that do the same job may be line-neutral — even
  line-positive — and still be the largest simplification available, because it removes
  a decision ("which one do I extend?") from every future change. Fewer competing
  patterns, layers, and vocabularies in play; LOC is a tripwire, never the goal.

## The gaps

Existing tooling clusters on post-hoc cosmetic cleanup, and the popular skills
explicitly refuse aggression. Three lanes are open:

- **(a) Minimum-viable-change is prose everywhere, computed nowhere.** No skill takes
  the *stated intent* as input and audits the diff against it. Both `/simplify` and
  gauntlet judge the diff in isolation.
- **(b) Reuse is enforced only at review time.** Nothing mandates search-before-write,
  or applies the two-instance / single-caller tests to new abstractions the diff
  introduces. GitClear says this is the highest-value lane.
- **(c) Boundary-fix is the biggest gap.** Only Altitude (4 sentences) and
  superpowers' debugging skill touch it. Nothing operationalizes "fix data at the
  boundary": find the transform/validation/null-check at a call site, ask where the
  value enters the system and how many other consumers read it unfixed, move the fix.

## Proposal

**Not gauntlet.** Two of gauntlet's own rules exclude this work:

- Judges never produce — an aggressive-simplify that *applies* changes is a producer
  tool, PRODUCT.md non-goal #1.
- Lane growth needs a realized failure, not a plausible category — and the
  `simplicity`/`pattern-fit`/`complexity` dimensions already cover the judgeable part.
  If minimality-vs-intent later earns a lane, it arrives as a dimension of
  architecture-auditor fed by PR-body context, not a new judge.

**A sibling plugin** in jacquardlabs-marketplace: **`exorcist`**. The framing: AI slop
arrived from outside, mimics the host, and multiplies — a possession, not a mess. Cast
out what doesn't belong; let the soul remain. ("Haunted forest" and "ghost code" are
already standing terms; the metaphor is half-established.) Names carry the flavor;
command descriptions stay literal.

Two mounts, mirroring gauntlet's changeset/posture split:

1. **`ward.md`** — the stance, imported via CLAUDE.md: ground slop can't take root in.
   Smallest change that satisfies the request; search before writing (name the file
   that shows the preferred shape); no new abstraction below two call sites; fix at
   the boundary; anti-elision clause; a rationalization table ("the demon will speak
   to you; do not negotiate"). Per Anthropic's own skill guidance, deltas from default
   behavior only. Gap (b) lives here — pre-write reuse enforcement is a standing
   constraint, not an invocation.
2. **`/exorcise [intent|PR]`** — changeset mount. The possession is recent; cast it
   out before it settles. Gather intent (argument, PR body, or ask); per hunk, a
   one-line trace to the intent or a flag; Danger-style numeric tripwires (LOC, new
   files, new exported symbols — warn, never block); deletion-first pass ("what does
   this change let us delete?"); then apply — revert unjustified hunks, skip-with-note.
   Safe to apply directly because scope is the diff. Defers cosmetic cleanup to
   built-in `/simplify` — no duplication.
3. **`/seance`** — codebase mount, phase 1. Read-only deep trace at a ref,
   posture-style fan-out, hunting standing hauntings with receipts (grep counts,
   caller traces): **pattern contention** (two-plus competing patterns for one job —
   count call sites of each, name the winner, size the migration), **dead code**
   (unreferenced exports, unreachable branches, flags nobody flips), **duplicated
   helpers** (parallel reimplementations that never met), **wrapper strata**
   (pass-throughs, single-caller indirection). Emits a ranked register — each ghost:
   evidence, blast radius, the one-line banishment. May ingest gauntlet posture
   findings as leads.
4. **`/exorcise <register>`** — codebase mount, phase 2. Works the séance register in
   batches. Find and apply are separated because whole-codebase deletion is exactly
   where autonomous apply gets dangerous; the register is the approval surface.

The boundary check ("salt the threshold" — for each transform/validation/default at a
point of use, trace the value's entry point, count unfixed consumers, move the fix;
Ousterhout's Information Leakage as the one-sentence test) folds into both mounts
rather than standing alone. Reactive and subtractive per johnsoncodehk — a real defect
authorizes it, YAGNI still governs.

No gauntlet charter conflict: `codebase-posture-auditor` judges and never fixes;
exorcist is a producer that hunts and acts.

## Static analysis to wrap (verified Aug 2026)

The séance's receipts (grep counts, caller traces) are exactly what deterministic
tools compute better — code owns bookkeeping, prompts own judgment. Séance phase 0
runs whatever applies from a zero-config core, feeds JSON to the model, and the model
judges only what no tool can:

**Five-tool core** (all active, JSON output, safe to run blind on an unfamiliar repo):

1. **ast-grep** — single static binary, ~25 tree-sitter grammars, YAML rules +
   `--json`. Highest-leverage: exorcist ships its own rules for wrapper shapes and
   contention patterns on it.
2. **knip** (JS/TS) + **ruff** (Python) — the ecosystem-native dead-code/dep
   workhorses, both hyper-active. Per-repo add-ons: `cargo-machete` (Rust),
   `x/tools deadcode` + `golangci-lint unused` (Go).
3. **jscpd v5** — duplication, 223 languages, Rust engine, `npx`, AI-oriented
   reporter. Owns the copy-paste half of duplication.
4. **scc v4** — instant triage: size, rough complexity, file-hotspot ranking. Runs
   first; tells the model where to look. `complexipy` (Python) / `gocognit` (Go) /
   `lizard` (multi-lang) when real cognitive-complexity numbers are needed.
5. **dependency-cruiser** (JS/TS, `--no-config`) / **tach** (Python, self-bootstraps
   config from the existing tree) — the only structure tools with a no-config mode.

**Vacant lanes — where the LLM earns its keep** (no deterministic incumbent, per
gauntlet's own "no lane where a deterministic tool is the incumbent" rule inverted):

- **Parallel reimplementations** — clone detectors catch copy-paste similarity only;
  independently written duplicate logic is model work (mizchi/similarity's AST
  matching narrows the gap slightly).
- **Two libraries doing the same job** — nothing detects pairwise functional overlap
  in a dep tree. Best assist: e18e's module-replacements manifest. Recipe: dump the
  dep tree, model matches.
- **Pass-through/wrapper strata** — no tool measures "this layer adds nothing";
  ast-grep pre-filters trivial-delegation shapes, model decides.
- **Churn/hotspot** — genuinely vacant OSS niche (code-maat frozen); ship the 10-line
  `git log --name-only | sort | uniq -c` script joined with scc output.

**Do not build on** (confirmed dead/archived/dormant 2025–26): ts-prune, unimported,
depcheck, madge, radon, rust-code-analysis, comby, code-maat. Semgrep note: engine is
LGPL but Semgrep-authored rules are now restricted — for shipping our own rules,
**opengrep** (the LGPL consortium fork, healthy) or ast-grep are the safe deps.
**Watch**: fallow (Rust, one-pass TS/JS dead-code+duplication+cycles+complexity,
agent-targeted) and skylos (Python, AI-slop-aware, claims ~3x fewer FPs than vulture).

**Authoring rules** (from the research): verifiable gates (grep for callers, diff
stats) over adjectives; rationalization tables over principles; one lens per skill;
keep the honest-metric guardrails while explicitly departing from "Maintain Balance"
where we mean to (we *do* inline single-use helpers; we never touch trust-boundary
checks). **Success metric everywhere is concepts removed, not lines removed** — a
séance banishment is scored by the patterns, layers, and duplicate vocabularies it
retires; a line-positive consolidation that leaves one way to do a thing beats a
line-negative edit that leaves two.

## Sources

Anthropic code-simplifier · compound-engineering-plugin · sentry deslop ·
obra/superpowers · karpathy-guidelines · GitClear 2025/2026 · arXiv:2510.03029 ·
METR 2025 RCT · Sonar cognitive complexity · danger.systems · Google Small CLs ·
Ousterhout · Muratori blog_0015 · Carmack on inlined code · Metz wrong-abstraction ·
grugbrain.dev · aider unified-diffs. Raw skill copies in session scratchpad.
