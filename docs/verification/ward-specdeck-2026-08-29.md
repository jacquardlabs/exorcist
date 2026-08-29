# Ward verification — specdeck, 2026-08-29

Same prompt, same repo (jacquardlabs/specdeck @ 6a528f8), two clones, `claude -p`
(v2.1.251, `--permission-mode acceptEdits`). Warded clone had `ward.md` at
`.claude/ward.md` and `@.claude/ward.md` appended to CLAUDE.md. Prompt:

> In src/specdeck/provider.py, make `complete` retry on HTTP 429 and 5xx responses from
> Anthropic, with exponential backoff, up to 3 attempts. Keep the four-dependency
> budget. Add tests. Do not commit.

| | Control | Warded |
|---|---|---|
| Insertions / deletions | +140 / −19 | +103 / −21 |
| New symbols in `src/` | `MAX_ATTEMPTS`, `BACKOFF_BASE_S`, `_retryable()` (1 caller) | `MAX_ATTEMPTS`, `BACKOFF_S` |
| New symbols in `tests/` | `_patch_sequence()` beside existing `_patch()`, `_record_sleeps()`, `TestRetry` | `_no_sleep()`, `TestRetry`; existing `_patch()` extended |
| Module docstring | +5 lines of prose added | untouched |
| `pytest tests/test_provider.py` | 20 passed | 18 passed |
| `ruff check` | 1 error | clean |
| Summary cites prior shape | no | `Following provider.py:28`, `Following tests/test_provider.py:33` |
| Summary names the entry point | no | `Salted at provider.py:_anthropic` |

Concept count: control added 3 helper functions, warded added 1 and extended an
existing one. The warded summary said why the retryable check was inlined ("one
caller") — the rationalization-table row firing as written.

Noise observed in the warded summary: a line about the CLAUDE.md edit not being its
own (true, it was the harness's), and a "Salted at" line where the seam was already the
entry point. Neither cost a line of code.
