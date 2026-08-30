# Contributing

## Repo settings

Matched to gauntlet except the merge method: **merge commits only** (squash and rebase
both rewrite SHAs, so a stacked child PR would re-carry its parent's commits after the
parent lands; a true merge keeps them as ancestors). Delete branch on merge, PR required
at 0 approvals, branches up to date before merge, conversation resolution required, no
force-push or deletion of `main`, all CI checks required. Required contexts match the CI
job names exactly:

- `unit tests (Python 3.9)` … `unit tests (Python 3.14)`
- `plugin manifest`
- `ruff + version floor`

## Local checks

```bash
for t in tests/test_*.py; do python3 "$t"; done
python3 scripts/validate_plugin.py
uv run --no-project --with ruff==0.16.0 ruff check scripts tests
uv run --no-project --with vermin==1.8.0 vermin --no-tips -t=3.9- scripts/
```

## Conventions

- **Conventional Commits** for every commit subject — with merge commits, semantic-release
  reads the branch's commits, not the PR title; a merge commit's own message is ignored.
  A non-conforming subject produces no release, not an error.
- **3.9 floor for `scripts/`**, enforced by vermin: they run on whatever `python3` the
  host has. `tests/` may use anything the CI matrix covers.
- **Never edit the version in `.claude-plugin/plugin.json` by hand.** CI bumps it on
  merge to `main`, tags, publishes a release, and pings the marketplace to re-pin.
- **Names carry the flavor; descriptions stay literal.** A command's `description`
  frontmatter says what it does in plain words. The possession metaphor lives in names
  and section headings, never in a sentence a user must parse to act.
- **Deltas only.** Prompt files state where behavior departs from the model's default.
  A rule the model already follows is a sentence that costs attention and buys nothing.
- **Verifiable gates over adjectives.** A rule is a check someone can run — a grep for
  callers, a diff stat — not a quality the reader is asked to feel.

## Verifying a command headlessly

```bash
CLAUDE_CODE_PRINT_BG_WAIT_CEILING_MS=0 claude --plugin-dir . -p '/exorcist:seance' \
  --permission-mode acceptEdits --allowedTools "Bash(git *)" "Bash(python3 *)" Read Glob Grep Task Agent Write
```

`--plugin-dir` loads the checkout without installing it. The ceiling variable matters:
`-p` mode kills background subagents after 600s by default, and a séance's four lanes
over a 20k-line repository take longer than that.
