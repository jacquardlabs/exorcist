# Exorcise verification — specdeck, 2026-08-29

Subject: the control diff from the [ward verification](ward-specdeck-2026-08-29.md) —
an unwarded `claude -p` run's retry-with-backoff change, +140/−19, uncommitted in a
clone of specdeck @ 6a528f8. Invocation:

```text
claude --plugin-dir ~/Projects/exorcist -p '/exorcist:exorcise In src/specdeck/provider.py,
make `complete` retry on HTTP 429 and 5xx … up to 3 attempts. Keep the four-dependency
budget. Add tests.'
```

Result, verbatim header: `Traced 8 · Reverted 0 · Rewritten 2 · Deleted 0 · Held 1`.

| Finding | Lane | Action taken |
|---|---|---|
| `_retryable()`, 1 caller | abstraction | inlined into the loop; definition removed |
| `_patch_sequence()` parallel to `_patch()` | abstraction | folded into `_patch` (accepts one response or a list); 5 call sites moved |
| `tests/test_judge.py:385` asserts one POST on a 429 | trace | **held** — behavior change outside the diff's files; names it as a spec conflict for the human (CLAUDE.md: "do not improvise product decisions") |

Concepts removed: 2. Diff after: +133/−21 across the same 2 files. Checks it ran:
`ruff format --check` pass, `ruff check` 1 pre-existing RUF012 in the original diff,
`pytest tests/test_provider.py tests/test_judge.py` 72 passed / 1 failed — the held
case, failing identically before its edits.

The held finding is the notable one: the intent as given conflicts with a test the
repo already had, which neither headless run in the ward test noticed. Exorcise
surfaced it instead of patching the test to green.

Defect found and fixed in this run: `threshold-salter` returned prose around its
array and was counted as unreported. Agents now end with an explicit
"entire reply is the array, no fence, no prose" clause, and the command strips one
surrounding code fence as transport.
